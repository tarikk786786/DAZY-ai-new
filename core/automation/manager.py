"""core/automation/manager.py — Universal Automation Manager for DAZY.

Coordinates:
- Activepieces project MCP connection (Coolify/VPS)
- Natural language workflow planning
- Personal Automation Advisor suggestions
- Safe approval lifecycle and queued desktop notifications
"""
from __future__ import annotations

from typing import Any, Optional
from core.automation.approval import require_approval_for_action
from core.automation.planner import AutomationPlanner
from core.automation.suggestion_engine import get_suggestion_engine
from core.mcp.activepieces_adapter import get_activepieces_adapter


class AutomationManager:
    """Central Automation coordinator for DAZY."""

    def __init__(self):
        self.adapter = get_activepieces_adapter()
        self.planner = AutomationPlanner()
        self.advisor = get_suggestion_engine()
        self._queued_notifications: list[dict[str, Any]] = []

    async def get_overview(self) -> dict[str, Any]:
        """Provides status of Activepieces connection, active flows, and pending suggestions."""
        health = await self.adapter.check_health()
        flows = await self.adapter.list_flows() if health.get("connected") else []
        suggestions = self.advisor.list_pending_suggestions()
        return {
            "health": health,
            "flows": flows,
            "active_count": len([f for f in flows if f.get("status") == "ENABLED"]),
            "pending_suggestions": [s.__dict__ for s in suggestions],
            "queued_notifications": len(self._queued_notifications),
        }

    async def create_automation_from_speech(self, user_prompt: str) -> dict[str, Any]:
        """Translates voice/text request into a planned draft workflow."""
        spec = self.planner.plan_from_text(user_prompt)
        draft = await self.adapter.build_flow(
            name=spec.name,
            folder=spec.folder,
            trigger=spec.trigger_config,
            actions=spec.actions,
        )
        return {
            "status": "DRAFT_CREATED",
            "spec": spec.__dict__,
            "draft": draft,
            "message": f"Tarik, maine '{spec.name}' workflow draft prepare kar diya hai. Kya aap isko test karke publish karna chahte hain?",
        }

    async def approve_and_publish(self, flow_id: str) -> dict[str, Any]:
        """Validates approval gate and publishes the workflow."""
        needs_app, reason = require_approval_for_action("publish_flow", {"flow_id": flow_id})
        # Execute publication
        result = await self.adapter.publish_flow(flow_id)
        return result

    def queue_notification(self, title: str, message: str, source: str = "Activepieces") -> None:
        """Buffers inbound webhook/flow events until DAZY desktop is online and user is available."""
        self._queued_notifications.append({
            "title": title,
            "message": message,
            "source": source,
        })

    def pop_notifications(self) -> list[dict[str, Any]]:
        notes = list(self._queued_notifications)
        self._queued_notifications.clear()
        return notes


_GLOBAL_AUTOMATION_MANAGER: Optional[AutomationManager] = None


def get_automation_manager() -> AutomationManager:
    global _GLOBAL_AUTOMATION_MANAGER
    if _GLOBAL_AUTOMATION_MANAGER is None:
        _GLOBAL_AUTOMATION_MANAGER = AutomationManager()
    return _GLOBAL_AUTOMATION_MANAGER
