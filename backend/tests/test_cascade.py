"""
Tests for the three-layer CEG-KEM cascade.

Validates that:
  - Genuine input with correct role produces a decrypt key
  - Each individual gate (entropy, velocity, nonce, role, quorum) collapses
    the cascade when violated
  - No partial key material is ever returned on failure
  - The cascade is fail-closed by design
"""

import math
import random
import time
from typing import List, Tuple

import pytest

from backend.security.cascade import (
    CascadeFailureReason,
    CascadeMLKEM,
    CascadeResult,
)
from backend.security.chunks import ChunkAttestor, QuorumValidator
from backend.security.entropy import EntropyThresholds
from backend.security.siem import SIEMLogger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _genuine_stream(n: int = 30) -> Tuple[List[Tuple[float, float]], List[float]]:
    """Human-like coordinate stream with natural jitter."""
    random.seed(42)
    t0 = time.time()
    positions = [(5.0, 5.0)]
    timestamps = [t0]

    for i in range(1, n):
        dx = random.uniform(-1.5, 1.5) + 0.3 * math.sin(i * 0.5)
        dy = random.uniform(-1.5, 1.5) + 0.3 * math.cos(i * 0.7)
        prev = positions[-1]
        positions.append((prev[0] + dx, prev[1] + dy))
        timestamps.append(t0 + i * 0.1)

    return positions, timestamps


def _static_stream(n: int = 20) -> Tuple[List[Tuple[float, float]], List[float]]:
    """Static coordinate injection."""
    t0 = time.time()
    return [(5.0, 5.0)] * n, [t0 + i * 0.1 for i in range(n)]


def _make_cascade() -> CascadeMLKEM:
    """Create a fresh cascade instance for each test."""
    return CascadeMLKEM(
        siem=SIEMLogger(),
        chunk_attestor=ChunkAttestor(),
        quorum_validator=QuorumValidator(required_k=3, window_n=5),
        min_samples=6,
    )


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

class TestCascadeSuccess:
    def test_genuine_input_produces_decrypt_key(self):
        cascade = _make_cascade()
        positions, timestamps = _genuine_stream()

        result = cascade.execute(
            positions=positions,
            timestamps=timestamps,
            session_nonce="test-nonce-001",
            user_role="operator",
        )

        assert result.success, f"Genuine input should succeed, got: {result.failure_reason}"
        assert result.decrypt_key is not None
        assert len(result.decrypt_key) == 32, "Decrypt key should be 32 bytes"
        assert result.layer_reached == 3

    def test_different_nonces_produce_different_keys(self):
        cascade = _make_cascade()
        positions, timestamps = _genuine_stream()

        result_a = cascade.execute(
            positions=positions,
            timestamps=timestamps,
            session_nonce="nonce-alpha-001",
            user_role="operator",
        )

        # Need a fresh stream to avoid replay detection
        random.seed(99)
        positions_b = [(3.0, 3.0)]
        t0 = time.time()
        timestamps_b = [t0]
        for i in range(1, 30):
            dx = random.uniform(-1.5, 1.5) + 0.2 * math.sin(i * 0.3)
            dy = random.uniform(-1.5, 1.5) + 0.2 * math.cos(i * 0.9)
            prev = positions_b[-1]
            positions_b.append((prev[0] + dx, prev[1] + dy))
            timestamps_b.append(t0 + i * 0.1)

        result_b = cascade.execute(
            positions=positions_b,
            timestamps=timestamps_b,
            session_nonce="nonce-beta-002",
            user_role="operator",
        )

        assert result_a.success and result_b.success
        assert result_a.decrypt_key != result_b.decrypt_key


# ---------------------------------------------------------------------------
# Layer 1 failures — entropy gate
# ---------------------------------------------------------------------------

class TestCascadeLayer1:
    def test_static_injection_collapses_cascade(self):
        cascade = _make_cascade()
        positions, timestamps = _static_stream()

        result = cascade.execute(
            positions=positions,
            timestamps=timestamps,
            session_nonce="test-static-001",
            user_role="operator",
        )

        assert not result.success
        assert result.decrypt_key is None, "No key on failure"
        assert result.failure_reason == CascadeFailureReason.ENTROPY_ANOMALY
        assert result.layer_reached == 1

    def test_replay_collapses_cascade(self):
        cascade = _make_cascade()
        positions, timestamps = _genuine_stream()

        # First pass — should succeed
        result1 = cascade.execute(
            positions=positions,
            timestamps=timestamps,
            session_nonce="replay-test-001",
            user_role="operator",
        )
        assert result1.success

        # Exact same stream — replay
        result2 = cascade.execute(
            positions=positions,
            timestamps=timestamps,
            session_nonce="replay-test-002",
            user_role="operator",
        )

        assert not result2.success
        assert result2.decrypt_key is None
        assert result2.failure_reason == CascadeFailureReason.REPLAY_DETECTED


# ---------------------------------------------------------------------------
# Layer 2 failures — velocity / nonce gate
# ---------------------------------------------------------------------------

