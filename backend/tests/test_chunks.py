"""
Tests for the chunk attestation and quorum validation system.

Covers HMAC integrity, chunk creation, tamper detection, quorum
thresholds, and expired-chunk rejection.
"""

import time
from typing import List, Tuple

import pytest

from backend.security.chunks import ChunkAttestor, PositionChunk, QuorumValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_stream(
    n: int = 30,
    dt: float = 0.1,
    in_bounds: bool = True,
) -> Tuple[List[Tuple[float, float]], List[float], List[bool]]:
    """Generate a simple position stream with timestamps and validity flags."""
    t0 = time.time()
    positions = [(float(i), float(i)) for i in range(n)]
    timestamps = [t0 + i * dt for i in range(n)]
    flags = [in_bounds] * n
    return positions, timestamps, flags


# ---------------------------------------------------------------------------
# ChunkAttestor tests
# ---------------------------------------------------------------------------

class TestChunkAttestor:
    def test_creates_chunks_from_stream(self):
        attestor = ChunkAttestor(chunk_duration_seconds=1.0)
        positions, timestamps, flags = _sample_stream(n=30, dt=0.1)

        chunks = attestor.create_chunks(positions, timestamps, flags)
        assert len(chunks) >= 2, "30 samples at 0.1s/sample with 1s chunks should produce multiple chunks"

    def test_chunk_has_valid_attestation(self):
        attestor = ChunkAttestor(chunk_duration_seconds=1.0)
        positions, timestamps, flags = _sample_stream(n=20, dt=0.1)

        chunks = attestor.create_chunks(positions, timestamps, flags)
        for chunk in chunks:
            assert attestor.verify_chunk(chunk), f"Chunk {chunk.chunk_id} HMAC should verify"

    def test_tampered_chunk_fails_verification(self):
        attestor = ChunkAttestor(chunk_duration_seconds=1.0)
        positions, timestamps, flags = _sample_stream(n=20, dt=0.1)

        chunks = attestor.create_chunks(positions, timestamps, flags)
        original = chunks[0]

        # Tamper: flip the validity flag
        tampered = PositionChunk(
            chunk_id=original.chunk_id,
            start_time=original.start_time,
            end_time=original.end_time,
            positions=original.positions,
            timestamps=original.timestamps,
            attestation_hmac=original.attestation_hmac,  # original HMAC
            is_valid_position=not original.is_valid_position,  # flipped
            nonce=original.nonce,
        )

        assert not attestor.verify_chunk(tampered), "Tampered chunk must fail HMAC verification"

    def test_different_secret_fails_verification(self):
        attestor_a = ChunkAttestor(server_secret=b"secret-a")
        attestor_b = ChunkAttestor(server_secret=b"secret-b")

        positions, timestamps, flags = _sample_stream(n=20, dt=0.1)
        chunks = attestor_a.create_chunks(positions, timestamps, flags)

        # Verify with the wrong attestor (different server secret)
        for chunk in chunks:
            assert not attestor_b.verify_chunk(chunk), "Chunk from attestor A must fail with attestor B's secret"

    def test_empty_stream_produces_no_chunks(self):
        attestor = ChunkAttestor()
        chunks = attestor.create_chunks([], [], [])
        assert chunks == []

    def test_all_out_of_bounds_chunks_marked_invalid(self):
        attestor = ChunkAttestor(chunk_duration_seconds=1.0)
        positions, timestamps, flags = _sample_stream(n=20, dt=0.1, in_bounds=False)

        chunks = attestor.create_chunks(positions, timestamps, flags)
        for chunk in chunks:
            assert not chunk.is_valid_position, "Out-of-bounds stream should produce invalid chunks"

    def test_mixed_bounds_chunk_marked_invalid(self):
        """A chunk is valid only if ALL samples are in-bounds."""
        attestor = ChunkAttestor(chunk_duration_seconds=2.0)
        t0 = time.time()

        # 10 samples in 2s window — first 9 in-bounds, last 1 out
        positions = [(float(i), float(i)) for i in range(10)]
        timestamps = [t0 + i * 0.2 for i in range(10)]
        flags = [True] * 9 + [False]

        chunks = attestor.create_chunks(positions, timestamps, flags)
        assert len(chunks) >= 1
        # The chunk containing the out-of-bounds sample should be invalid
        has_invalid = any(not c.is_valid_position for c in chunks)
        assert has_invalid, "Mixed-bounds chunk must be marked invalid"


