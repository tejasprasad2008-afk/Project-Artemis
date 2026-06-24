"""
Tests for the Shannon entropy scorer and anomaly detector.

Covers all four anomaly classifications (replay, static, noise, scripted)
plus genuine human-like input validation.
"""

import math
import random
import time

import pytest

from backend.security.entropy import (
    AnomalyType,
    EntropyAnomalyDetector,
    EntropyResult,
    EntropyThresholds,
    ShannonEntropyScorer,
    VelocityAnalyzer,
)


# ---------------------------------------------------------------------------
# Helpers — generate characteristic position streams
# ---------------------------------------------------------------------------

def _genuine_stream(n: int = 30, base_x: float = 5.0, base_y: float = 5.0):
    """
    Simulate human-like drag movement with natural jitter.

    Produces varied deltas with micro-tremor noise — the entropy should
    land in the genuine acceptance band.
    """
    random.seed(42)
    positions = [(base_x, base_y)]
    t0 = time.time()
    timestamps = [t0]

    for i in range(1, n):
        dx = random.uniform(-1.5, 1.5) + 0.3 * math.sin(i * 0.5)
        dy = random.uniform(-1.5, 1.5) + 0.3 * math.cos(i * 0.7)
        prev = positions[-1]
        positions.append((prev[0] + dx, prev[1] + dy))
        timestamps.append(t0 + i * 0.1)

    return positions, timestamps


def _static_stream(n: int = 20, x: float = 5.0, y: float = 5.0):
    """All samples at the same coordinate — entropy ≈ 0."""
    t0 = time.time()
    positions = [(x, y)] * n
    timestamps = [t0 + i * 0.1 for i in range(n)]
    return positions, timestamps


def _noise_stream(n: int = 30):
    """Uniformly random coordinates — entropy should be very high."""
    random.seed(99)
    t0 = time.time()
    positions = [(random.uniform(-500, 500), random.uniform(-500, 500)) for _ in range(n)]
    timestamps = [t0 + i * 0.1 for i in range(n)]
    return positions, timestamps


def _scripted_stream(n: int = 30, step: float = 1.0):
    """
    Perfectly uniform linear movement — zero jitter.

    Every delta is exactly (step, step) → very low jitter score.
    """
    t0 = time.time()
    positions = [(i * step, i * step) for i in range(n)]
    timestamps = [t0 + i * 0.1 for i in range(n)]
    return positions, timestamps


def _teleport_stream():
    """Two points impossibly far apart in a tiny time window."""
    t0 = time.time()
    positions = [
        (0.0, 0.0),
        (0.1, 0.1),
        (0.2, 0.15),
        (0.25, 0.3),
        (0.3, 0.35),
        (0.35, 0.4),
        (999.0, 999.0),  # teleportation
        (999.1, 999.1),
    ]
    timestamps = [t0 + i * 0.1 for i in range(len(positions))]
    return positions, timestamps


# ---------------------------------------------------------------------------
# ShannonEntropyScorer tests
# ---------------------------------------------------------------------------

class TestShannonEntropyScorer:
    def test_static_positions_have_zero_entropy(self):
        scorer = ShannonEntropyScorer()
        positions, _ = _static_stream()
        score = scorer.score(positions)
        assert score == 0.0, f"Static stream should have zero entropy, got {score}"

    def test_genuine_positions_have_moderate_entropy(self):
        scorer = ShannonEntropyScorer()
        positions, _ = _genuine_stream()
        score = scorer.score(positions)
        assert 1.0 < score < 5.0, f"Genuine stream entropy {score} outside expected range"

    def test_noise_positions_have_high_entropy(self):
        scorer = ShannonEntropyScorer()
        positions, _ = _noise_stream()
        score = scorer.score(positions)
        assert score > 3.0, f"Noise stream should have high entropy, got {score}"

    def test_single_position_returns_zero(self):
        scorer = ShannonEntropyScorer()
        assert scorer.score([(1.0, 1.0)]) == 0.0

    def test_fingerprint_deterministic(self):
        scorer = ShannonEntropyScorer()
        positions, _ = _genuine_stream()
        fp1 = scorer.fingerprint(positions)
        fp2 = scorer.fingerprint(positions)
        assert fp1 == fp2, "Same input must produce the same fingerprint"

    def test_fingerprint_differs_for_different_streams(self):
        scorer = ShannonEntropyScorer()
        pos_a, _ = _genuine_stream(n=20)
        pos_b, _ = _noise_stream(n=20)
        assert scorer.fingerprint(pos_a) != scorer.fingerprint(pos_b)


