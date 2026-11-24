"""Domain services: memory, reminders, chat orchestration, tasks, rate limit."""
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from . import config, db, gateway

IST = timezone(timedelta(hours=5, minutes=30))


def now_iso() -> str:
    return datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S%z")[:-2] + ":30"


# ── Memory ────────────────────────────────────────────────────────────────────

def list_memories(q: str = "", limit: int = 50) -> list[dict[str, Any]]:
    if q.strip():
        return db.query(
            "SELECT m.* FROM memories m JOIN memories_fts f ON m.rowid = f.rowid"
            " WHERE memories_fts MATCH ? ORDER BY m.importance DESC, m.updated_at DESC LIMIT ?",
            (q.strip(), limit),
        )
    return db.query("SELECT * FROM memories ORDER BY importance DESC, updated_at DESC LIMIT ?", (limit,))


def upsert_memory(key: str, value: str, category: str = "fact", source: str = "chat") -> dict[str, Any] | None:
    key, value = key.strip()[:120], value.strip()[:500]
    if not key or not value or gateway.SECRET_RE.search(key + value):
        return None
    existing = db.one("SELECT id FROM memories WHERE lower(key)=lower(?)", (key,))
    mid = (existing or {}).get("id") or str(uuid.uuid4())
    if existing:
        db.execute("UPDATE memories SET value=?, category=?, updated_at=? WHERE id=?", (value, category, now_iso(), mid))
    else:
        db.execute(
            "INSERT INTO memories (id, category, key, value, source, updated_at) VALUES (?,?,?,?,?,?)",
            (mid, category, key, value, source, now_iso()),
        )
    return db.one("SELECT * FROM memories WHERE id=?", (mid,))


def edit_memory(mid: str, value: str) -> dict[str, Any] | None:
    value = value.strip()[:500]
    if not value:
        return None
    db.execute("UPDATE memories SET value=?, updated_at=? WHERE id=?", (value, now_iso(), mid))
    return db.one("SELECT * FROM memories WHERE id=?", (mid,))


def forget_memory(mid: str) -> bool:
    if not db.one("SELECT id FROM memories WHERE id=?", (mid,)):
        return False
    db.execute("DELETE FROM memories WHERE id=?", (mid,))
    return True


# ── Reminders ─────────────────────────────────────────────────────────────────

def list_reminders() -> list[dict[str, Any]]:
    return db.query("SELECT * FROM reminders WHERE completed_at IS NULL ORDER BY due_at LIMIT 50")


def create_reminder(title: str, due_at: str) -> dict[str, Any] | None:
    title = title.strip()[:300]
    if not title or not due_at:
        return None
    rid = str(uuid.uuid4())
    db.execute(
        "INSERT INTO reminders (id, title, due_at) VALUES (?,?,?)",
        (rid, title, due_at),
    )
    return db.one("SELECT * FROM reminders WHERE id=?", (rid,))


def complete_reminder(rid: str) -> bool:
    cur = db.conn().execute("UPDATE reminders SET completed_at=? WHERE id=? AND completed_at IS NULL", (now_iso(), rid))
    db.conn().commit()
    return cur.rowcount > 0


def snooze_reminder(rid: str, minutes: int) -> dict[str, Any] | None:
    r = db.one("SELECT * FROM reminders WHERE id=?", (rid,))
    if not r or r["completed_at"]:
        return None
    base = max(datetime.now(IST), datetime.fromisoformat(r["due_at"]))
    new_due = (base + timedelta(minutes=max(1, min(minutes, 1440)))).strftime("%Y-%m-%dT%H:%M:%S+05:30")
    db.execute("UPDATE reminders SET due_at=?, snoozed_count=snoozed_count+1 WHERE id=?", (new_due, rid))
    return db.one("SELECT * FROM reminders WHERE id=?", (rid,))


def edit_reminder(rid: str, title: str) -> dict[str, Any] | None:
    title = title.strip()[:300]
    if not title:
        return None
    db.execute("UPDATE reminders SET title=? WHERE id=?", (title, rid))
    return db.one("SELECT * FROM reminders WHERE id=?", (rid,))


def delete_reminder(rid: str) -> bool:
    if not db.one("SELECT id FROM reminders WHERE id=?", (rid,)):
        return False
    db.execute("DELETE FROM reminders WHERE id=?", (rid,))
    return True


def due_reminders() -> list[dict[str, Any]]:
    return db.query(
        "SELECT * FROM reminders WHERE completed_at IS NULL AND due_at <= ?",
        (now_iso(),),
    )


# ── Chat ──────────────────────────────────────────────────────────────────────

def rate_limit_ok() -> tuple[bool, int]:
    window_start = datetime.now(timezone.utc) - timedelta(seconds=config.WINDOW_SECS)
    row = db.one("SELECT COUNT(*) AS n FROM events WHERE kind='chat_turn' AND created_at >= ?", (window_start.isoformat(),))
    return (row["n"] or 0) < config.MAX_TURNS, row["n"] or 0


