"""Tests: DB/migrations, memory, reminders, task engine, gateway failover (mocked HTTP)."""
import json
import os
import sys
import tempfile
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_tmp = tempfile.mkdtemp(prefix="dazy-test-")
os.environ["DAZY_DATA_DIR"] = _tmp
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("OPENROUTER_API_KEY", None)
os.environ.pop("DEEPSEEK_API_KEY", None)
os.environ.pop("LOCAL_LLM_URL", None)

from backend import db, gateway, services  # noqa: E402


@pytest.fixture(autouse=True)
def _migrate():
    db.migrate()
    yield


@pytest.fixture(autouse=True)
def _clear_tables():
    yield
    for t in ("messages", "conversations", "memories", "reminders", "tasks", "provider_attempts", "events", "settings"):
        db.execute(f"DELETE FROM {t}")


# ── DB ───────────────────────────────────────────────────────────────────────

def test_migrations_idempotent():
    applied = db.migrate()
    assert applied == []  # nothing new on second run
    tables = {r["name"] for r in db.query("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"conversations", "messages", "memories", "reminders", "tasks", "provider_attempts", "events"} <= tables


def test_fts_search():
    services.upsert_memory("birthday", "Tarik's birthday is 14 Feb", source="test")
    services.upsert_memory("music", "Likes Arijit Singh", source="test")
    hits = services.list_memories("birthday")
    assert len(hits) == 1 and "14 Feb" in hits[0]["value"]


def test_memory_secret_guard():
    db.execute("DELETE FROM memories")
    assert services.upsert_memory("gemini api key", "sk-abc123") is None
    assert services.list_memories() == []


# ── Reminders ────────────────────────────────────────────────────────────────

def test_reminder_complete_and_snooze():
    r = services.create_reminder("Uthana hai", "2026-11-25T07:00:00+05:30")
    assert r is not None
    s = services.snooze_reminder(r["id"], 10)
    assert s["snoozed_count"] == 1
    assert services.complete_reminder(r["id"]) is True
    assert services.complete_reminder(r["id"]) is False  # double-complete rejected
    assert all(x["id"] != r["id"] for x in services.list_reminders())


def test_reminder_delete():
    r = services.create_reminder("Temp", "2026-11-25T07:00:00+05:30")
    assert services.delete_reminder(r["id"]) is True
    assert services.delete_reminder(r["id"]) is False


# ── Task engine ──────────────────────────────────────────────────────────────

def test_task_lifecycle():
    services.TASK_KINDS["echo"] = lambda p: {"echo": p.get("x")}
    t = services.enqueue_task("echo", {"x": 1}, idempotency_key="echo-1")
    again = services.enqueue_task("echo", {"x": 1}, idempotency_key="echo-1")
    assert t["id"] == again["id"]  # idempotent

    claimed = services.claim_task()
    assert claimed and claimed["id"] == t["id"] and claimed["status"] == "running"
    assert services.claim_task() is None  # no double-claim of same/absent
    services.complete_task(t["id"], {"echo": 1})
    assert services.list_tasks("completed")[0]["id"] == t["id"]


def test_task_retry_and_dead():
    services.TASK_KINDS["boom"] = lambda p: (_ for _ in ()).throw(RuntimeError("planned"))
    t = services.enqueue_task("boom", {}, max_attempts=2)
    services.fail_task(t["id"], "first failure")
    row = services.list_tasks()[0]
    assert row["status"] == "queued" and row["attempts"] == 1  # retry scheduled
    services.fail_task(t["id"], "second failure")
    row = services.list_tasks()[0]
    assert row["status"] == "dead" and row["attempts"] == 2


def test_task_unknown_kind():
    with pytest.raises(ValueError):
        services.enqueue_task("nope", {})


# ── Gateway (mocked HTTP) ────────────────────────────────────────────────────

GEMINI_OK = {"candidates": [{"content": {"parts": [{"text": json.dumps({
    "response": "Sab theek hai!", "emotion": "happy", "speak": "Sab theek hai!",
    "memory": None, "reminder": None})}]}}]}


def test_gateway_all_providers_unconfigured(monkeypatch):
    with pytest.raises(gateway.GatewayError) as e:
        gateway.chat("hello")
    assert e.value.attempts  # honest attempts list, not a fake success


def test_gateway_gemini_success(monkeypatch):
    os.environ["GEMINI_API_KEY"] = "test-key"
    try:
        def fake_post(url, **kwargs):
            resp = httpx.Response(200, json=GEMINI_OK, request=httpx.Request("POST", url))
            return resp
        class FakeClient:
            def __init__(self, *a, **k): pass
            def __enter__(self): return self
            def __exit__(self, *a): return None
            def post(self, url, **kw): return fake_post(url, **kw)
        monkeypatch.setattr(gateway.httpx, "Client", FakeClient)
        result = gateway.chat("hello")
        assert result["provider_used"] == "gemini"
        assert result["fallback_used"] is False
        assert result["response"] == "Sab theek hai!"
        rows = db.query("SELECT * FROM provider_attempts WHERE outcome='ok'")
        assert len(rows) == 1 and rows[0]["provider"] == "gemini"
    finally:
        os.environ.pop("GEMINI_API_KEY", None)


def test_gateway_failover_to_groq(monkeypatch):
    os.environ["GEMINI_API_KEY"] = "test-key"
    os.environ["GROQ_API_KEY"] = "test-key"
    try:
        calls = []
        class FakeClient:
            def __init__(self, *a, **k): pass
            def __enter__(self): return self
            def __exit__(self, *a): return None
            def post(self, url, **kw):
                calls.append(url)
                if "gemini" in url or "googleapis" in url:
                    return httpx.Response(429, json={}, request=httpx.Request("POST", url))
                return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
                    "response": "Groq here", "emotion": "neutral", "speak": "Groq here",
                    "memory": None, "reminder": None})}}]}, request=httpx.Request("POST", url))
        monkeypatch.setattr(gateway.httpx, "Client", FakeClient)
        result = gateway.chat("hello")
        assert result["provider_used"] == "groq"
        assert result["fallback_used"] is True
        outcomes = [(a["provider"], a["outcome"]) for a in db.query(
            "SELECT provider, outcome FROM provider_attempts ORDER BY id")]
        assert ("gemini", "rate_limited") in outcomes and ("groq", "ok") in outcomes
    finally:
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GROQ_API_KEY", None)