# ---------------------------------------------------------------------------
# QuorumValidator tests
# ---------------------------------------------------------------------------

class TestQuorumValidator:
    def test_all_valid_chunks_pass_quorum(self):
        attestor = ChunkAttestor(chunk_duration_seconds=0.5)
        validator = QuorumValidator(required_k=3, window_n=5, max_chunk_age_seconds=60.0)

        positions, timestamps, flags = _sample_stream(n=30, dt=0.1, in_bounds=True)
        chunks = attestor.create_chunks(positions, timestamps, flags)

        passed, details = validator.validate(chunks, attestor)
        assert passed, f"All-valid chunks should pass quorum: {details}"

    def test_all_invalid_chunks_fail_quorum(self):
        attestor = ChunkAttestor(chunk_duration_seconds=0.5)
        validator = QuorumValidator(required_k=3, window_n=5, max_chunk_age_seconds=60.0)

        positions, timestamps, flags = _sample_stream(n=30, dt=0.1, in_bounds=False)
        chunks = attestor.create_chunks(positions, timestamps, flags)

        passed, details = validator.validate(chunks, attestor)
        assert not passed, f"All-invalid chunks should fail quorum: {details}"

    def test_expired_chunks_fail_quorum(self):
        attestor = ChunkAttestor(chunk_duration_seconds=0.5)
        validator = QuorumValidator(
            required_k=3,
            window_n=5,
            max_chunk_age_seconds=1.0,  # Very short expiry
        )

        # Create chunks with timestamps far in the past
        t_past = time.time() - 100.0
        positions = [(float(i), float(i)) for i in range(30)]
        timestamps = [t_past + i * 0.1 for i in range(30)]
        flags = [True] * 30

        chunks = attestor.create_chunks(positions, timestamps, flags)
        passed, details = validator.validate(chunks, attestor, current_time=time.time())
        assert not passed, f"Expired chunks should fail quorum: {details}"
        assert details["expired"] > 0

    def test_quorum_threshold_enforcement(self):
        """Require 3 valid out of 5, provide exactly 2 valid → fail."""
        attestor = ChunkAttestor(chunk_duration_seconds=0.5)
        validator = QuorumValidator(required_k=3, window_n=5, max_chunk_age_seconds=60.0)

        positions, timestamps, flags = _sample_stream(n=30, dt=0.1, in_bounds=True)
        chunks = attestor.create_chunks(positions, timestamps, flags)

        # Tamper enough chunks to drop below quorum
        tampered_chunks = []
        for i, chunk in enumerate(chunks):
            if i < len(chunks) - 2:
                # Flip validity + regenerate as new object (HMAC will fail → counted as tampered)
                tampered = PositionChunk(
                    chunk_id=chunk.chunk_id,
                    start_time=chunk.start_time,
                    end_time=chunk.end_time,
                    positions=chunk.positions,
                    timestamps=chunk.timestamps,
                    attestation_hmac="0000000000000000000000000000000000000000000000000000000000000000",
                    is_valid_position=chunk.is_valid_position,
                    nonce=chunk.nonce,
                )
                tampered_chunks.append(tampered)
            else:
                tampered_chunks.append(chunk)

        passed, details = validator.validate(tampered_chunks, attestor)
        assert not passed, f"Below-quorum tampered chunks should fail: {details}"

    def test_k_greater_than_n_raises(self):
        with pytest.raises(ValueError, match="required_k"):
            QuorumValidator(required_k=6, window_n=5)
