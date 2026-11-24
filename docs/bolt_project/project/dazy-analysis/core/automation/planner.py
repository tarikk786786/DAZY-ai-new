"""core/automation/planner.py — Converts Natural Language requests into Workflow Specifications."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowSpec:
    name: str
    folder: str
    trigger_type: str             # "schedule" | "webhook" | "app_event"
    trigger_config: dict[str, Any] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)
    requires_approval: bool = True
    summary: str = ""


class AutomationPlanner:
    """Translates user natural language into structured Activepieces flows."""

    def plan_from_text(self, text: str) -> WorkflowSpec:
        clean = text.lower()

        # 1. Morning briefing
        if "morning briefing" in clean or "subah briefing" in clean or "daily briefing" in clean:
            return WorkflowSpec(
                name="DAZY Morning Briefing",
                folder="Personal",
                trigger_type="schedule",
                trigger_config={"cron": "0 7 * * *", "timezone": "Asia/Kolkata"},
                actions=[
                    {"piece": "gmail", "action": "find_unread_emails", "limit": 5},
                    {"piece": "google_calendar", "action": "list_today_events"},
                    {"piece": "open_meteo", "action": "get_weather_forecast"},
                    {"piece": "dazy_relay", "action": "deliver_spoken_briefing"},
                ],
                requires_approval=True,
                summary="Runs every morning at 07:00 AM, collecting unread emails, calendar events, and weather for DAZY's briefing."
            )

        # 2. Important Gmail monitor
        if "email" in clean or "gmail" in clean:
            return WorkflowSpec(
                name="Important Gmail Alerts",
                folder="Gmail",
                trigger_type="app_event",
                trigger_config={"piece": "gmail", "event": "new_email"},
                actions=[
                    {"piece": "dazy_ai", "action": "filter_important_messages"},
                    {"piece": "telegram", "action": "send_alert_notification"},
                    {"piece": "gmail", "action": "create_draft_reply"},
                ],
                requires_approval=True,
                summary="Watches inbox for priority emails, generates an AI summary, and drafts suggested replies."
            )

        # 3. WhatsApp Business inbound
        if "whatsapp" in clean:
            return WorkflowSpec(
                name="WhatsApp Inbound Notification",
                folder="Communication",
                trigger_type="webhook",
                trigger_config={"endpoint": "/webhooks/whatsapp"},
                actions=[
                    {"piece": "whatsapp_business", "action": "parse_incoming_message"},
                    {"piece": "dazy_ai", "action": "categorize_message"},
                    {"piece": "dazy_relay", "action": "notify_desktop"},
                ],
                requires_approval=True,
                summary="Catches Meta webhook events for incoming WhatsApp messages and notifies DAZY with a proposed response."
            )

        # 4. Meeting reminder
        if "meeting" in clean or "calendar" in clean or "reminder" in clean:
            return WorkflowSpec(
                name="Smart Meeting Reminders",
                folder="Calendar",
                trigger_type="app_event",
                trigger_config={"piece": "google_calendar", "event": "event_starting_soon", "offset_minutes": 15},
                actions=[
                    {"piece": "google_calendar", "action": "get_meeting_link"},
                    {"piece": "dazy_relay", "action": "speak_reminder"},
                ],
                requires_approval=True,
                summary="Alerts you 15 minutes before appointments with meeting links and agenda."
            )

        # Default custom scheduled automation
        return WorkflowSpec(
            name=f"Custom Automation: {text[:30]}",
            folder="Personal",
            trigger_type="schedule",
            trigger_config={"schedule": "manual"},
            actions=[{"piece": "custom", "action": "execute", "description": text}],
            requires_approval=True,
            summary=f"Custom workflow planned for: {text}"
        )
