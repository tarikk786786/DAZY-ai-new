"""API tests via FastAPI TestClient — routes, error contracts, rate limit."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DAZY_DATA_DIR", tempfile.mkdtemp(prefix="dazy-api-test-"))
for k in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY", "LOCAL_LLM_URL"):
    os.environ.pop(k, None)

from fastapi.testclient import TestClient  # noqa: E402

from backend.api import app  # noqa: E402
from backend import db  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean():
    db.migrate()
    yield
    for t in ("messages", "conversations", "memories", "reminders", "tasks", "provider_attempts", "events"):
        db.execute(f"DELETE FROM {t}")


def test_system_endpoint():
    r = client.get("/api/v1/system")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True and body["mode"] == "local-first"


def test_status_reports_unconfigured_providers_honestly():
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    providers = r.json()["providers"]
    assert len(providers) >= 4
    assert all(p["configured"] is False for p in providers)


def test_chat_honest_502_when_no_providers():
    r = client.post("/api/v1/chat", json={"message": "hi"})
    assert r.status_code == 502
    detail = r.json()["detail"]
    assert detail["error"] == "ALL_PROVIDERS_FAILED"
    assert isinstance(detail["attempts"], list) and detail["attempts"]


def test_chat_validation():
    assert client.post("/api/v1/chat", json={"message": ""}).status_code == 422


def test_memory_crud_flow():
    r = client.post("/api/v1/memory", json={"key": "favourite_food", "value": "biryani"})
    assert r.status_code == 200
    mid = r.json()["id"]
    r = client.put(f"/api/v1/memory/{mid}", json={"key": "favourite_food", "value": "mutton biryani"})
    assert r.status_code == 200 and r.json()["value"] == "mutton biryani"
    r = client.get("/api/v1/memory", params={"q": "biryani"})
    assert len(r.json()) == 1
    assert client.delete(f"/api/v1/memory/{mid}").status_code == 200
    assert client.get("/api/v1/memory").json() == []


def test_memory_rejects_secrets():
    r = client.post("/api/v1/memory", json={"key": "my api key", "value": "sk-123"})
    assert r.status_code == 400


def test_reminder_flow():
    r = client.post("/api/v1/reminders", json={"title": "Call mom", "minutes": 30})
    assert r.status_code == 200
    rid = r.json()["id"]
    assert client.post(f"/api/v1/reminders/{rid}/snooze", json={"minutes": 10}).json()["snoozed_count"] == 1
    assert client.post(f"/api/v1/reminders/{rid}/complete").json()["ok"] is True
    assert client.post(f"/api/v1/reminders/{rid}/complete").status_code == 404
    assert client.get("/api/v1/reminders").json() == []


def test_tasks_unknown_kind():
    assert client.post("/api/v1/tasks", json={"kind": "nope"}).status_code == 400


def test_conversations_endpoints():
    assert client.get("/api/v1/conversations").json() == []
    assert client.get("/api/v1/events").status_code == 200
