"""Atlas tests — no live network. GitHub calls are mocked at httpx.Client level."""
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

os.environ.setdefault("ATLAS_DATA_DIR", tempfile.mkdtemp(prefix="atlas-test-"))

from atlas import config, db, github_verify  # noqa: E402
from atlas.api import app  # noqa: E402


@pytest.fixture()
def fresh_db():
    old = config.DB_PATH
    with tempfile.TemporaryDirectory(prefix="atlas-fixture-") as d:
        config.DB_PATH = Path(d) / "atlas.db"
        if hasattr(db._local, "conn"):
            db._local.conn = None  # drop cached connection bound to the old path
        db.migrate()
        yield config.DB_PATH
        if hasattr(db._local, "conn"):
            db._local.conn = None
    config.DB_PATH = old


@pytest.fixture()
def no_http(monkeypatch):
    """Block any accidental live network call in tests."""
    def boom(*a, **k):
        raise AssertionError("live network call attempted in test")
    monkeypatch.setattr(httpx.Client, "get", boom)
    monkeypatch.setattr(httpx.Client, "post", boom)


def _mock_github(monkeypatch, status=200, licence="Apache-2.0", pushed_at=None, archived=False):
    def fake_get(self, url, **kwargs):
        if url.endswith("/license") and status == 200:
            return httpx.Response(200, json={"license": {"spdx_id": licence}, "name": "LICENSE"}, headers={})
        if status == 200:
            payload = {
                "full_name": "example/repo", "stargazers_count": 12,
                "pushed_at": pushed_at or datetime.now(timezone.utc).isoformat(),
                "archived": archived, "license": None, "description": "d",
            }
            return httpx.Response(200, json=payload, headers={"x-ratelimit-remaining": "55"})
        return httpx.Response(status, json={"message": "err"}, headers={})
    monkeypatch.setattr(httpx.Client, "get", fake_get)


def test_migrations_idempotent(fresh_db, no_http):
    db.migrate()
    db.migrate()
    from atlas.seed import seed
    seed()
    assert db.one("SELECT COUNT(*) AS n FROM categories")["n"] > 0


def _cat(cid: str = "01-ai-brains") -> None:
    db.execute("INSERT INTO categories (id, name, description) VALUES (?, 'T', 't') ON CONFLICT(id) DO NOTHING", (cid,))


def _add(name, cap, cat, url, **kw):
    _cat(cat)
    return github_verify.add_entry(name, cap, cat, url, **kw)


def test_add_entry_idempotent(fresh_db, no_http):
    _add("LiteLLM", "gateway", "01-ai-brains", "https://github.com/BerriAI/litellm", entry_type="library")
    row = github_verify.add_entry("LiteLLM", "gateway", "01-ai-brains", "https://github.com/BerriAI/litellm", entry_type="library")
    assert row["id"] == "litellm"
    assert db.one("SELECT COUNT(*) AS n FROM entries")["n"] == 1


def test_unverified_entry_is_unknown(fresh_db, no_http):
    _add("X", "test", "01-ai-brains", "https://github.com/u/r", entry_type="library")
    row = db.one("SELECT * FROM entries WHERE id='x'")
    assert row["licence"] == "unknown"
    assert row["cost_class"] == "unknown"
    assert row["maintenance"] == "unknown"
    assert row["verified_at"] is None


def test_parse_repo(fresh_db, no_http):
    assert github_verify.parse_repo("https://github.com/BerriAI/litellm") == ("BerriAI", "litellm")
    assert github_verify.parse_repo("https://github.com/u/r.git") == ("u", "r")
    assert github_verify.parse_repo("https://gitlab.com/u/r") is None


def test_verify_entry_success(fresh_db, monkeypatch):
    _add("OkRepo", "test", "01-ai-brains", "https://github.com/example/okrepo", entry_type="library")
    _mock_github(monkeypatch, status=200, licence="Apache-2.0",
                 pushed_at=datetime.now(timezone.utc).isoformat())
    res = github_verify.verify_entry("okrepo")
    assert res["last_verified_status"] == 200
    assert res["licence"] == "Apache-2.0"
    assert res["maintenance"] == "active"
    row = db.one("SELECT * FROM entries WHERE id='okrepo'")
    assert row["verified_at"] is not None
    assert json.loads(row["verified_evidence"])["api_status"] == 200


def test_verify_entry_failure_writes_unknown_evidence(fresh_db, monkeypatch):
    _add("DeadRepo", "tts", "04-voice", "https://github.com/example/deadrepo", entry_type="model")
    _mock_github(monkeypatch, status=404)
    res = github_verify.verify_entry("deadrepo")
    assert res["last_verified_status"] == 404
    row = db.one("SELECT * FROM entries WHERE id='deadrepo'")
    assert row["licence"] == "unknown"
    assert row["verified_at"] is None
    assert json.loads(row["verified_evidence"])["api_status"] == 404