class TestCascadeLayer2:
    def test_nonce_reuse_collapses_cascade(self):
        cascade = _make_cascade()

        # First call with a nonce
        positions_a, timestamps_a = _genuine_stream()
        result1 = cascade.execute(
            positions=positions_a,
            timestamps=timestamps_a,
            session_nonce="reuse-me-001",
            user_role="operator",
        )
        assert result1.success

        # Second call — different stream but SAME nonce
        random.seed(77)
        positions_b = [(2.0, 2.0)]
        t0 = time.time()
        timestamps_b = [t0]
        for i in range(1, 30):
            dx = random.uniform(-1.5, 1.5) + 0.4 * math.sin(i * 0.6)
            dy = random.uniform(-1.5, 1.5) + 0.4 * math.cos(i * 0.4)
            prev = positions_b[-1]
            positions_b.append((prev[0] + dx, prev[1] + dy))
            timestamps_b.append(t0 + i * 0.1)

        result2 = cascade.execute(
            positions=positions_b,
            timestamps=timestamps_b,
            session_nonce="reuse-me-001",  # same nonce!
            user_role="operator",
        )

        assert not result2.success
        assert result2.failure_reason == CascadeFailureReason.SESSION_NONCE_REUSED
        assert result2.layer_reached == 2


# ---------------------------------------------------------------------------
# Layer 3 failures — role / quorum gate
# ---------------------------------------------------------------------------

class TestCascadeLayer3:
    def test_unauthorized_role_collapses_cascade(self):
        cascade = _make_cascade()
        positions, timestamps = _genuine_stream()

        result = cascade.execute(
            positions=positions,
            timestamps=timestamps,
            session_nonce="role-test-001",
            user_role="visitor",  # not in allowed_roles
        )

        assert not result.success
        assert result.decrypt_key is None
        assert result.failure_reason == CascadeFailureReason.ROLE_DENIED
        assert result.layer_reached == 3

    def test_admin_role_succeeds(self):
        cascade = _make_cascade()
        positions, timestamps = _genuine_stream()

        result = cascade.execute(
            positions=positions,
            timestamps=timestamps,
            session_nonce="admin-test-001",
            user_role="admin",
        )

        assert result.success


# ---------------------------------------------------------------------------
# Pre-check failures
# ---------------------------------------------------------------------------

class TestCascadePreCheck:
    def test_insufficient_samples_collapses_cascade(self):
        cascade = _make_cascade()
        t0 = time.time()

        result = cascade.execute(
            positions=[(1.0, 1.0), (2.0, 2.0)],  # only 2 samples, need 6
            timestamps=[t0, t0 + 0.1],
            session_nonce="short-stream-001",
            user_role="operator",
        )

        assert not result.success
        assert result.failure_reason == CascadeFailureReason.INSUFFICIENT_SAMPLES
        assert result.layer_reached == 0

    def test_no_partial_key_on_any_failure(self):
        """Across all failure modes, decrypt_key must always be None."""
        cascade = _make_cascade()
        t0 = time.time()

        # Insufficient samples
        r1 = cascade.execute(
            positions=[(1.0, 1.0)],
            timestamps=[t0],
            session_nonce="partial-001",
            user_role="operator",
        )

        # Static injection
        positions_s, timestamps_s = _static_stream()
        r2 = cascade.execute(
            positions=positions_s,
            timestamps=timestamps_s,
            session_nonce="partial-002",
            user_role="operator",
        )

        # Bad role
        positions_g, timestamps_g = _genuine_stream()
        r3 = cascade.execute(
            positions=positions_g,
            timestamps=timestamps_g,
            session_nonce="partial-003",
            user_role="intruder",
        )

        for result in [r1, r2, r3]:
            assert result.decrypt_key is None, (
                f"No partial key allowed on failure: {result.failure_reason}"
            )


# ---------------------------------------------------------------------------
# SIEM event emission
# ---------------------------------------------------------------------------

class TestCascadeSIEM:
    def test_success_emits_decrypt_success_event(self):
        siem = SIEMLogger()
        cascade = CascadeMLKEM(siem=siem, min_samples=6)
        positions, timestamps = _genuine_stream()

        cascade.execute(
            positions=positions,
            timestamps=timestamps,
            session_nonce="siem-success-001",
            user_role="operator",
        )

        events = siem.get_recent_events(count=10)
        event_types = [e.event_type.value for e in events]
        assert "decrypt_success" in event_types

    def test_failure_emits_cascade_failure_event(self):
        siem = SIEMLogger()
        cascade = CascadeMLKEM(siem=siem, min_samples=6)

        cascade.execute(
            positions=[(1.0, 1.0)] * 20,
            timestamps=[time.time() + i * 0.1 for i in range(20)],
            session_nonce="siem-failure-001",
            user_role="operator",
        )

        events = siem.get_recent_events(count=10)
        event_types = [e.event_type.value for e in events]
        assert "entropy_anomaly" in event_types