def test_gateway_auth_skips_retries(monkeypatch):
    os.environ["GEMINI_API_KEY"] = "bad-key"
    try:
        class FakeClient:
            def __init__(self, *a, **k): pass
            def __enter__(self): return self
            def __exit__(self, *a): return None
            def post(self, url, **kw):
                return httpx.Response(401, json={}, request=httpx.Request("POST", url))
        monkeypatch.setattr(gateway.httpx, "Client", FakeClient)
        with pytest.raises(gateway.GatewayError) as e:
            gateway.chat("hello")
        gemini_attempts = [a for a in e.value.attempts if a["provider"] == "gemini"]
        assert len(gemini_attempts) == 1  # auth failure skips remaining retries
        assert gemini_attempts[0]["outcome"] == "auth"
    finally:
        os.environ.pop("GEMINI_API_KEY", None)


def test_health_reports_real_state(monkeypatch):
    report = gateway.health(deep=False)
    ids = {p["id"]: p for p in report["providers"]}
    assert set(ids) >= {"gemini", "groq", "openrouter", "deepseek"}
    assert all(not p["configured"] for p in report["providers"])  # env cleared
    assert ids["gemini"]["stats_24h"]["total"] == 0


# ── Rate limit ───────────────────────────────────────────────────────────────

def test_rate_limit_blocks(monkeypatch):
    from backend import config as cfg
    original = cfg.MAX_TURNS
    cfg.MAX_TURNS = 2
    try:
        assert services.rate_limit_ok()[0] is True
        db.execute("INSERT INTO events (kind, payload) VALUES ('chat_turn','{}')")
        db.execute("INSERT INTO events (kind, payload) VALUES ('chat_turn','{}')")
        assert services.rate_limit_ok()[0] is False
    finally:
        cfg.MAX_TURNS = original
