"""DAZY local backend API — v1 routes. Binds 127.0.0.1 by default."""
import json
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import config, db, gateway, services

app = FastAPI(title="DAZY AI OS — Local Backend", version="1.0.0")


@app.on_event("startup")
def startup() -> None:
    applied = db.migrate()
    for name in applied:
        print(f"[dazy] migration applied: {name}")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


@app.get("/api/v1/system")
def system() -> dict[str, Any]:
    return {
        "ok": True,
        "app": "DAZY AI OS",
        "mode": "local-first",
        "db": {"path": str(config.DB_PATH), "exists": config.DB_PATH.exists()},
        "providers_configured": [p["id"] for p in gateway.providers() if p["configured"]],
        "offline_capable": bool(config.LOCAL_LLM_URL),
    }


@app.get("/api/v1/status")
def status(deep: bool = False) -> dict[str, Any]:
    backend_ok = db.one("SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table'") is not None
    return {
        "ok": True,
        "backend": {"state": "healthy" if backend_ok else "unhealthy", "db": str(config.DB_PATH)},
        **gateway.health(deep=deep),
    }


@app.post("/api/v1/chat")
def chat(body: ChatIn) -> dict[str, Any]:
    try:
        return services.send_chat(body.message, body.conversation_id)
    except services.RateLimited as e:
        raise HTTPException(status_code=429, detail={
            "error": "RATE_LIMIT", "detail": f"Bas thoda ruk jao — {e.used} turns in window. Thodi der baad try karo."})
    except gateway.GatewayError as e:
        raise HTTPException(status_code=502, detail={
            "error": "ALL_PROVIDERS_FAILED", "request_id": e.request_id, "attempts": e.attempts})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class MemoryIn(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=500)


@app.get("/api/v1/memory")
def memory_list(q: str = "", limit: int = 50) -> list[dict[str, Any]]:
    return services.list_memories(q, min(limit, 200))


@app.post("/api/v1/memory")
def memory_create(body: MemoryIn) -> dict[str, Any]:
    saved = services.upsert_memory(body.key, body.value, source="manual")
    if not saved:
        raise HTTPException(status_code=400, detail="Rejected: empty or secret-like memory")
    return saved


@app.put("/api/v1/memory/{mid}")
def memory_edit(mid: str, body: MemoryIn) -> dict[str, Any]:
    saved = services.edit_memory(mid, body.value)
    if not saved:
        raise HTTPException(status_code=404, detail="memory not found")
    return saved


@app.delete("/api/v1/memory/{mid}")
def memory_delete(mid: str) -> dict[str, bool]:
    if not services.forget_memory(mid):
        raise HTTPException(status_code=404, detail="memory not found")
    return {"ok": True}


class ReminderIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    due_at: str | None = None
    minutes: int | None = Field(default=None, ge=1, le=1440)


class SnoozeIn(BaseModel):
    minutes: int = Field(default=10, ge=1, le=1440)


@app.get("/api/v1/reminders")
def reminders_list() -> list[dict[str, Any]]:
    return services.list_reminders()


@app.get("/api/v1/reminders/due")
def reminders_due() -> list[dict[str, Any]]:
    return services.due_reminders()


@app.post("/api/v1/reminders")
def reminders_create(body: ReminderIn) -> dict[str, Any]:
    due = body.due_at
    if not due and body.minutes:
        from datetime import datetime, timedelta, timezone as tz
        due = (datetime.now(tz.utc) + timedelta(minutes=body.minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not due:
        raise HTTPException(status_code=400, detail="due_at or minutes required")
    saved = services.create_reminder(body.title, due)
    if not saved:
        raise HTTPException(status_code=400, detail="invalid reminder")
    return saved


@app.put("/api/v1/reminders/{rid}")
def reminders_edit(rid: str, body: ReminderIn) -> dict[str, Any]:
    if body.title:
        saved = services.edit_reminder(rid, body.title)
        if not saved:
            raise HTTPException(status_code=404, detail="reminder not found")
        return saved
    raise HTTPException(status_code=400, detail="nothing to update")


@app.post("/api/v1/reminders/{rid}/complete")
def reminders_complete(rid: str) -> dict[str, bool]:
    if not services.complete_reminder(rid):
        raise HTTPException(status_code=404, detail="reminder not found or already complete")
    return {"ok": True}


@app.post("/api/v1/reminders/{rid}/snooze")
def reminders_snooze(rid: str, body: SnoozeIn) -> dict[str, Any]:
    saved = services.snooze_reminder(rid, body.minutes)
    if not saved:
        raise HTTPException(status_code=404, detail="reminder not found")
    return saved


@app.delete("/api/v1/reminders/{rid}")
def reminders_delete(rid: str) -> dict[str, bool]:
    if not services.delete_reminder(rid):
        raise HTTPException(status_code=404, detail="reminder not found")
    return {"ok": True}


class TaskIn(BaseModel):
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=9)
    idempotency_key: str | None = None
    max_attempts: int = Field(default=3, ge=1, le=10)


@app.post("/api/v1/tasks")
def tasks_enqueue(body: TaskIn) -> dict[str, Any]:
    try:
        return services.enqueue_task(body.kind, body.payload, priority=body.priority,
                                     idempotency_key=body.idempotency_key, max_attempts=body.max_attempts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/tasks")
def tasks_list(status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    return services.list_tasks(status, min(limit, 200))


@app.post("/api/v1/tasks/{tid}/cancel")
def tasks_cancel(tid: str) -> dict[str, bool]:
    if not services.cancel_task(tid):
        raise HTTPException(status_code=404, detail="task not cancellable")
    return {"ok": True}


@app.get("/api/v1/conversations")
def conversations_list(limit: int = 20) -> list[dict[str, Any]]:
    return db.query("SELECT id, title, created_at, last_message_at FROM conversations ORDER BY last_message_at DESC LIMIT ?", (min(limit, 100),))


@app.get("/api/v1/conversations/{cid}/messages")
def conversation_messages(cid: str, limit: int = 80) -> list[dict[str, Any]]:
    return db.query("SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at LIMIT ?", (cid, min(limit, 200)))


@app.get("/api/v1/events")
def events_list(limit: int = 50) -> list[dict[str, Any]]:
    return db.query("SELECT * FROM events ORDER BY id DESC LIMIT ?", (min(limit, 200),))
