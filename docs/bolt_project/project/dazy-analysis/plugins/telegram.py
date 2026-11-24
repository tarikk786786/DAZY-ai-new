"""plugins/telegram.py — Direct Lightweight Telegram Notification Tool."""
from __future__ import annotations

import asyncio

PLUGIN = {
    "name": "telegram_messenger",
    "description": "Sends instant alerts or updates to a user's Telegram chat.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "chat_id": {
                "type": "STRING",
                "description": "Target Telegram Chat ID (defaults to saved user chat)",
            },
            "message": {
                "type": "STRING",
                "description": "Notification or message text to send",
            },
        },
        "required": ["message"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    message = str(parameters.get("message", "")).strip()
    chat_id = str(parameters.get("chat_id", "")).strip()

    if not message:
        return "Message empty hai."

    from integrations.communication.telegram import TelegramIntegration
    from integrations.credential_manager import get_credential_manager

    tg = TelegramIntegration()
    if not chat_id:
        chat_id = get_credential_manager().get_secret("telegram", "default_chat_id") or ""

    if not chat_id:
        return "Telegram Chat ID configured nahi hai."

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        res = loop.run_until_complete(tg.send_message(chat_id, message))
        if res.get("ok"):
            return "Telegram message successfully send ho gaya."
        return f"Telegram send failed: {res.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Telegram error: {e}"
    finally:
        loop.close()