# ---------------------------------------------------------------------------
# VelocityAnalyzer tests
# ---------------------------------------------------------------------------

class TestVelocityAnalyzer:
    def test_static_velocity_is_zero(self):
        analyzer = VelocityAnalyzer()
        positions, timestamps = _static_stream()
        max_v, mean_v, jitter = analyzer.analyze(positions, timestamps)
        assert max_v == 0.0
        assert mean_v == 0.0
        assert jitter == 0.0

    def test_scripted_has_near_zero_jitter(self):
        analyzer = VelocityAnalyzer()
        positions, timestamps = _scripted_stream()
        _, _, jitter = analyzer.analyze(positions, timestamps)
        assert jitter < 0.01, f"Scripted path jitter should be near zero, got {jitter}"

    def test_genuine_has_measurable_jitter(self):
        analyzer = VelocityAnalyzer()
        positions, timestamps = _genuine_stream()
        _, _, jitter = analyzer.analyze(positions, timestamps)
        assert jitter > 0.1, f"Genuine movement should have measurable jitter, got {jitter}"

    def test_teleport_detected_by_max_velocity(self):
        analyzer = VelocityAnalyzer()
        positions, timestamps = _teleport_stream()
        max_v, _, _ = analyzer.analyze(positions, timestamps)
        assert max_v > 1000, f"Teleportation should produce extreme velocity, got {max_v}"


# ---------------------------------------------------------------------------
# EntropyAnomalyDetector integration tests
# ---------------------------------------------------------------------------

class TestEntropyAnomalyDetector:
    def test_genuine_classified_correctly(self):
        detector = EntropyAnomalyDetector()
        positions, timestamps = _genuine_stream()
        result = detector.analyze(positions, timestamps)
        assert result.anomaly == AnomalyType.GENUINE

    def test_static_classified_as_static(self):
        detector = EntropyAnomalyDetector()
        positions, timestamps = _static_stream()
        result = detector.analyze(positions, timestamps)
        assert result.anomaly == AnomalyType.STATIC

    def test_noise_classified_as_noise(self):
        detector = EntropyAnomalyDetector()
        positions, timestamps = _noise_stream()
        result = detector.analyze(positions, timestamps)
        assert result.anomaly == AnomalyType.NOISE

    def test_scripted_classified_as_scripted(self):
        detector = EntropyAnomalyDetector()
        positions, timestamps = _scripted_stream()
        result = detector.analyze(positions, timestamps)
        # Scripted paths fail on either low jitter or low entropy
        assert result.anomaly in (AnomalyType.SCRIPTED, AnomalyType.STATIC)

    def test_replay_detected_on_second_submission(self):
        detector = EntropyAnomalyDetector()
        positions, timestamps = _genuine_stream()

        # First submission should pass
        result1 = detector.analyze(positions, timestamps)
        assert result1.anomaly == AnomalyType.GENUINE

        # Exact same stream submitted again — replay
        result2 = detector.analyze(positions, timestamps)
        assert result2.anomaly == AnomalyType.REPLAY

    def test_teleportation_classified_as_anomalous(self):
        detector = EntropyAnomalyDetector()
        positions, timestamps = _teleport_stream()
        result = detector.analyze(positions, timestamps)
        # Teleportation triggers SCRIPTED (velocity gate) or STATIC (entropy
        # gate fires first when sample count is low).  Either is correct —
        # the key invariant is that it is NOT classified as GENUINE.
        assert result.anomaly != AnomalyType.GENUINE

    def test_result_contains_all_fields(self):
        detector = EntropyAnomalyDetector()
        positions, timestamps = _genuine_stream()
        result = detector.analyze(positions, timestamps)
        assert isinstance(result.score, float)
        assert isinstance(result.fingerprint, str)
        assert isinstance(result.velocity_max, float)
        assert isinstance(result.jitter_score, float)
        assert result.sample_count == len(positions)
