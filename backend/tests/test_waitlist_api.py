"""Waitlist API critical path tests: create/list/duplicate handling."""

import os
from pathlib import Path
import uuid

import pytest
import requests


def _read_backend_url_from_frontend_env() -> str:
    env_path = Path("/app/frontend/.env")
    if not env_path.exists():
        pytest.skip("frontend/.env missing; cannot resolve REACT_APP_BACKEND_URL")

    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value.rstrip("/")
    pytest.skip("REACT_APP_BACKEND_URL not found in frontend/.env")


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or _read_backend_url_from_frontend_env()
API_BASE = f"{BASE_URL}/api"


@pytest.fixture
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestWaitlistAPI:
    """/api/waitlist contract tests."""

    def test_health_root(self, api_client):
        response = api_client.get(f"{API_BASE}/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Project Artemis API online"

    def test_waitlist_create_and_verify_via_get(self, api_client):
        suffix = uuid.uuid4().hex[:10]
        payload = {
            "name": f"TEST_Artemis {suffix}",
            "firm": f"TEST Firm {suffix}",
            "email": f"test.artemis.{suffix}@example.com",
        }

        create_response = api_client.post(f"{API_BASE}/waitlist", json=payload)
        assert create_response.status_code == 201
        created = create_response.json()

        assert created["name"] == payload["name"]
        assert created["firm"] == payload["firm"]
        assert created["email"] == payload["email"]
        assert created["segment"] == "Local wealth / law office sandbox"
        assert created["access_tier"] == "Sandboxed early access"
        assert isinstance(created["id"], str)
        assert len(created["id"]) > 10

        get_response = api_client.get(f"{API_BASE}/waitlist")
        assert get_response.status_code == 200
        entries = get_response.json()
        assert isinstance(entries, list)

        match = [e for e in entries if e["email"] == payload["email"]]
        assert len(match) == 1
        assert match[0]["name"] == payload["name"]
        assert match[0]["firm"] == payload["firm"]

    def test_duplicate_email_rejected_with_useful_error(self, api_client):
        suffix = uuid.uuid4().hex[:10]
        payload = {
            "name": f"TEST_Duplicate {suffix}",
            "firm": f"TEST Duplicate Firm {suffix}",
            "email": f"test.dup.{suffix}@example.com",
        }

        first = api_client.post(f"{API_BASE}/waitlist", json=payload)
        assert first.status_code == 201

        second = api_client.post(f"{API_BASE}/waitlist", json=payload)
        assert second.status_code == 409
        data = second.json()
        assert "detail" in data
        assert "already" in data["detail"].lower()