def test_verify_entry_unparseable_url(fresh_db, no_http):
    _add("BadUrl", "x", "01-ai-brains", "https://gitlab.com/a/b", entry_type="library")
    res = github_verify.verify_entry("badurl")
    assert res["last_verified_status"] == 0
    assert json.loads(res["verified_evidence"])["error"] == "unparseable repo url"


def test_verify_all_respects_limit(fresh_db, monkeypatch):
    for i in range(4):
        _add(f"R{i}", "x", "01-ai-brains", f"https://github.com/example/r{i}", entry_type="library")
    _mock_github(monkeypatch, status=404)
    res = github_verify.verify_all(limit=2)
    assert res["failed"] == 2
    assert res["verified"] == 0


def test_verify_all_stops_on_rate_limit(fresh_db, monkeypatch):
    _add("RL", "x", "01-ai-brains", "https://github.com/a/rl", entry_type="library")
    def fake_get(self, url, **kwargs):
        return httpx.Response(403, json={"message": "API rate limit exceeded"},
                              headers={"x-ratelimit-remaining": "0"})
    monkeypatch.setattr(httpx.Client, "get", fake_get)
    res = github_verify.verify_all(limit=5)
    assert res["failed"] == 1  # broke after the first 403
    assert res["verified"] == 0


def test_verify_caches_within_ttl(fresh_db, monkeypatch):
    _add("CacheMe", "x", "01-ai-brains", "https://github.com/a/c", entry_type="library")
    calls = []
    def fake_get(self, url, **kwargs):
        calls.append(url)
        if url.endswith("/license"):
            return httpx.Response(200, json={"license": {"spdx_id": "MIT"}, "name": "LICENSE"}, headers={})
        return httpx.Response(200, json={"full_name": "a/c", "stargazers_count": 1,
                                         "pushed_at": datetime.now(timezone.utc).isoformat(),
                                         "archived": False, "license": None}, headers={})
    monkeypatch.setattr(httpx.Client, "get", fake_get)
    github_verify.verify_entry("cacheme")
    n = len(calls)
    github_verify.verify_entry("cacheme")  # within TTL, no new calls
    assert len(calls) == n


def test_seed_idempotent(fresh_db, no_http):
    from atlas.seed import seed
    seed()
    total = db.one("SELECT COUNT(*) AS n FROM entries")["n"]
    assert total >= 50
    seed()
    assert db.one("SELECT COUNT(*) AS n FROM entries")["n"] == total


def test_classify_from_synthetic_evidence(fresh_db, no_http):
    fresh = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old = (datetime.now(timezone.utc) - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
    active = github_verify._classify({"api_status": 200, "pushed_at": fresh, "archived": False, "licence_spdx": "MIT"})
    assert active["maintenance"] == "active" and active["licence"] == "MIT"
    stale = github_verify._classify({"api_status": 200, "pushed_at": old, "archived": False, "licence_spdx": "MIT"})
    assert stale["maintenance"] == "stale"
    arch = github_verify._classify({"api_status": 200, "pushed_at": fresh, "archived": True, "licence_spdx": "MIT"})
    assert arch["maintenance"] == "archived"
    assert github_verify._classify({"api_status": 404}) is None


# ---- API ----

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client(fresh_db):
    return TestClient(app)


def test_api_entries_and_filters(client):
    _add("FilterMe", "unique-cap", "01-ai-brains", "https://github.com/x/f", entry_type="library")
    r = client.get("/api/v1/entries", params={"q": "unique-cap"})
    assert r.status_code == 200
    assert any(e["name"] == "FilterMe" for e in r.json())
    r2 = client.get("/api/v1/entries", params={"verified": "false"})
    assert any(e["name"] == "FilterMe" for e in r2.json())
    bad = client.get("/api/v1/entries", params={"cost": "bogus"})
    assert bad.status_code == 400


def test_api_entry_404(client):
    assert client.get("/api/v1/entries/nope-nope").status_code == 404


def test_api_stats(client):
    _add("S1", "s", "01-ai-brains", "https://github.com/a/s1", entry_type="library")
    s = client.get("/api/v1/stats").json()
    assert s["total_entries"] >= 1
    assert s["verified"] == 0


def test_api_verify_all_mocked(client, monkeypatch):
    def fake_fetch(repo_url):
        return {"repo_url": repo_url, "checked_at": "now", "api_status": 404, "error": "http 404"}
    monkeypatch.setattr(github_verify, "_fetch", fake_fetch)
    r = client.post("/api/v1/verify-all", params={"limit": 3})
    assert r.status_code == 200
    assert "failed" in r.json()