def send_chat(text: str, conversation_id: str | None = None) -> dict[str, Any]:
    text = text.strip()[:4000]
    if not text:
        raise ValueError("empty message")
    allowed, used = rate_limit_ok()
    if not allowed:
        raise RateLimited(used)
    db.execute("INSERT INTO events (kind, payload) VALUES ('chat_turn', ?)", (json.dumps({"n": used + 1}),))

    if conversation_id:
        conv = db.one("SELECT * FROM conversations WHERE id=?", (conversation_id,))
        if not conv:
            raise ValueError("conversation not found")
    else:
        conversation_id = str(uuid.uuid4())
        db.execute("INSERT INTO conversations (id, title) VALUES (?,?)", (conversation_id, text[:40]))

    history_rows = db.query(
        "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY created_at DESC LIMIT 10",
        (conversation_id,),
    )
    history = [{"role": r["role"], "content": r["content"]} for r in reversed(history_rows)]

    db.execute(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?,?,?,?)",
        (str(uuid.uuid4()), conversation_id, "user", text),
    )

    result = gateway.chat(text, history)

    mem = result.get("memory")
    if mem and mem.get("key") and mem.get("value"):
        upsert_memory(mem["key"], str(mem["value"]), source="chat")
        result["memory_saved"] = mem

    rem = result.get("reminder")
    if rem and rem.get("title") and rem.get("due_at"):
        saved = create_reminder(str(rem["title"]), str(rem["due_at"]))
        if saved:
            result["reminder_set"] = {"id": saved["id"], "title": saved["title"], "due_at": saved["due_at"]}

    db.execute(
        "INSERT INTO messages (id, conversation_id, role, content, emotion, provider, model, latency_ms, request_id)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), conversation_id, "assistant", result["response"], result.get("emotion"),
         result.get("provider_used"), result.get("model_used"), result.get("latency_ms"), result.get("request_id")),
    )
    db.execute("UPDATE conversations SET last_message_at=? WHERE id=?", (now_iso(), conversation_id))
    db.execute("INSERT INTO events (kind, payload) VALUES ('chat_done', ?)",
               (json.dumps({"provider": result.get("provider_used"), "latency_ms": result.get("latency_ms")}),))
    result["conversation_id"] = conversation_id
    return result


class RateLimited(Exception):
    def __init__(self, used: int):
        self.used = used
        super().__init__(f"rate limit: {used} turns in window")


# ── Task engine (durable queue) ───────────────────────────────────────────────

TASK_KINDS: dict[str, Any] = {}


def task_handler(kind: str):
    def register(fn):
        TASK_KINDS[kind] = fn
        return fn
    return register


def enqueue_task(kind: str, payload: dict | None = None, *, priority: int = 5,
                 idempotency_key: str | None = None, max_attempts: int = 3) -> dict[str, Any]:
    if kind not in TASK_KINDS:
        raise ValueError(f"unknown task kind: {kind}")
    if idempotency_key:
        existing = db.one("SELECT * FROM tasks WHERE idempotency_key=?", (idempotency_key,))
        if existing:
            return existing
    tid = str(uuid.uuid4())
    db.execute(
        "INSERT INTO tasks (id, kind, payload, priority, idempotency_key, max_attempts) VALUES (?,?,?,?,?,?)",
        (tid, kind, json.dumps(payload or {}), max(1, min(priority, 9)), idempotency_key, max(1, max_attempts)),
    )
    db.execute("INSERT INTO events (kind, payload) VALUES ('task_queued', ?)", (json.dumps({"id": tid, "kind": kind}),))
    return db.one("SELECT * FROM tasks WHERE id=?", (tid,))


def claim_task() -> dict[str, Any] | None:
    c = db.conn()
    with c:
        row = c.execute(
            "SELECT id FROM tasks WHERE status='queued' AND run_after <= ?"
            " ORDER BY priority ASC, created_at ASC LIMIT 1",
            (now_iso(),),
        ).fetchone()
        if not row:
            return None
        cur = c.execute(
            "UPDATE tasks SET status='running', started_at=?, updated_at=? WHERE id=? AND status='queued'",
            (now_iso(), now_iso(), row["id"]),
        )
        if cur.rowcount == 0:
            return None
        return dict(c.execute("SELECT * FROM tasks WHERE id=?", (row["id"],)).fetchone())


def complete_task(tid: str, result: dict | None = None) -> None:
    db.execute(
        "UPDATE tasks SET status='completed', result=?, finished_at=?, updated_at=? WHERE id=?",
        (json.dumps(result or {}), now_iso(), now_iso(), tid),
    )
    db.execute("INSERT INTO events (kind, payload) VALUES ('task_done', ?)", (json.dumps({"id": tid}),))


def fail_task(tid: str, error: str) -> None:
    t = db.one("SELECT * FROM tasks WHERE id=?", (tid,))
    if not t:
        return
    attempts = t["attempts"] + 1
    db.execute("INSERT INTO events (kind, payload) VALUES ('task_attempt_failed', ?)",
               (json.dumps({"id": tid, "attempt": attempts, "error": error[:200]}),))
    if attempts >= t["max_attempts"]:
        db.execute("UPDATE tasks SET status='dead', attempts=?, error=?, finished_at=?, updated_at=? WHERE id=?",
                   (attempts, error[:500], now_iso(), now_iso(), tid))
        db.execute("INSERT INTO events (kind, payload) VALUES ('task_dead', ?)", (json.dumps({"id": tid}),))
        return
    backoff = min(2 ** attempts * 30, 3600)
    run_after = (datetime.now(timezone.utc) + timedelta(seconds=backoff)).strftime("%Y-%m-%dT%H:%M:%SZ")
    db.execute("UPDATE tasks SET status='queued', attempts=?, run_after=?, error=?, updated_at=? WHERE id=?",
               (attempts, run_after, error[:500], now_iso(), tid))


def list_tasks(status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if status:
        return db.query("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC LIMIT ?", (status, limit))
    return db.query("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))


def cancel_task(tid: str) -> bool:
    cur = db.conn().execute(
        "UPDATE tasks SET status='cancelled', finished_at=?, updated_at=? WHERE id=? AND status IN ('queued','waiting_approval')",
        (now_iso(), now_iso(), tid),
    )
    db.conn().commit()
    return cur.rowcount > 0
