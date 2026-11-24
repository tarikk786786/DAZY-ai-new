"""Multi-brain model gateway.

Provider ladder mirrors the verified edge-function implementation:
Gemini -> Groq -> OpenRouter -> DeepSeek -> optional local OpenAI-compatible.
Every attempt is logged to provider_attempts. Responses always carry
provider_used / model_used / latency_ms / fallback_used — never silently pretend.
"""
import json
import time
import uuid
from typing import Any

import httpx

from . import config, db

MAX_ATTEMPTS_PER_PROVIDER = 2
TIMEOUT_SECS = 30

PERSONA = (
    "You are DAZY — Tarik's AI companion, warm, witty, speaks Hinglish by default. "
    "Reply with STRICT JSON only: "
    '{"response": string, "emotion": "neutral|affection|happy|playful|empathetic|curious|excited|sad|serious|confident", '
    '"speak": string (spoken version, short), '
    '"memory": {"key": string, "value": string} | null (save important user facts, never API keys/passwords/tokens), '
    '"reminder": {"title": string, "due_at": "YYYY-MM-DDTHH:MM:SS+05:30"} | null (IST). '
    "No markdown, no text outside JSON."
)


class ProviderError(Exception):
    def __init__(self, outcome: str, detail: str = ""):
        self.outcome = outcome
        self.detail = detail
        super().__init__(f"{outcome}: {detail}")


def providers() -> list[dict[str, Any]]:
    ladder: list[dict[str, Any]] = [
        {"id": "gemini", "role": "primary", "env_key": "GEMINI_API_KEY", "model": config.GEMINI_MODEL},
        {"id": "groq", "role": "fallback", "env_key": "GROQ_API_KEY", "model": config.GROQ_MODEL},
        {"id": "openrouter", "role": "fallback", "env_key": "OPENROUTER_API_KEY", "model": config.OPENROUTER_MODEL},
        {"id": "deepseek", "role": "fallback", "env_key": "DEEPSEEK_API_KEY", "model": config.DEEPSEEK_MODEL},
    ]
    if config.LOCAL_LLM_URL:
        ladder.append({"id": "local", "role": "offline", "env_key": None, "model": config.LOCAL_LLM_MODEL})
    for p in ladder:
        key = config.env(p["env_key"]) if p["env_key"] else "present"
        p["configured"] = bool(key)
        p["state"] = "unknown"
    return ladder


def _classify(status: int) -> str:
    if status in (401, 403):
        return "auth"
    if status == 404:
        return "not_found"
    if status == 402:
        return "payment"
    if status == 429:
        return "rate_limited"
    if 500 <= status < 600:
        return "server"
    return "http"


def _log_attempt(request_id: str, provider: str, model: str, outcome: str, ms: int, detail: str = "") -> None:
    db.execute(
        "INSERT INTO provider_attempts (request_id, provider, model, outcome, latency_ms, detail) VALUES (?,?,?,?,?,?)",
        (request_id, provider, model, outcome, ms, detail[:300]),
    )
    events = db.query("SELECT 1 FROM events LIMIT 1")
    if events is not None:
        db.execute(
            "INSERT INTO events (kind, payload) VALUES (?,?)",
            ("provider_attempt", json.dumps({"request_id": request_id, "provider": provider, "outcome": outcome, "latency_ms": ms})),
        )


def _call_gemini(model: str, prompt: str, key: str) -> str:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.85, "maxOutputTokens": 1024, "responseMimeType": "application/json"},
    }
    with httpx.Client(timeout=TIMEOUT_SECS) as client:
        resp = client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json=body,
        )
    if resp.status_code != 200:
        raise ProviderError(_classify(resp.status_code), f"http {resp.status_code}")
    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as e:
        raise ProviderError("malformed", f"missing candidates text: {e}") from e
    if not text.strip():
        raise ProviderError("empty", "no text")
    return text


def _call_openai_compatible(base_url: str, model: str, prompt: str, key: str, provider: str) -> str:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    with httpx.Client(timeout=TIMEOUT_SECS) as client:
        resp = client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024},
        )
    if resp.status_code != 200:
        raise ProviderError(_classify(resp.status_code), f"http {resp.status_code}")
    try:
        text = resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ProviderError("malformed", f"bad choices shape: {e}") from e
    if not text.strip():
        raise ProviderError("empty", "no text")
    return text


def _call_provider(pid: str, model: str, prompt: str, key: str) -> str:
    if pid == "gemini":
        return _call_gemini(model, prompt, key)
    if pid == "groq":
        return _call_openai_compatible("https://api.groq.com/openai/v1", model, prompt, key, pid)
    if pid == "openrouter":
        return _call_openai_compatible("https://openrouter.ai/api/v1", model, prompt, key, pid)
    if pid == "deepseek":
        return _call_openai_compatible("https://api.deepseek.com/v1", model, prompt, key, pid)
    if pid == "local":
        base = config.LOCAL_LLM_URL.rstrip("/")
        if not base.endswith("/v1"):
            base = base + "/v1"
        return _call_openai_compatible(base, model, prompt, "", pid)
    raise ProviderError("not_found", f"unknown provider {pid}")


