from fastapi import FastAPI, APIRouter, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import secrets
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Any, Dict, List, Optional, Tuple
import uuid
from datetime import datetime, timezone

from backend.security.entropy import EntropyAnomalyDetector, EntropyThresholds
from backend.security.chunks import ChunkAttestor, QuorumValidator
from backend.security.cascade import CascadeMLKEM
from backend.security.siem import SIEMLogger, EventType
from backend.security.uwb_proxy import UWBProxyClient

import sys
from guard import SecurityConfig
from guard.middleware import SecurityMiddleware


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ---------------------------------------------------------------------------
# Admin API key — used to protect internal/SIEM endpoints.
# Set ARTEMIS_ADMIN_KEY in env; a random key is generated for dev if absent.
# ---------------------------------------------------------------------------
_admin_key_header = APIKeyHeader(name="X-Artemis-Admin-Key", auto_error=False)
_ADMIN_KEY: str = os.environ.get("ARTEMIS_ADMIN_KEY") or secrets.token_hex(32)
if not os.environ.get("ARTEMIS_ADMIN_KEY"):
    logging.getLogger(__name__).warning(
        "ARTEMIS_ADMIN_KEY not set — generated ephemeral key for this session: %s",
        _ADMIN_KEY,
    )


async def _require_admin_key(api_key: Optional[str] = Security(_admin_key_header)) -> str:
    """FastAPI dependency that enforces the admin API key."""
    if not api_key or not secrets.compare_digest(api_key, _ADMIN_KEY):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: valid X-Artemis-Admin-Key required",
        )
    return api_key

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# CEG-KEM security module initialisation
# ---------------------------------------------------------------------------
siem_logger = SIEMLogger()
chunk_attestor = ChunkAttestor()
quorum_validator = QuorumValidator(required_k=3, window_n=5, max_chunk_age_seconds=30.0)
cascade = CascadeMLKEM(
    siem=siem_logger,
    chunk_attestor=chunk_attestor,
    quorum_validator=quorum_validator,
)
uwb_proxy = UWBProxyClient()


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


class WaitlistCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    firm: str = Field(..., min_length=2, max_length=160)
    email: EmailStr


class WaitlistEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    firm: str = "Undisclosed firm"
    email: EmailStr
    segment: str = "Local wealth / law office sandbox"
    access_tier: str = "Sandboxed early access"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# CEG-KEM request / response models
# ---------------------------------------------------------------------------

class PositionSample(BaseModel):
    """A single coordinate sample with timestamp."""
    x: float
    y: float
    t: float  # Unix timestamp (seconds)


class VerifyPositionRequest(BaseModel):
    """Request body for /api/verify-position."""
    positions: List[PositionSample] = Field(..., min_length=2)
    session_nonce: str = Field(..., min_length=8, max_length=128)


class DecryptRequest(BaseModel):
    """Request body for /api/decrypt — full CEG-KEM cascade."""
    positions: List[PositionSample] = Field(..., min_length=6)
    session_nonce: str = Field(..., min_length=8, max_length=128)
    user_role: str = Field(..., min_length=1, max_length=64)

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Project Artemis API online"}


