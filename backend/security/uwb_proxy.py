import os
import logging
from typing import List, Tuple
from backend.security.entropy import EntropyAnomalyDetector, EntropyResult

logger = logging.getLogger(__name__)

class UWBProxyClient:
    """
    Simulates a secure server-to-server proxy to the third-party UWB verifier.
    
    Ensures the client-side/frontend never has access to the UWB API credentials
    by keeping the API key on the backend and forwarding the request through this proxy.
    """

    def __init__(self) -> None:
        self.secret_key = os.environ.get("UWB_SECRET_KEY", "artemis_secure_uwb_token_2026")
        self.verifier_url = os.environ.get("UWB_VERIFIER_URL", "https://api.external-uwb.io/v1/verify")
        self.detector = EntropyAnomalyDetector()

    def verify_position(
        self, positions: List[Tuple[float, float]], timestamps: List[float]
    ) -> EntropyResult:
        # Simulate the secure headers and payload that would be sent over HTTP
        headers = {
            "X-Artemis-UWB-Secret": self.secret_key,
            "Content-Type": "application/json"
        }
        
        # Log the outgoing proxy request
        logger.info(
            f"[UWB PROXY // SECURE EXCHANGE] Proxying telemetry to verifier: {self.verifier_url} | "
            f"Secret Key attached: {self.secret_key[:6]}*** (hidden from client)"
        )
        
        # Act as the receiving API gateway by verifying the secret key
        if self.secret_key != "artemis_secure_uwb_token_2026":
            raise ValueError("Unauthorized: Invalid X-Artemis-UWB-Secret token")

        # Run the detection logic
        return self.detector.analyze(positions, timestamps)
