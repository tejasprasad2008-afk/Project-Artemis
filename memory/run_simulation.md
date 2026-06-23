# Running and Testing the Aegis Vault Simulation

This guide provides step-by-step instructions to start the backend, run the frontend, and test the `fastapi-guard` security middleware.

---

## 1. Start the Backend Server

Start the local FastAPI server with the virtual environment's Python (3.14) and PYTHONPATH configured:

```bash
PYTHONPATH=. /Users/tejasprasad/TraceTree/venv/bin/python3.14 -m uvicorn backend.server:app --port 8000 --reload
```

*Note: The server has already been tested and runs on `http://127.0.0.1:8000` with the `fastapi-guard` security middleware active.*

---

## 2. Start the Frontend App

To connect the React dashboard to your local backend (instead of the preview server), run the frontend start command with the local backend URL:

```bash
REACT_APP_BACKEND_URL=http://localhost:8000 yarn --cwd frontend start
```

Alternatively, you can edit [frontend/.env](file:///Users/tejasprasad/Project-Artemis/frontend/.env) and update the backend URL:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

Then simply start it:
```bash
yarn --cwd frontend start
```

---

## 3. Testing the `fastapi-guard` Security Middleware

We configured the `fastapi-guard` middleware with several threat defenses (rate-limiting, automated IP banning, and blocked user agents). You can trigger and test these rules directly:

### Test A: Blocked User Agents (e.g. Scanners)
The middleware is configured to automatically block known scanners like `sqlmap` and `nikto`. You can test this using `curl`:

```bash
curl -H "User-Agent: sqlmap" http://localhost:8000/api/waitlist
```
**Expected Response:**
`403 Forbidden` / `User-Agent not allowed` (since `sqlmap` is in the blocked user-agents list).

### Test B: Rate Limiting and Auto-Banning
The middleware limits requests to **100 requests per minute** per IP and automatically bans an IP after **5 failed requests** (e.g., triggering invalid status codes).

To verify, you can query a rate-limited endpoint or repeatedly trigger authentication failures.

---

## 4. Threat Logging and SIEM Dashboards

To view the threat logs processed by our CEG-KEM security engine and SIEM logger, use these local endpoints:

*   **View Recent Security Events**:
    ```bash
    curl http://localhost:8000/api/security/events
    ```
*   **View Aggregated Threat Summary**:
    ```bash
    curl http://localhost:8000/api/security/summary
    ```

You can view these logs directly in your browser or through the live telemetry log panel on the frontend dashboard.
