"""core/automation/approval.py — Permission and Approval Gates for External Automations."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class ActionRiskLevel(str, Enum):
    READ = "read"                     # Free reading/inspecting
    DRAFT = "draft"                   # Creating drafts, testing workflows
    CONSEQUENTIAL = "consequential"   # Publishing flows, sending real emails/messages
    DESTRUCTIVE = "destructive"       # Deleting workflows or account data (Disabled by default)


def require_approval_for_action(action_name: str, payload: dict[str, Any]) -> tuple[bool, str]:
    """Determines whether an automation operation requires explicit user approval."""
    act = action_name.lower()

    if any(k in act for k in ("delete", "destroy", "drop", "purge")):
        return True, f"Operation '{action_name}' is destructive and disabled by default"

    if any(k in act for k in ("publish", "lock_and_publish", "send_email", "send_whatsapp", "transfer")):
        return True, f"Operation '{action_name}' is consequential and requires your explicit approval"

    # Reading, testing, drafting are allowed
    return False, "Allowed"
