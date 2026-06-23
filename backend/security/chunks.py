"""
Chunk-level position attestation for CEG-KEM.

Breaks a continuous position stream into fixed-duration time-chunks,
generates an HMAC attestation per chunk, and validates that a quorum
of recent chunks all attest valid-position before allowing decryption.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class PositionChunk:
    """
    An immutable, time-bounded window of position samples.

    Each chunk covers ``[start_time, end_time)`` and holds the raw
    coordinate samples plus an HMAC attestation signed with a
    server-side secret.
    """

    chunk_id: str
    start_time: float
    end_time: float
    positions: Tuple[Tuple[float, float], ...]
    timestamps: Tuple[float, ...]
    attestation_hmac: str
    is_valid_position: bool
    nonce: str


class ChunkAttestor:
    """
    Splits a position stream into time-chunks and generates per-chunk
    HMAC attestations.

    The HMAC binds the chunk contents to a server-side secret and a
    one-time nonce, making replay of captured chunks from a different
    session infeasible.
    """

    def __init__(
        self,
        chunk_duration_seconds: float = 2.0,
        server_secret: Optional[bytes] = None,
    ) -> None:
        self._chunk_duration = chunk_duration_seconds
        self._secret = server_secret or os.urandom(32)

    def create_chunks(
        self,
        positions: List[Tuple[float, float]],
        timestamps: List[float],
        position_valid_flags: List[bool],
    ) -> List[PositionChunk]:
        """
        Partition position samples into time-chunks and attest each one.

        ``position_valid_flags`` is a per-sample boolean indicating
        whether that sample was inside the spatial boundary.  A chunk
        is considered valid only if ALL samples within it are valid.
        """
        if not positions or not timestamps:
            return []

        chunks: List[PositionChunk] = []
        t_start = timestamps[0]

        current_positions: List[Tuple[float, float]] = []
        current_timestamps: List[float] = []
        current_flags: List[bool] = []

        for pos, ts, flag in zip(positions, timestamps, position_valid_flags):
            if ts >= t_start + self._chunk_duration and current_positions:
                chunk = self._finalize_chunk(
                    t_start,
                    t_start + self._chunk_duration,
                    current_positions,
                    current_timestamps,
                    current_flags,
                )
                chunks.append(chunk)

                t_start = ts
                current_positions = []
                current_timestamps = []
                current_flags = []

            current_positions.append(pos)
            current_timestamps.append(ts)
            current_flags.append(flag)

        # Finalize the trailing partial chunk
        if current_positions:
            chunk = self._finalize_chunk(
                t_start,
                current_timestamps[-1],
                current_positions,
                current_timestamps,
                current_flags,
            )
            chunks.append(chunk)

        return chunks

    def verify_chunk(self, chunk: PositionChunk) -> bool:
        """Verify that a chunk's HMAC attestation is authentic."""
        expected = self._compute_hmac(
            chunk.chunk_id,
            chunk.nonce,
            chunk.positions,
            chunk.timestamps,
            chunk.is_valid_position,
        )
        return hmac.compare_digest(expected, chunk.attestation_hmac)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _finalize_chunk(
        self,
        start: float,
        end: float,
        positions: List[Tuple[float, float]],
        timestamps: List[float],
        flags: List[bool],
    ) -> PositionChunk:
        nonce = os.urandom(16).hex()
        chunk_id = hashlib.sha256(
            f"{start}:{end}:{nonce}".encode()
        ).hexdigest()[:16]

        is_valid = all(flags)
        pos_tuple = tuple(tuple(p) for p in positions)
        ts_tuple = tuple(timestamps)

        attestation = self._compute_hmac(
            chunk_id, nonce, pos_tuple, ts_tuple, is_valid
        )

        return PositionChunk(
            chunk_id=chunk_id,
            start_time=start,
            end_time=end,
            positions=pos_tuple,
            timestamps=ts_tuple,
            attestation_hmac=attestation,
            is_valid_position=is_valid,
            nonce=nonce,
        )

    def _compute_hmac(
        self,
        chunk_id: str,
        nonce: str,
        positions: Tuple[Tuple[float, float], ...],
        timestamps: Tuple[float, ...],
        is_valid: bool,
    ) -> str:
        """HMAC-SHA256 binding chunk contents to server secret + nonce."""
        payload = json.dumps(
            {
                "chunk_id": chunk_id,
                "nonce": nonce,
                "positions": list(positions),
                "timestamps": list(timestamps),
                "is_valid": is_valid,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()


class QuorumValidator:
    """
    Validates that at least K of the last N chunks attest valid position.

    This defeats single-point-in-time spoofing: the attacker must maintain
    a plausible position stream across the entire quorum window, not just
    forge one "yes" sample.
    """

    def __init__(
        self,
        required_k: int = 3,
        window_n: int = 5,
        max_chunk_age_seconds: float = 30.0,
    ) -> None:
        if required_k > window_n:
            raise ValueError(
                f"required_k ({required_k}) must be <= window_n ({window_n})"
            )
        self._required_k = required_k
        self._window_n = window_n
        self._max_age = max_chunk_age_seconds

    def validate(
        self,
        chunks: List[PositionChunk],
        attestor: ChunkAttestor,
        current_time: Optional[float] = None,
    ) -> Tuple[bool, Dict[str, object]]:
        """
        Check quorum across the most recent N chunks.

        Returns (passed, details) where details includes counts and
        which chunks failed for SIEM logging.
        """
        now = current_time if current_time is not None else time.time()

        # Take the N most recent chunks
        recent = sorted(chunks, key=lambda c: c.end_time, reverse=True)[
            : self._window_n
        ]

        valid_count = 0
        expired_count = 0
        tampered_count = 0
        invalid_position_count = 0
        failed_chunk_ids: List[str] = []

        for chunk in recent:
            age = now - chunk.end_time
            if age > self._max_age:
                expired_count += 1
                failed_chunk_ids.append(chunk.chunk_id)
                continue

            if not attestor.verify_chunk(chunk):
                tampered_count += 1
                failed_chunk_ids.append(chunk.chunk_id)
                continue

            if not chunk.is_valid_position:
                invalid_position_count += 1
                failed_chunk_ids.append(chunk.chunk_id)
                continue

            valid_count += 1

        passed = valid_count >= self._required_k

        details = {
            "passed": passed,
            "valid_count": valid_count,
            "required_k": self._required_k,
            "window_n": self._window_n,
            "expired": expired_count,
            "tampered": tampered_count,
            "invalid_position": invalid_position_count,
            "failed_chunk_ids": failed_chunk_ids,
            "evaluated_chunks": len(recent),
        }

        return (passed, details)
