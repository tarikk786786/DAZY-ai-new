"""plugins/gmail.py — Direct Lightweight Gmail Plugin."""
from __future__ import annotations

import asyncio

PLUGIN = {
    "name": "gmail_manager",
    "description": "Checks recent unread emails or drafts a reply via Gmail REST API.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "enum": ["check_unread", "create_draft"],
                "description": "Action to perform",
            },
            "to": {
                "type": "STRING",
                "description": "Recipient email address for drafting",
            },
            "subject": {
                "type": "STRING",
                "description": "Email subject",
            },
            "body": {
                "type": "STRING",
                "description": "Draft message content",
            },
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    action = str(parameters.get("action", "check_unread")).lower()
    to = str(parameters.get("to", ""))
    subject = str(parameters.get("subject", ""))
    body = str(parameters.get("body", ""))

    from integrations.google.gmail import GmailIntegration

    gmail = GmailIntegration()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if action == "check_unread":
            messages = loop.run_until_complete(gmail.list_recent_emails(max_results=5))
            if not messages:
                return "Aapke inbox me koi naya unread message nahi mila."
            return f"Aapke paas {len(messages)} unread emails hain."

        elif action == "create_draft":
            if not to or not body:
                return "Draft create karne ke liye 'to' aur 'body' required hain."
            res = loop.run_until_complete(gmail.create_draft(to, subject or "No Subject", body))
            if "id" in res:
                return f"Draft successfully create ho gaya hai: {to} ke liye."
            return f"Draft create nahi ho saka: {res.get('error', 'Unknown error')}"

    except Exception as e:
        return f"Gmail operation error: {e}"
    finally:
        loop.close()

    return "Operation complete."