@api_router.post("/waitlist", response_model=WaitlistEntry, status_code=201)
async def create_waitlist_entry(input: WaitlistCreate):
    clean_email = input.email.lower().strip()
    clean_name = " ".join(input.name.strip().split())
    clean_firm = " ".join(input.firm.strip().split())

    existing = await db.waitlist_entries.find_one({"email": clean_email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="This email is already on the Artemis sandbox list.")

    entry = WaitlistEntry(name=clean_name, firm=clean_firm, email=clean_email)
    doc = entry.model_dump()
    await db.waitlist_entries.insert_one(doc)
    return entry


@api_router.get("/waitlist", response_model=List[WaitlistEntry])
async def get_waitlist_entries():
    entries = await db.waitlist_entries.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return entries

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app

# ---------------------------------------------------------------------------
# CEG-KEM endpoints
# ---------------------------------------------------------------------------

@api_router.post("/verify-position")
async def verify_position(body: VerifyPositionRequest, request: Request):
    """
    Entropy-only position verification.

    Runs the entropy anomaly detector against the submitted coordinate
    stream and returns the classification.  Does NOT run the full
    cascade or produce a decrypt key.
    """
    positions = [(s.x, s.y) for s in body.positions]
    timestamps = [s.t for s in body.positions]
    source_ip = request.client.host if request.client else None

    result = uwb_proxy.verify_position(positions, timestamps)

    event_type = (
        EventType.POSITION_VERIFIED
        if result.anomaly.value == "genuine"
        else EventType.POSITION_REJECTED
    )
    siem_logger.emit(
        event_type,
        f"Position verification: {result.anomaly.value}",
        {
            "entropy_score": result.score,
            "anomaly": result.anomaly.value,
            "velocity_max": result.velocity_max,
            "jitter": result.jitter_score,
            "nonce": body.session_nonce,
        },
        source_ip=source_ip,
    )

    return {
        "verified": result.anomaly.value == "genuine",
        "anomaly": result.anomaly.value,
        "entropy_score": round(result.score, 4),
        "velocity_max": round(result.velocity_max, 2),
        "jitter_score": round(result.jitter_score, 4),
        "sample_count": result.sample_count,
    }


@api_router.post("/decrypt")
async def decrypt_vault(body: DecryptRequest, request: Request):
    """
    Full CEG-KEM cascade — entropy + velocity + nonce + role gates.

    On success, returns the hex-encoded decrypt key.
    On failure, returns the layer at which the cascade collapsed and why.
    """
    positions = [(s.x, s.y) for s in body.positions]
    timestamps = [s.t for s in body.positions]
    source_ip = request.client.host if request.client else None

    result = cascade.execute(
        positions=positions,
        timestamps=timestamps,
        session_nonce=body.session_nonce,
        user_role=body.user_role,
        source_ip=source_ip,
    )

    if not result.success:
        siem_logger.emit(
            EventType.DECRYPT_DENIED,
            f"Decrypt denied: {result.failure_reason.value if result.failure_reason else 'unknown'}",
            {
                "cascade_id": result.cascade_id,
                "layer_reached": result.layer_reached,
                "failure_reason": result.failure_reason.value if result.failure_reason else None,
            },
            source_ip=source_ip,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "cascade_failure",
                "failure_reason": result.failure_reason.value if result.failure_reason else "unknown",
                "layer_reached": result.layer_reached,
                "cascade_id": result.cascade_id,
            },
        )

    return {
        "success": True,
        "cascade_id": result.cascade_id,
        "decrypt_key": result.decrypt_key.hex() if result.decrypt_key else None,
        "entropy_score": round(result.entropy_result.score, 4) if result.entropy_result else None,
        "layer_reached": result.layer_reached,
    }


@api_router.get("/security/events")
async def get_security_events(
    count: int = 50,
    severity: Optional[str] = None,
    _key: str = Security(_require_admin_key),
):
    """Retrieve recent security events for the threat dashboard (admin only)."""
    from backend.security.siem import Severity

    severity_filter = None
    if severity:
        try:
            severity_filter = Severity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    events = siem_logger.get_recent_events(
        count=count, severity_filter=severity_filter
    )
    return {"events": [e.to_dict() for e in events]}


@api_router.get("/security/summary")
async def get_security_summary(
    _key: str = Security(_require_admin_key),
):
    """Threat summary dashboard data (admin only)."""
    return siem_logger.get_threat_summary()


app.include_router(api_router)

# ---------------------------------------------------------------------------
# CORS — wildcard origin + allow_credentials=True is a security misconfiguration.
# When credentials are included (cookies/auth headers), origins must be explicit.
# ---------------------------------------------------------------------------
_raw_cors = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
_cors_origins = [o.strip() for o in _raw_cors.split(',') if o.strip()]
if '*' in _cors_origins:
    # Wildcard with credentials is spec-forbidden and exploitable — fall back to
    # localhost only and log a warning so this is visible at startup.
    logging.getLogger(__name__).warning(
        "CORS_ORIGINS=* with allow_credentials=True is a security misconfiguration. "
        "Restricting to http://localhost:3000. Set CORS_ORIGINS to your production domain."
    )
    _cors_origins = ['http://localhost:3000']

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Artemis-Admin-Key"],
)

# Initialize fastapi-guard middleware
is_testing = "pytest" in sys.modules
guard_config = SecurityConfig(
    enable_rate_limiting=not is_testing,
    rate_limit=100,             # 100 requests per minute
    rate_limit_window=60,
    enable_ip_banning=not is_testing,
    auto_ban_threshold=5,
    blocked_user_agents=["sqlmap", "nikto"],
    exclude_paths=["/api/status"],
)

app.add_middleware(SecurityMiddleware, config=guard_config)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()