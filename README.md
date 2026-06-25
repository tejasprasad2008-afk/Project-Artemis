# Project Artemis: Aegis Proximity Vault

A sophisticated physical-proximity-gated cryptographic vault demonstration that combines ultra-wideband (UWB) positioning with advanced multi-layer machine learning based encryption. Project Artemis showcases a production-grade security architecture for location-dependent access control.

**Live Demo:** https://project-artemis-psi.vercel.app

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Security Protocol](#security-protocol)
4. [Getting Started](#getting-started)
5. [Backend Guide](#backend-guide)
6. [Frontend Guide](#frontend-guide)
7. [Environment Configuration](#environment-configuration)
8. [API Reference](#api-reference)
9. [Deployment](#deployment)
10. [Security Considerations](#security-considerations)

## Overview

### Project Goals

Project Artemis demonstrates how modern cryptographic techniques can enforce location-based access control. The system:

- Simulates real-time UWB positioning in a React-based office blueprint interface
- Enforces a three-layer cascading entropy-gated ML-KEM security protocol
- Logs all security events to a MongoDB-backed SIEM dashboard
- Provides administrative security monitoring via a protected REST API
- Implements rate limiting and IP filtering for defense against abuse

### Use Cases

- Secure vault access requiring physical proximity verification
- Location-dependent credential distribution
- Proximity-gated classified information access
- Military or intelligence applications with location requirements
- Research into ML-KEM (a NIST-standardized post-quantum algorithm)

## Architecture

### System Overview

The system consists of three primary components:

```
Frontend (React)
    |
    | HTTP/REST
    |
Backend (FastAPI)
    |
    +-- MongoDB (Event Logging & Waitlist)
    |
    +-- UWB Verifier Service (External)
```

### Directory Structure

```
project-root/
├── backend/
│   ├── server.py                 (FastAPI entry point)
│   ├── requirements.txt           (Python dependencies)
│   ├── .env.example               (Environment template)
│   ├── api/
│   │   └── router.py              (Route definitions)
│   ├── security/
│   │   ├── chunks.py              (Position stream attestation)
│   │   ├── cascade.py             (Three-layer CEG-KEM protocol)
│   │   ├── entropy.py             (Shannon entropy computation)
│   │   ├── siem.py                (Security event logging)
│   │   └── uwb_proxy.py            (UWB verifier client)
│   └── tests/
│       ├── test_chunks.py
│       ├── test_cascade.py
│       ├── test_entropy.py
│       └── test_siem.py
├── frontend/
│   ├── src/
│   │   ├── App.js                 (Main React component)
│   │   ├── components/
│   │   │   └── ui/                (shadcn/ui components)
│   │   ├── styles/
│   │   │   ├── artemis-design.css (Custom design tokens)
│   │   │   └── artemis-theme.css  (Theme configuration)
│   │   └── public/
│   │       └── office-blueprint.png (Vault location map)
│   ├── package.json
│   ├── .env                       (Frontend environment)
│   └── yarn.lock
└── vercel.json                    (Vercel deployment config)
```

### Backend Architecture

#### Server Entry Point (server.py)

The FastAPI application serves as the central hub:

- All API routes are mounted under `/api` via `api_router`
- Uses `motor` for async MongoDB connections
- Implements middleware for rate limiting via `fastapi-guard`
- Provides CORS configuration for frontend communication
- Includes health check endpoints for monitoring

#### API Routes

**Waitlist Management**
- Endpoint: `POST /api/waitlist`
- Function: Stores user signup information in MongoDB
- Integration: Sends confirmation emails via Resend API
- Response: User token and confirmation status

**Position Verification**
- Endpoint: `POST /api/verify-position`
- Function: Receives UWB coordinates from the frontend
- Security: Runs the complete CascadeMLKEM protocol
- Response: Session key encapsulation for vault access

**Vault Decryption**
- Endpoint: `POST /api/decrypt`
- Function: Decrypts vault data after quorum validation
- Requirement: Must pass all three security gates
- Response: Decrypted sensitive data or access denied

**SIEM Dashboard**
- Endpoint: `GET /api/security/events`
- Function: Retrieves security event logs
- Authentication: Protected by `X-Artemis-Admin-Key` header
- Response: Paginated security events with timestamps

**Security Summary**
- Endpoint: `GET /api/security/summary`
- Function: Aggregates security metrics and anomalies
- Authentication: Protected by `X-Artemis-Admin-Key` header
- Response: Statistics on access attempts and events

#### Security Modules

##### chunks.py: Position Stream Attestation

The `ChunkAttestor` class processes continuous position data:

- Divides the position stream into HMAC-signed time windows (chunks)
- Each chunk includes timestamp, position coordinates, and cryptographic signature
- Validates chunk integrity using shared secrets
- Stores recent chunks in a sliding window buffer

The `QuorumValidator` class enforces quorum requirements:

- Checks that K-of-N recent chunks attest to valid position
- Configurable threshold (default K=3 of N=5)
- Rejects positions outside the secure zone perimeter
- Tracks validation history for audit trails

##### cascade.py: Three-Layer CEG-KEM Protocol

The `CascadeMLKEM` class implements the core security protocol with three sequential gates:

**Layer 1: Entropy Gate**
- Computes Shannon entropy of position samples
- Validates that recent positions show sufficient variability
- Purpose: Prevents static position replay attacks
- Failure action: Immediately rejects the request

**Layer 2: Velocity and Nonce Gate**
- Calculates velocity vector from position deltas
- Validates velocity is within realistic human movement bounds (0.5 to 2.0 m/s)
- Enforces cryptographic nonce uniqueness per session
- Purpose: Prevents teleportation attacks and replay attacks
- Failure action: Immediately rejects the request

**Layer 3: Quorum and Role Gate**
- Invokes QuorumValidator to confirm K-of-N recent chunks
- Checks user's assigned role and clearance level
- Verifies role permits access to requested vault data
- Purpose: Implements multi-signature-like position consensus
- Failure action: Immediately rejects the request

If all three layers pass, the system:

1. Generates a shared secret using HKDF-SHA256
2. Encapsulates a session key using ML-KEM
3. Returns the encapsulated key to the frontend
4. Logs the successful access event

If any layer fails, the entire cascade collapses:
- Returns a generic error to prevent information leakage
- Logs the failed attempt with reason code
- Increments attack counter for rate limiting

##### entropy.py: Shannon Entropy Computation

Calculates information-theoretic entropy from position data:

- Discretizes continuous coordinates into spatial bins
- Computes probability distribution of bin occupancy
- Calculates Shannon entropy: H = -sum(p_i * log2(p_i))
- Returns entropy value and confidence bounds

Used by the cascade protocol to detect:
- Static positions (entropy near zero)
- Implausibly random positions (entropy too high)
- Realistic human movement patterns (entropy in optimal range)

##### siem.py: Security Event Logging

The `SIEMLogger` class provides structured security event recording:

- Event types: ACCESS_GRANTED, ACCESS_DENIED, ANOMALY_DETECTED, RATE_LIMIT_EXCEEDED
- Stores to MongoDB collection `security_events`
- Fields: timestamp, event_type, user_id, position, gate_results, metadata
- Supports querying recent events and generating summary statistics
- Integrates with all security modules for comprehensive audit trail

##### uwb_proxy.py: UWB Verifier Client

The `UWBProxyClient` class communicates with an external UWB service:

- Sends HMAC-signed position requests to external verifier
- Receives cryptographic proofs of position authenticity
- Validates responses using shared secrets
- Handles timeout and network error gracefully
- Supports both synchronous and asynchronous operation

### Frontend Architecture

#### Main Application (App.js)

Single-page React application providing:

- Office blueprint visualization with canvas rendering
- Real-time position simulation along predefined paths
- Interactive UI for vault access attempts
- Visual feedback on security gate results
- Admin dashboard for security event review

#### Blueprint Visualization

The frontend displays:

- PNG image of an office floor plan (`public/office-blueprint.png`)
- Secure zone perimeter defined as percentage coordinates
- Position indicator (simulated UWB tag) moving on the blueprint
- Heat map of access attempts (optional, based on historical data)

#### Position Simulation

The UWB simulator:

- Generates realistic position traces along office corridors
- Includes random jitter to simulate sensor noise
- Supports multiple predefined paths for testing
- Can be configured to enter or stay outside secure zone
- Emits position updates at configurable frequency (default 100 ms)

#### Component Structure

- `App.js`: Main container, state management, API coordination
- `BlueprintCanvas`: Renders office map and position indicator
- `SecurityGatesDisplay`: Shows real-time gate evaluation results
- `VaultAccessPanel`: UI for triggering access attempts
- `EventLog`: Displays recent security events from SIEM
- `AdminDashboard`: Shows aggregated security metrics

#### Styling

- Base framework: Tailwind CSS
- Component library: shadcn/ui (React components on Radix UI)
- Custom design tokens in `artemis-design.css`
- Theme colors in `artemis-theme.css`
- Responsive design for desktop and tablet displays

## Security Protocol

### Cascading Entropy-Gated ML-KEM (CEG-KEM)

The protocol combines multiple security mechanisms:

#### Overview

CEG-KEM enforces a "defense in depth" model where a single compromised subsystem cannot grant unauthorized access. Each layer is independent:

- **Entropy Layer**: Position data must be natural (not static or random)
- **Velocity Layer**: Movement speed must be physically plausible
- **Quorum Layer**: Multiple position attestations must agree

#### Detailed Protocol Flow

```
Client sends: {user_id, recent_positions, session_nonce}
    |
    v
[Entropy Gate]
    Check: Shannon entropy of positions >= threshold
    On fail: Reject, log ENTROPY_INSUFFICIENT
    On pass: Continue
    |
    v
[Velocity Gate]
    Check: Calculated velocity <= 2.0 m/s (human speed limit)
    Check: Velocity >= 0.5 m/s (must be moving or idle, not teleporting)
    Check: Session nonce not seen before
    On fail: Reject, log VELOCITY_ANOMALY or REPLAY_DETECTED
    On pass: Continue
    |
    v
[Quorum Gate]
    Check: K recent position chunks signed with correct HMAC
    Check: K >= threshold (default 3 of 5)
    Check: User role permits vault access
    On fail: Reject, log QUORUM_FAILED or UNAUTHORIZED_ROLE
    On pass: Continue
    |
    v
[Key Encapsulation]
    Generate shared secret from validated positions + nonce
    Derive key material using HKDF-SHA256
    Encapsulate session key using ML-KEM
    Return encapsulated key to client
    Log: ACCESS_GRANTED with gate_results
    |
    v
Client receives: {encapsulated_key, session_id}
```

#### ML-KEM Integration

The current implementation uses simulated ML-KEM:

- Encapsulation simulates NIST's ML-KEM using HKDF-SHA256 and AES
- Supports configurable key sizes (512, 768, 1024 bits)
- Designed for drop-in replacement with liboqs (OpenQuantumSafe C library)

Production deployment would integrate `liboqs-python` with code changes in `cascade.py` only:

```python
# Current simulation approach
from Crypto.Protocol.KDF import HKDF
key = HKDF(shared_secret, key_length, salt, hashmod=SHA256)

# Production approach with liboqs
import liboqs
kem = liboqs.KEM("ML-KEM-768")
encapsulated_key, shared_secret = kem.encap_secret()
```

#### Threat Model

The protocol protects against:

1. **Replay Attacks**: Nonce uniqueness prevents reuse of captured position + key data
2. **Teleportation Attacks**: Velocity constraints prevent jumping between distant locations
3. **Static Position Attacks**: Entropy requirements prevent holding fixed position
4. **Man-in-the-Middle**: HMAC signing on position chunks prevents modification
5. **Unauthorized Access**: Role-based checks prevent privilege escalation
6. **Timing Attacks**: Cascade failure is indistinguishable from genuine authorization rejection

The protocol does NOT protect against:

- Compromise of the shared UWB secret key
- Physical coercion to move the UWB tag to authorized position
- Side-channel attacks on cryptographic operations
- Database compromise (MongoDB must be secured separately)

## Getting Started

### Prerequisites

- Python 3.10 or later
- Node.js 16+ and Yarn
- MongoDB 5.0+ (local or cloud instance)
- Git for version control

### Quick Start

#### Backend Setup

```bash
# Clone repository
git clone https://github.com/mapzink/Project-Artemis.git
cd Project-Artemis

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your MongoDB URL and API keys

# Run development server
uvixorn backend.server:app --reload --port 8001
```

The backend will start on http://localhost:8001 with automatic reload on code changes.

#### Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
yarn install

# Create environment file
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Start development server
yarn start
```

The frontend will open on http://localhost:3000 and connect to the backend.

### Verification

To verify the setup is working:

1. Open http://localhost:3000 in a browser
2. You should see the office blueprint and position indicator
3. Click "Request Vault Access" to trigger a position verification
4. Check backend logs for security gate results

## Backend Guide

### Running Tests

```bash
# Run all tests with verbose output
pytest backend/tests/ -v

# Run a specific test file
pytest backend/tests/test_cascade.py -v

# Run with coverage report
pytest backend/tests/ --cov=backend --cov-report=html
```

Test files:
- `test_chunks.py`: ChunkAttestor and QuorumValidator tests
- `test_cascade.py`: Full three-layer protocol tests
- `test_entropy.py`: Shannon entropy computation tests
- `test_siem.py`: Event logging and retrieval tests

### Code Quality Tools

```bash
# Linting (style violations)
flake8 backend/

# Type checking
mypy backend/

# Code formatting check
black backend/ --check

# Import sorting check
isort backend/ --check

# Apply formatting
black backend/
isort backend/
```

### Adding New Endpoints

To add a new API route:

1. Create handler function in appropriate module
2. Add route definition to `backend/api/router.py`
3. Include request/response validation using Pydantic models
4. Add authentication middleware if admin-only
5. Log security events using `SIEMLogger`
6. Write tests in `backend/tests/`

Example:

```python
# In backend/api/router.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class PositionRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float

@router.post("/new-endpoint")
async def new_endpoint(request: PositionRequest):
    """Handles new functionality."""
    # Implementation here
    return {"status": "success"}
```

### Database Schema

MongoDB collections used:

**waitlist collection**
```json
{
  "_id": "ObjectId",
  "email": "user@example.com",
  "timestamp": "2026-06-24T10:00:00Z",
  "verified": false
}
```

**security_events collection**
```json
{
  "_id": "ObjectId",
  "timestamp": "2026-06-24T10:00:00Z",
  "event_type": "ACCESS_GRANTED|ACCESS_DENIED|ANOMALY_DETECTED",
  "user_id": "user123",
  "position": {"x": 45.5, "y": 32.1},
  "gate_results": {
    "entropy": true,
    "velocity": true,
    "quorum": true
  },
  "metadata": {}
}
```

## Frontend Guide

### Development Commands

```bash
# Start development server (with auto-reload)
yarn start

# Production build
yarn build

# Run tests
yarn test

# Eject (warning: cannot be undone)
yarn eject
```

### Component Props Reference

#### BlueprintCanvas

```jsx
<BlueprintCanvas
  blueprintUrl="path/to/blueprint.png"
  secureZoneBounds={{top: 20, left: 30, width: 40, height: 35}}
  position={{x: 45, y: 50}}
  isInsideSecureZone={true}
/>
```

#### SecurityGatesDisplay

```jsx
<SecurityGatesDisplay
  gates={{
    entropy: {passed: true, message: "Normal movement detected"},
    velocity: {passed: true, message: "Speed within limits"},
    quorum: {passed: false, message: "Quorum check failed"}
  }}
/>
```

#### EventLog

```jsx
<EventLog
  events={[
    {id: 1, type: "ACCESS_GRANTED", timestamp: "2026-06-24T10:00:00Z"},
    {id: 2, type: "ANOMALY_DETECTED", timestamp: "2026-06-24T10:01:00Z"}
  ]}
  maxItems={20}
/>
```

### Styling Customization

Design tokens are defined in `src/styles/artemis-design.css`:

```css
:root {
  --artemis-primary: #0066cc;
  --artemis-success: #00aa44;
  --artemis-danger: #ff3333;
  --artemis-warning: #ffaa00;
}
```

Modify these variables to change the theme throughout the application.

### Environment Variables

Create `frontend/.env`:

```
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_LOG_LEVEL=debug
REACT_APP_POSITION_UPDATE_INTERVAL=100
```

All variables must be prefixed with `REACT_APP_` to be exposed to the frontend.

## Environment Configuration

### Backend Environment (.env)

```bash
# MongoDB Connection
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=artemis_prod

# UWB Security
UWB_SECRET_KEY=your-uwb-shared-secret-key-here

# Admin API Authentication
ARTEMIS_ADMIN_KEY=your-strong-admin-key-here

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com,https://project-artemis-psi.vercel.app

# Email Service (Resend)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxx

# Security Parameters
ENTROPY_THRESHOLD=3.5
VELOCITY_MAX_MS=2.0
VELOCITY_MIN_MS=0.5
QUORUM_K=3
QUORUM_N=5

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

### Frontend Environment (.env)

```bash
# Backend API
REACT_APP_BACKEND_URL=http://localhost:8001

# Logging
REACT_APP_LOG_LEVEL=info

# UWB Simulation
REACT_APP_POSITION_UPDATE_INTERVAL=100
REACT_APP_SIMULATION_SPEED=1.0
```

### Production Secrets Management

For production deployment:

1. Use environment-specific .env files (.env.production)
2. Never commit secrets to version control
3. Use a secrets manager: AWS Secrets Manager, HashiCorp Vault, or GitHub Secrets
4. Rotate API keys regularly (quarterly minimum)
5. Use strong, randomly generated keys (minimum 32 characters, mixed case + numbers + symbols)

## API Reference

### POST /api/waitlist

Register for early access to the vault.

**Request:**
```json
{
  "email": "user@example.com",
  "name": "John Doe"
}
```

**Response (200):**
```json
{
  "token": "waitlist_token_abc123",
  "position": 42,
  "estimated_date": "2026-07-01"
}
```

**Response (400):**
```json
{
  "error": "Invalid email format"
}
```

### POST /api/verify-position

Verify position and encapsulate session key.

**Request:**
```json
{
  "user_id": "user123",
  "positions": [
    {"timestamp": 1687530000000, "x": 45.5, "y": 32.1},
    {"timestamp": 1687530100000, "x": 45.6, "y": 32.2},
    {"timestamp": 1687530200000, "x": 45.7, "y": 32.3}
  ],
  "nonce": "unique_session_nonce_value"
}
```

**Response (200):**
```json
{
  "session_id": "session_abc123",
  "encapsulated_key": "base64_encoded_key_material",
  "gate_results": {
    "entropy": {
      "passed": true,
      "value": 4.2,
      "threshold": 3.5
    },
    "velocity": {
      "passed": true,
      "speed_ms": 1.2,
      "threshold": 2.0
    },
    "quorum": {
      "passed": true,
      "chunks_valid": 4,
      "chunks_required": 3
    }
  }
}
```

**Response (403):**
```json
{
  "error": "Access denied",
  "reason": "QUORUM_FAILED",
  "gate_results": {
    "entropy": {"passed": true},
    "velocity": {"passed": true},
    "quorum": {"passed": false}
  }
}
```

### POST /api/decrypt

Decrypt vault data using session key.

**Request:**
```json
{
  "session_id": "session_abc123",
  "encrypted_data": "base64_encrypted_vault_data"
}
```

**Response (200):**
```json
{
  "vault_data": {
    "classified_info": "decrypted content here",
    "access_level": "top_secret",
    "timestamp": "2026-06-24T10:00:00Z"
  }
}
```

**Response (403):**
```json
{
  "error": "Session expired or invalid"
}
```

### GET /api/security/events

Retrieve security event logs (admin only).

**Headers:**
```
X-Artemis-Admin-Key: your-admin-key-here
```

**Query Parameters:**
- `limit`: Number of events (default 100, max 1000)
- `offset`: Pagination offset (default 0)
- `event_type`: Filter by type (ACCESS_GRANTED, ACCESS_DENIED, ANOMALY_DETECTED)
- `user_id`: Filter by user
- `start_time`: ISO 8601 timestamp
- `end_time`: ISO 8601 timestamp

**Response (200):**
```json
{
  "events": [
    {
      "id": "event123",
      "timestamp": "2026-06-24T10:00:00Z",
      "event_type": "ACCESS_GRANTED",
      "user_id": "user123",
      "position": {"x": 45.5, "y": 32.1},
      "gate_results": {
        "entropy": true,
        "velocity": true,
        "quorum": true
      }
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

**Response (401):**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing X-Artemis-Admin-Key"
}
```

### GET /api/security/summary

Get aggregated security metrics (admin only).

**Headers:**
```
X-Artemis-Admin-Key: your-admin-key-here
```

**Response (200):**
```json
{
  "period": "24h",
  "total_access_attempts": 156,
  "successful_accesses": 142,
  "failed_accesses": 14,
  "success_rate": 0.91,
  "anomalies_detected": 3,
  "top_failure_reasons": [
    {"reason": "QUORUM_FAILED", "count": 8},
    {"reason": "VELOCITY_ANOMALY", "count": 4},
    {"reason": "ENTROPY_INSUFFICIENT", "count": 2}
  ],
  "unique_users": 23,
  "peak_activity_hour": 14
}
```

## Deployment

### Frontend Deployment (Vercel)

The project is automatically deployed to Vercel at: https://project-artemis-psi.vercel.app

The `vercel.json` configuration handles frontend deployment:

```json
{
  "buildCommand": "yarn build",
  "outputDirectory": "build"
}
```

**Steps:**

1. Push code to GitHub
2. Connect repository to Vercel dashboard
3. Set environment variables in Vercel project settings
4. Deploy triggers automatically on push to main branch

```bash
# Manual deployment
npm install -g vercel
vercel deploy --prod
```

### Backend Deployment (Self-Hosted or Cloud)

#### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t artemis-backend .
docker run -p 8000:8000 --env-file .env artemis-backend
```

#### AWS EC2 Deployment

```bash
# SSH into instance
ssh -i key.pem ubuntu@your-instance-ip

# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv

# Clone and setup
git clone https://github.com/mapzink/Project-Artemis.git
cd Project-Artemis
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Configure .env with production values

# Run with systemd
sudo cp deployment/artemis.service /etc/systemd/system/
sudo systemctl start artemis
sudo systemctl enable artemis
```

#### Heroku Deployment

```bash
heroku create artemis-backend
heroku config:set MONGO_URL=<production-url>
heroku config:set UWB_SECRET_KEY=<secret>
git push heroku main
```

### Production Checklist

Before deploying to production:

- [ ] All tests pass (`pytest backend/tests/ -v`)
- [ ] Code quality checks pass (flake8, mypy, black, isort)
- [ ] Environment variables configured for production
- [ ] MongoDB backups configured and tested
- [ ] HTTPS/TLS certificates installed
- [ ] Rate limiting configured appropriately
- [ ] Admin API key is strong (32+ characters)
- [ ] CORS origins restricted to known domains (including https://project-artemis-psi.vercel.app)
- [ ] Logging configured and monitored
- [ ] Error tracking (Sentry, etc.) configured
- [ ] Load balancing configured if needed
- [ ] Database indexes created for common queries
- [ ] Security audit completed
- [ ] Incident response plan documented

### Monitoring and Logs

**Backend Logging:**
```bash
# View logs from running container
docker logs -f container_id

# Or from systemd
journalctl -u artemis -f
```

**Security Events:**
Access the SIEM dashboard at: `GET /api/security/events` (admin authenticated)

**Performance Metrics:**
- API response times
- Position verification latency
- ML-KEM encapsulation time
- Database query performance

## Security Considerations

### Threat Analysis

#### Spoofing UWB Signals

**Risk**: Attacker broadcasts fake UWB signals to spoof position.

**Mitigation**:
- HMAC signature on position chunks prevents unauthorized modification
- UWB verifier service validates signal authenticity
- Entropy and velocity checks reject implausible trajectories

#### Compromise of Shared Secrets

**Risk**: If UWB_SECRET_KEY is leaked, attacker can forge positions.

**Mitigation**:
- Store secrets in secure key management system
- Rotate keys quarterly
- Monitor access logs for unauthorized retrieval
- Separate keys by environment (dev/staging/prod)

#### Database Compromise

**Risk**: Attacker gains access to MongoDB and reads security events or positions.

**Mitigation**:
- Enable MongoDB authentication with strong passwords
- Use VPC/network isolation to restrict database access
- Enable MongoDB encryption at rest
- Regular automated backups to separate storage
- Database audit logging enabled

#### Denial of Service (DoS)

**Risk**: Attacker floods API with requests to prevent legitimate access.

**Mitigation**:
- Rate limiting: 100 requests per 60 seconds per IP
- IP filtering/whitelist for admin endpoints
- DDoS protection via Cloudflare or AWS Shield
- Request size limits
- Circuit breaker pattern for cascading failures

#### Timing Side Channels

**Risk**: Cascade failure behavior reveals which gate failed.

**Mitigation**:
- All gate failures return generic error message
- Response times made constant regardless of failure type
- No detailed error messages in production

### Best Practices

#### Development

- Never commit secrets or credentials
- Use separate dev/staging/prod environments
- Code review all security-related changes
- Peer review test cases for edge cases

#### Deployment

- Use HTTPS/TLS for all API communication
- Enable CORS only for known frontend domains
- Implement request signing for admin endpoints
- Log all administrative access
- Monitor error rates and alert on anomalies

#### Maintenance

- Keep dependencies updated (security patches)
- Run regular security audits
- Test disaster recovery procedures
- Review logs for suspicious patterns
- Conduct quarterly penetration testing

#### Incident Response

If a security breach is suspected:

1. Immediately revoke all compromised API keys
2. Rotate database credentials
3. Review access logs for unauthorized activity
4. Notify affected users
5. Conduct post-incident review
6. Update security procedures based on findings

## Contributing

To contribute to Project Artemis:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and commit (`git commit -am 'Add feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

Please ensure all tests pass and code quality checks are satisfied before submitting a PR.

## License

Project Artemis is licensed under the MIT License. See LICENSE file for details.

## Contact and Support

For questions, issues, or feature requests:

- Open an issue on GitHub
- Contact the development team at artemis-dev@example.com
- Review the technical documentation in CLAUDE.md

---

Last updated: June 24, 2026
Project Artemis Development Team
