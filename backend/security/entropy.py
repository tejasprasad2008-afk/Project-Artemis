"""
Position-stream entropy analysis for CEG-KEM anti-spoofing.

Computes Shannon entropy and velocity metrics over sliding windows of
coordinate data, then classifies the stream as genuine or one of four
anomaly types: REPLAY, STATIC, NOISE, or SCRIPTED.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class AnomalyType(str, Enum):
    """Classification of position-stream anomalies."""

    GENUINE = "genuine"
    REPLAY = "replay"
    STATIC = "static_injection"
    NOISE = "random_noise"
    SCRIPTED = "scripted_path"


@dataclass(frozen=True)
class EntropyResult:
    """Immutable result of an entropy analysis pass."""

    score: float
    anomaly: AnomalyType
    velocity_max: float
    velocity_mean: float
    jitter_score: float
    fingerprint: str
    sample_count: int


# ---------------------------------------------------------------------------
# Configurable thresholds — kept server-side, never sent to the client.
# ---------------------------------------------------------------------------

@dataclass
class EntropyThresholds:
    """
    Tunable boundaries for anomaly classification.

    These MUST remain server-side.  Exposing them to the client allows an
    attacker to craft coordinates that sit just inside the acceptance band.
    """

    entropy_min: float = 1.8
    entropy_max: float = 4.5
    velocity_max: float = 120.0  # grid-units per second
    jitter_floor: float = 0.15
    replay_fingerprint_similarity: float = 0.95
    window_size: int = 24


# ---------------------------------------------------------------------------
# Core scorers
# ---------------------------------------------------------------------------

class ShannonEntropyScorer:
    """
    Computes Shannon entropy over quantised coordinate deltas.

    Genuine human input produces entropy roughly in [2.0, 4.0].
    Replay / static / noise / scripted inputs fall outside that band or
    exhibit characteristic micro-structure that the anomaly detector catches.
    """

    def __init__(self, bin_resolution: float = 1.0) -> None:
        self._bin_resolution = bin_resolution

    def score(self, positions: List[Tuple[float, float]]) -> float:
        """Return Shannon entropy of the quantised delta stream."""
        if len(positions) < 2:
            return 0.0

        deltas = []
        for i in range(1, len(positions)):
            dx = round(
                (positions[i][0] - positions[i - 1][0]) / self._bin_resolution
            )
            dy = round(
                (positions[i][1] - positions[i - 1][1]) / self._bin_resolution
            )
            deltas.append((dx, dy))

        counts = Counter(deltas)
        total = len(deltas)
        entropy = 0.0
        for count in counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy

    def fingerprint(self, positions: List[Tuple[float, float]]) -> str:
        """
        Produce a deterministic hash of the quantised delta stream.

        Two position sequences that are exact replays will produce the
        same fingerprint regardless of absolute offset or timestamp.
        """
        if len(positions) < 2:
            return hashlib.sha256(b"empty").hexdigest()

        delta_bytes = []
        for i in range(1, len(positions)):
            dx = round(
                (positions[i][0] - positions[i - 1][0]) / self._bin_resolution
            )
            dy = round(
                (positions[i][1] - positions[i - 1][1]) / self._bin_resolution
            )
            delta_bytes.append(f"{dx},{dy}".encode())

        return hashlib.sha256(b"|".join(delta_bytes)).hexdigest()


class VelocityAnalyzer:
    """Computes per-step velocity and flags impossible jumps."""

    def analyze(
        self,
        positions: List[Tuple[float, float]],
        timestamps: List[float],
    ) -> Tuple[float, float, float]:
        """
        Returns (max_velocity, mean_velocity, jitter_score).

        Jitter is the standard deviation of velocities — genuine human
        movement has measurable jitter from hand tremor; scripted paths
        have near-zero jitter.
        """
        if len(positions) < 2 or len(timestamps) < 2:
            return (0.0, 0.0, 0.0)

        velocities: List[float] = []
        for i in range(1, len(positions)):
            dt = timestamps[i] - timestamps[i - 1]
            if dt <= 0:
                # Zero or negative time gap is itself suspicious but we
                # handle it gracefully to avoid division by zero.
                dt = 0.001

            dx = positions[i][0] - positions[i - 1][0]
            dy = positions[i][1] - positions[i - 1][1]
            distance = math.sqrt(dx * dx + dy * dy)
            velocities.append(distance / dt)

        max_v = max(velocities)
        mean_v = sum(velocities) / len(velocities)

        # Jitter = standard deviation of velocity
        if len(velocities) < 2:
            jitter = 0.0
        else:
            variance = sum((v - mean_v) ** 2 for v in velocities) / len(velocities)
            jitter = math.sqrt(variance)

        return (max_v, mean_v, jitter)


class EntropyAnomalyDetector:
    """
    Classifies a position stream against known anomaly signatures.

    Decision tree:
      1. Fingerprint matches recent history   → REPLAY
      2. Entropy below floor                  → STATIC
      3. Entropy above ceiling                → NOISE
      4. Jitter below floor                   → SCRIPTED
      5. Velocity exceeds max                 → SCRIPTED (teleportation)
      6. All checks pass                      → GENUINE
    """

    def __init__(
        self,
        thresholds: Optional[EntropyThresholds] = None,
    ) -> None:
        self._thresholds = thresholds or EntropyThresholds()
        self._scorer = ShannonEntropyScorer()
        self._velocity = VelocityAnalyzer()
        self._recent_fingerprints: List[str] = []
        self._max_fingerprint_history = 200

    def analyze(
        self,
        positions: List[Tuple[float, float]],
        timestamps: List[float],
    ) -> EntropyResult:
        """Run full anomaly classification on a position stream."""
        t = self._thresholds

        entropy = self._scorer.score(positions)
        fingerprint = self._scorer.fingerprint(positions)
        max_v, mean_v, jitter = self._velocity.analyze(positions, timestamps)

        anomaly = AnomalyType.GENUINE

        # 1. Replay detection — fingerprint already seen
        if fingerprint in self._recent_fingerprints:
            anomaly = AnomalyType.REPLAY
        # 2. Static injection — entropy too low
        elif entropy < t.entropy_min:
            anomaly = AnomalyType.STATIC
        # 3. Random noise — entropy too high
        elif entropy > t.entropy_max:
            anomaly = AnomalyType.NOISE
        # 4. Scripted path — no natural jitter
        elif jitter < t.jitter_floor:
            anomaly = AnomalyType.SCRIPTED
        # 5. Teleportation — impossible velocity
        elif max_v > t.velocity_max:
            anomaly = AnomalyType.SCRIPTED

        # Record fingerprint for future replay detection
        self._recent_fingerprints.append(fingerprint)
        if len(self._recent_fingerprints) > self._max_fingerprint_history:
            self._recent_fingerprints = self._recent_fingerprints[
                -self._max_fingerprint_history :
            ]

        return EntropyResult(
            score=entropy,
            anomaly=anomaly,
            velocity_max=max_v,
            velocity_mean=mean_v,
            jitter_score=jitter,
            fingerprint=fingerprint,
            sample_count=len(positions),
        )
