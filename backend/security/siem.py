"""
Structured security-event logging for CEG-KEM (SIEM / IDS layer).

Emits JSON-structured events for every security-relevant action in the
Artemis pipeline — entropy anomalies, cascade failures, replay detections,
privilege denials, and successful decryptions.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    """Security event classification."""

    ENTROPY_ANOMALY = "entropy_anomaly"
    VELOCITY_VIOLATION = "velocity_violation"
    REPLAY_DETECTED = "replay_detected"
    CASCADE_FAILURE = "cascade_failure"
    CASCADE_SUCCESS = "cascade_success"
    CHUNK_TAMPER = "chunk_tamper"
    CHUNK_EXPIRED = "chunk_expired"
    QUORUM_FAILURE = "quorum_failure"
    QUORUM_SUCCESS = "quorum_success"
    PRIVILEGE_DENIED = "privilege_denied"
    DECRYPT_SUCCESS = "decrypt_success"
    DECRYPT_DENIED = "decrypt_denied"
    SESSION_EXPIRED = "session_expired"
    POSITION_VERIFIED = "position_verified"
    POSITION_REJECTED = "position_rejected"


class Severity(str, Enum):
    """Event severity aligned with standard SIEM severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Map event types to default severities
_DEFAULT_SEVERITY: Dict[EventType, Severity] = {
    EventType.ENTROPY_ANOMALY: Severity.HIGH,
    EventType.VELOCITY_VIOLATION: Severity.MEDIUM,
    EventType.REPLAY_DETECTED: Severity.CRITICAL,
    EventType.CASCADE_FAILURE: Severity.HIGH,
    EventType.CASCADE_SUCCESS: Severity.INFO,
    EventType.CHUNK_TAMPER: Severity.CRITICAL,
    EventType.CHUNK_EXPIRED: Severity.LOW,
    EventType.QUORUM_FAILURE: Severity.HIGH,
    EventType.QUORUM_SUCCESS: Severity.INFO,
    EventType.PRIVILEGE_DENIED: Severity.HIGH,
    EventType.DECRYPT_SUCCESS: Severity.INFO,
    EventType.DECRYPT_DENIED: Severity.MEDIUM,
    EventType.SESSION_EXPIRED: Severity.LOW,
    EventType.POSITION_VERIFIED: Severity.INFO,
    EventType.POSITION_REJECTED: Severity.MEDIUM,
}


@dataclass(frozen=True)
class SecurityEvent:
    """Immutable security event record."""

    event_id: str
    event_type: EventType
    severity: Severity
    timestamp: float
    message: str
    details: Dict[str, Any]
    source_ip: Optional[str] = None
    session_id: Optional[str] = None
    user_role: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a flat dictionary for JSON output."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "message": self.message,
            "details": self.details,
            "source_ip": self.source_ip,
            "session_id": self.session_id,
            "user_role": self.user_role,
        }


class SIEMLogger:
    """
    Structured JSON security-event logger.

    Events are written to a dedicated ``security`` Python logger at the
    appropriate log level and also accumulated in memory for batch
    retrieval (useful for the real-time threat dashboard).
    """

    def __init__(self, logger_name: str = "artemis.security") -> None:
        self._logger = logging.getLogger(logger_name)
        self._events: List[SecurityEvent] = []
        self._max_buffer = 5000

    def emit(
        self,
        event_type: EventType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: Optional[Severity] = None,
        source_ip: Optional[str] = None,
        session_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> SecurityEvent:
        """Create, log, and buffer a security event."""
        resolved_severity = severity or _DEFAULT_SEVERITY.get(
            event_type, Severity.MEDIUM
        )

        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=resolved_severity,
            timestamp=time.time(),
            message=message,
            details=details or {},
            source_ip=source_ip,
            session_id=session_id,
            user_role=user_role,
        )

        log_line = json.dumps(event.to_dict(), separators=(",", ":"))
        log_level = self._severity_to_log_level(resolved_severity)
        self._logger.log(log_level, log_line)

        self._events.append(event)
        if len(self._events) > self._max_buffer:
            self._events = self._events[-self._max_buffer :]

        return event

    def get_recent_events(
        self,
        count: int = 50,
        severity_filter: Optional[Severity] = None,
        event_type_filter: Optional[EventType] = None,
    ) -> List[SecurityEvent]:
        """Retrieve recent events, optionally filtered."""
        filtered = self._events
        if severity_filter is not None:
            filtered = [e for e in filtered if e.severity == severity_filter]
        if event_type_filter is not None:
            filtered = [e for e in filtered if e.event_type == event_type_filter]
        return filtered[-count:]

    def get_threat_summary(self) -> Dict[str, Any]:
        """Return a summary of recent threat indicators."""
        severity_counts: Dict[str, int] = {}
        type_counts: Dict[str, int] = {}
        for event in self._events:
            sev = event.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            evt = event.event_type.value
            type_counts[evt] = type_counts.get(evt, 0) + 1

        return {
            "total_events": len(self._events),
            "by_severity": severity_counts,
            "by_type": type_counts,
            "critical_count": severity_counts.get("critical", 0),
            "high_count": severity_counts.get("high", 0),
        }

    @staticmethod
    def _severity_to_log_level(severity: Severity) -> int:
        """Map SIEM severity to Python log level."""
        mapping = {
            Severity.INFO: logging.INFO,
            Severity.LOW: logging.INFO,
            Severity.MEDIUM: logging.WARNING,
            Severity.HIGH: logging.ERROR,
            Severity.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(severity, logging.WARNING)
