# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Artemis ("Aegis Proximity Vault") is a physical-proximity-gated cryptographic vault demo. A React frontend visualizes a UWB (ultra-wideband) position simulation on an office blueprint; the FastAPI backend enforces a three-layer Cascading Entropy-Gated ML-KEM (CEG-KEM) security protocol before returning decrypted vault data.

## Commands

### Backend

```bash
# Install dependencies (from repo root)
pip install -r backend/requirements.txt

# Run server (from repo root — module imports require this)
uvicorn backend.server:app --reload --port 8001

# Run all backend tests
pytest backend/tests/

# Run a single test file
pytest backend/tests/test_chunks.py -v

# Lint / type-check
flake8 backend/
mypy backend/
black backend/ --check
isort backend/ --check
```

### Frontend

```bash
cd frontend

# Install
yarn install

# Dev server (expects backend on REACT_APP_BACKEND_URL from frontend/.env)
yarn start

# Production build
yarn build
```

## Architecture

### Backend (`backend/`)

**`server.py`** — FastAPI entry point. All routes are mounted under `/api` via `api_router`. Key endpoints:
- `POST /api/waitlist` — waitlist sign-up, stored in MongoDB, sends email via Resend
- `POST /api/verify-position` — receives UWB coordinates, runs `CascadeMLKEM` to encapsulate a session key
- `POST /api/decrypt` — decrypts vault data after quorum-gate passes
- `GET /api/security/events` / `/api/security/summary` — SIEM dashboard, protected by `X-Artemis-Admin-Key` header
- MongoDB via `motor` (async); `guard`/`fastapi-guard` middleware for rate-limiting and IP filtering

**`backend/security/`** — the CEG-KEM protocol, four modules:

| Module | Role |
|---|---|
| `chunks.py` | `ChunkAttestor` splits the position stream into HMAC-signed time-windows; `QuorumValidator` checks K-of-N recent chunks attest valid position |
| `cascade.py` | `CascadeMLKEM` — 3-layer gate (entropy → velocity/nonce → quorum + role). All three must pass; failure at any layer collapses the key cascade |
| `entropy.py` | Shannon entropy computation on position samples |
| `siem.py` | `SIEMLogger` — structured security event logging (stored in MongoDB) |
| `uwb_proxy.py` | `UWBProxyClient` — thin client to an external UWB verifier service (HMAC-signed requests) |

The simulated ML-KEM uses HKDF-SHA256; the architecture is designed so that swapping in `liboqs` is a drop-in replacement at `_encapsulate`/`_decapsulate`.

### Frontend (`frontend/src/`)

Single-page app, all UI lives in `App.js`. Key pieces:
- Office blueprint PNG rendered as a canvas/image; a `concealedSecureZone` bounding box defines the vault perimeter in percentage coordinates
- Simulates UWB coordinate streams locally, calls `/api/verify-position` and `/api/decrypt`
- UI primitives from shadcn/ui (`src/components/ui/`) + Tailwind CSS
- Custom design tokens in `src/styles/artemis-*.css`
- `REACT_APP_BACKEND_URL` (in `frontend/.env`) controls the API base URL

### Environment Setup

Copy `backend/.env.example` → `backend/.env` and fill in:
- `MONGO_URL`, `DB_NAME`
- `UWB_SECRET_KEY` — must match the UWB verifier
- `ARTEMIS_ADMIN_KEY` — protects SIEM endpoints
- `CORS_ORIGINS` — comma-separated allowed frontend origins
- `RESEND_API_KEY` — optional, for waitlist emails

Create `frontend/.env`:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Deployment

`vercel.json` at the repo root configures Vercel for the frontend. The backend is deployed separately (not via Vercel).
