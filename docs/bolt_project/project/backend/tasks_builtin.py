"""Built-in task handlers. Import this module to register real worker kinds."""
from . import services, gateway


@services.task_handler("memory_extract")
def memory_extract(payload: dict) -> dict:
    text = str(payload.get("text", "")).strip()
    if not text:
        raise ValueError("text required")
    result = gateway.chat(
        f"Extract up to 3 durable facts about the user from this message. "
        f"Reply STRICT JSON: {{\"memories\": [{{\"key\": ..., \"value\": ...}}]}}\nMessage: {text}"
    )
    saved = []
    mem = result.get("memory")
    if mem and mem.get("key"):
        row = services.upsert_memory(str(mem["key"]), str(mem["value"]), source="worker")
        if row:
            saved.append(row["id"])
    return {"saved": saved, "provider": result.get("provider_used")}


@services.task_handler("summarize")
def summarize(payload: dict) -> dict:
    text = str(payload.get("text", "")).strip()
    if not text:
        raise ValueError("text required")
    result = gateway.chat(f"Summarize in one crisp Hinglish sentence:\n{text[:3000]}")
    return {"summary": result["response"], "provider": result.get("provider_used")}
