"""GitHub verification engine.

Live REST checks against the real GitHub API. Every field written here is backed
by actual HTTP evidence; failures and unknowns are recorded, never guessed.
Respects rate limits, caches by repo, supports incremental re-verification.
"""
import base64
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from . import config, db

_CACHE_TTL = timedelta(days=7)


def _headers() -> dict[str, str]:
    h = {"User-Agent": config.USER_AGENT, "Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return h


def parse_repo(url: str) -> tuple[str, str] | None:
    url = url.strip().rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/", "https://www.github.com/"):
        if url.startswith(prefix):
            parts = url[len(prefix):].split("/")
            if len(parts) >= 2 and parts[0] and parts[1]:
                return parts[0], parts[1].removesuffix(".git")
    return None


def _fetch(repo_url: str) -> dict[str, Any]:
    """One real API round-trip: repo metadata + licence file. Returns raw evidence."""
    parsed = parse_repo(repo_url)
    evidence: dict[str, Any] = {"repo_url": repo_url, "checked_at": _now(), "api_status": None}
    if not parsed:
        evidence["api_status"] = 0
        evidence["error"] = "unparseable repo url"
        return evidence
    owner, name = parsed
    with httpx.Client(base_url=config.GITHUB_API, headers=_headers(), timeout=15, follow_redirects=True) as client:
        resp = client.get(f"/repos/{owner}/{name}")
        evidence["api_status"] = resp.status_code
        if resp.status_code == 403 and resp.headers.get("x-ratelimit-remaining") == "0":
            evidence["error"] = "rate_limited"
            return evidence
        if resp.status_code != 200:
            evidence["error"] = f"http {resp.status_code}"
            return evidence
        data = resp.json()
        evidence.update({
            "full_name": data.get("full_name"),
            "archived": bool(data.get("archived")),
            "pushed_at": data.get("pushed_at"),
            "stars": data.get("stargazers_count"),
            "licence_spdx": (data.get("license") or {}).get("spdx_id"),
            "description": data.get("description") or "",
        })

        lic = client.get(f"/repos/{owner}/{name}/license")
        evidence["license_api_status"] = lic.status_code
        if lic.status_code == 200:
            payload = lic.json()
            evidence["licence_spdx"] = (payload.get("license") or {}).get("spdx_id") or evidence["licence_spdx"]
            evidence["licence_file"] = payload.get("name")
    return evidence


def _classify(evidence: dict[str, Any]) -> dict[str, str] | None:
    """Map raw evidence to registry fields. Returns None when verification failed."""
    if evidence.get("api_status") != 200:
        return None
    spdx = evidence.get("licence_spdx") or "unknown"
    if spdx == "NOASSERTION":
        spdx = "custom (NOASSERTION)"
    pushed = evidence.get("pushed_at")
    maintenance = "unknown"
    if pushed:
        try:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            maintenance = "active" if age < timedelta(days=180) else "stale"
        except ValueError:
            pass
    if evidence.get("archived"):
        maintenance = "archived"
    return {
        "licence": spdx,
        "maintenance": maintenance,
        "cost_class": "oss",  # repo is public code; API/model cost is a separate per-entry judgement
        "runtime": "unknown",
        "platform": "unknown",
    }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verify_entry(entry_id: str, force: bool = False) -> dict[str, Any]:
    """Verify one entry against live GitHub. Writes evidence + result, returns the row."""
    entry = db.one("SELECT * FROM entries WHERE id=?", (entry_id,))
    if not entry:
        raise ValueError(f"entry not found: {entry_id}")
    if not force and entry["verified_at"]:
        checked = datetime.fromisoformat(entry["verified_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - checked < _CACHE_TTL:
            return entry

    evidence = _fetch(entry["repo_url"])
    fields = _classify(evidence)
    if fields is None:
        db.execute(
            "UPDATE entries SET last_verified_status=?, verified_evidence=?, updated_at=? WHERE id=?",
            (evidence.get("api_status", 0), json.dumps(evidence), _now(), entry_id),
        )
        return db.one("SELECT * FROM entries WHERE id=?", (entry_id,))

    db.execute(
        """UPDATE entries SET
            licence=?, maintenance=?, cost_class=?, runtime=?, platform=?,
            verified_at=?, verified_evidence=?, stars=?, last_commit=?,
            archived=?, last_verified_status=?, updated_at=?
        WHERE id=?""",
        (fields["licence"], fields["maintenance"], fields["cost_class"], fields["runtime"], fields["platform"],
         _now(), json.dumps(evidence), evidence.get("stars"), evidence.get("pushed_at"),
         1 if evidence.get("archived") else 0, 200, _now(), entry_id),
    )
    return db.one("SELECT * FROM entries WHERE id=?", (entry_id,))


def verify_all(limit: int = 25, only_stale: bool = True) -> dict[str, int]:
    """Verify up to `limit` entries per run. Rate-limit aware, incremental by default."""
    if only_stale:
        rows = db.query(
            "SELECT id FROM entries WHERE verified_at IS NULL OR verified_at < ? ORDER BY verified_at NULLS FIRST LIMIT ?",
            ((datetime.now(timezone.utc) - _CACHE_TTL).strftime("%Y-%m-%dT%H:%M:%SZ"), limit),
        )
    else:
        rows = db.query("SELECT id FROM entries ORDER BY name LIMIT ?", (limit,))
    counts = {"verified": 0, "failed": 0}
    for r in rows:
        row = verify_entry(r["id"])
        status = row.get("last_verified_status")
        if status == 200:
            counts["verified"] += 1
        else:
            counts["failed"] += 1
        if status == 403:
            break  # out of API quota; stop instead of hammering
        time.sleep(0.5)  # polite pacing without a token (60 req/hr unauthenticated)
    return counts


def add_entry(name: str, capability: str, category_id: str, repo_url: str, *,
              entry_type: str = "library", description: str = "", subcapability: str = "",
              docs_url: str = "", languages: str = "") -> dict[str, Any]:
    eid = f"{name.lower().replace(' ', '-')}"
    existing = db.one("SELECT id FROM entries WHERE id=?", (eid,))
    if existing:
        return db.one("SELECT * FROM entries WHERE id=?", (eid,))
    db.execute(
        """INSERT INTO entries (id, name, capability, subcapability, category_id, repo_url,
             docs_url, entry_type, description, languages)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (eid, name, capability, subcapability, category_id, repo_url, docs_url, entry_type, description, languages),
    )
    return db.one("SELECT * FROM entries WHERE id=?", (eid,))
