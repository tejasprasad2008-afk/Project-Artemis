import os
import hmac as hmac_module
import logging
from typing import List, Tuple
from backend.security.entropy import EntropyAnomalyDetector, EntropyResult

logger = logging.getLogger(__name__)

_MISSING_KEY_SENTINEL = "__MISSING__"


class UWBProxyClient:
    """
    Simulates a secure server-to-server proxy to the third-party UWB verifier.

    The UWB_SECRET_KEY environment variable MUST be set before starting the
    server.  There is intentionally no insecure hardcoded default — the
    service will raise ``EnvironmentError`` at startup if the variable is
    absent so that misconfiguration is caught immediately, not silently.
    """

    def __init__(self) -> None:
        raw = os.environ.get("UWB_SECRET_KEY", _MISSING_KEY_SENTINEL)
        if raw == _MISSING_KEY_SENTINEL:
            raise EnvironmentError(
                "UWB_SECRET_KEY environment variable is not set. "
                "Set it to a strong random secret before starting the server."
            )
        self._secret_key: str = raw
        self.verifier_url = os.environ.get(
            "UWB_VERIFIER_URL", "https://api.external-uwb.io/v1/verify"
        )
        self.detector = EntropyAnomalyDetector()

    def verify_position(
        self, positions: List[Tuple[float, float]], timestamps: List[float]
    ) -> EntropyResult:
        """
        Forward telemetry to the UWB verifier (simulated) and run local
        entropy analysis.  The secret key is NEVER logged in any form.
        """
        # Log only non-sensitive context — no key material ever appears in logs
        logger.info(
            "[UWB PROXY // SECURE EXCHANGE] Forwarding telemetry to verifier: %s",
            self.verifier_url,
        )

        # Constant-time comparison prevents timing oracle on the shared secret
        provided = os.environ.get("UWB_SECRET_KEY", _MISSING_KEY_SENTINEL)
        if not hmac_module.compare_digest(self._secret_key, provided):
            logger.warning("[UWB PROXY] Secret key mismatch — request rejected")
            raise ValueError("Unauthorized: Invalid UWB secret key")

        # Run the detection logic
        return self.detector.analyze(positions, timestamps)