def parse_reply(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"response": raw, "emotion": "neutral", "speak": raw, "memory": None, "reminder": None}
    if not isinstance(data, dict) or not isinstance(data.get("response"), str):
        return {"response": raw, "emotion": "neutral", "speak": raw, "memory": None, "reminder": None}
    return {
        "response": data["response"],
        "emotion": data.get("emotion", "neutral"),
        "speak": data.get("speak") or data["response"],
        "memory": data.get("memory") if isinstance(data.get("memory"), dict) else None,
        "reminder": data.get("reminder") if isinstance(data.get("reminder"), dict) else None,
    }


SECRET_RE = __import__("re").compile(r"api[\s_-]?key|password|passphrase|token|secret|credential", __import__("re").IGNORECASE)


def chat(user_text: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Walk the ladder. Returns the reply plus honest metadata; raises GatewayError if all fail."""
    request_id = str(uuid.uuid4())
    context = ""
    for m in (history or [])[-10:]:
        context += f"{m.get('role', 'user')}: {m.get('content', '')}\n"
    prompt = f"{PERSONA}\n\nConversation so far:\n{context}\nUser: {user_text}\n\nJSON only:"

    attempts: list[dict[str, str]] = []
    ladder = providers()
    for idx, p in enumerate(ladder):
        if not p["configured"]:
            attempts.append({"provider": p["id"], "outcome": "skipped", "detail": "not configured"})
            continue
        key = config.env(p["env_key"]) if p["env_key"] else ""
        for attempt in range(MAX_ATTEMPTS_PER_PROVIDER):
            start = time.monotonic()
            try:
                raw = _call_provider(p["id"], p["model"], prompt, key)
                ms = int((time.monotonic() - start) * 1000)
                _log_attempt(request_id, p["id"], p["model"], "ok", ms)
                reply = parse_reply(raw)
                mem = reply.get("memory")
                if mem and SECRET_RE.search(str(mem.get("key", ""))):
                    reply["memory"] = None
                return {
                    **reply,
                    "provider_used": p["id"],
                    "model_used": p["model"],
                    "fallback_used": idx > 0,
                    "latency_ms": ms,
                    "request_id": request_id,
                    "attempts": attempts,
                }
            except ProviderError as e:
                ms = int((time.monotonic() - start) * 1000)
                _log_attempt(request_id, p["id"], p["model"], e.outcome, ms, e.detail)
                attempts.append({"provider": p["id"], "outcome": e.outcome, "detail": e.detail})
                if e.outcome in ("auth", "not_found", "payment"):
                    break
                time.sleep(min(2**attempt * 0.4, 3.0))
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                ms = int((time.monotonic() - start) * 1000)
                detail = "timeout" if isinstance(e, httpx.TimeoutException) else "network error"
                _log_attempt(request_id, p["id"], p["model"], "network", ms, detail)
                attempts.append({"provider": p["id"], "outcome": "network", "detail": detail})
                time.sleep(min(2**attempt * 0.4, 3.0))

    raise GatewayError(request_id, attempts)


class GatewayError(Exception):
    def __init__(self, request_id: str, attempts: list[dict[str, str]]):
        self.request_id = request_id
        self.attempts = attempts
        super().__init__("ALL_PROVIDERS_FAILED")


def health(deep: bool = False) -> dict[str, Any]:
    """Cheap mode: configured + last-24h stats from provider_attempts. Deep: real 5-token ping."""
    rows = db.query(
        "SELECT provider, COUNT(*) AS total, SUM(CASE WHEN outcome='ok' THEN 1 ELSE 0 END) AS ok,"
        " SUM(CASE WHEN outcome='rate_limited' THEN 1 ELSE 0 END) AS rl,"
        " AVG(CASE WHEN outcome='ok' THEN latency_ms END) AS avg_ok"
        " FROM provider_attempts WHERE created_at >= datetime('now','-1 day') GROUP BY provider"
    )
    stats = {r["provider"]: r for r in rows}
    out = []
    for p in providers():
        s = stats.get(p["id"], {})
        entry = {
            "id": p["id"],
            "configured": p["configured"],
            "state": "unknown",
            "model": p["model"],
            "latency_ms": 0,
            "detail": "",
            "role": p["role"],
            "stats_24h": {
                "total": s.get("total", 0) or 0,
                "ok": s.get("ok", 0) or 0,
                "rate_limited": s.get("rl", 0) or 0,
                "avg_ok_latency_ms": int(s.get("avg_ok") or 0),
            },
        }
        if deep and p["configured"]:
            start = time.monotonic()
            try:
                key = config.env(p["env_key"]) if p["env_key"] else ""
                _call_provider(p["id"], p["model"], "ping. reply: ok", key)
                entry["state"] = "healthy"
                entry["latency_ms"] = int((time.monotonic() - start) * 1000)
                entry["detail"] = "ok"
            except ProviderError as e:
                entry["state"] = "unhealthy"
                entry["latency_ms"] = int((time.monotonic() - start) * 1000)
                entry["detail"] = e.detail or e.outcome
        out.append(entry)
    return {"providers": out, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
