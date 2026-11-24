"""core/automation/suggestion_engine.py — DAZY Personal Automation Advisor.

Analyzes permitted interaction patterns to recommend high-value background
automations. Never activates workflows without explicit user approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AutomationSuggestion:
    id: str
    name: str
    problem_solved: str
    trigger: str
    connected_apps: list[str]
    required_permissions: list[str]
    schedule: str
    estimated_cost: str = "Free tier ($0.00)"
    privacy_considerations: str = "Only metadata and priority subjects inspected; full contents stay local."
    status: str = "PENDING"        # "PENDING" | "ACCEPTED" | "DISMISSED"


class SuggestionEngine:
    """Detects recurring manual patterns and proposes automated Activepieces workflows."""

    def __init__(self):
        self._history_events: list[str] = []
        self._suggestions: dict[str, AutomationSuggestion] = {}
        self._seed_default_suggestions()

    def _seed_default_suggestions(self):
        """Pre-seeds standard high-utility suggestions tailored for DAZY."""
        sug1 = AutomationSuggestion(
            id="sug_morning_brief",
            name="Automated Morning Briefing",
            problem_solved="Eliminates manual checks across Gmail, Calendar, and Weather every morning.",
            trigger="Scheduled every day at 07:30 AM",
            connected_apps=["Gmail", "Google Calendar", "Open-Meteo"],
            required_permissions=["Read unread emails", "Read calendar events"],
            schedule="0 7 * * *",
            estimated_cost="Free ($0)",
            privacy_considerations="Summaries generated locally/privately; credentials securely stored."
        )
        sug2 = AutomationSuggestion(
            id="sug_important_email_radar",
            name="Priority Email Radar & Telegram Alert",
            problem_solved="Alerts you immediately on important emails without checking inbox constantly.",
            trigger="New email matching priority sender/keywords",
            connected_apps=["Gmail", "Telegram"],
            required_permissions=["Read emails", "Send Telegram messages"],
            schedule="Real-time (event-driven)",
            estimated_cost="Free ($0)",
            privacy_considerations="Only filtered high-priority messages trigger notifications."
        )
        self._suggestions[sug1.id] = sug1
        self._suggestions[sug2.id] = sug2

    def record_activity(self, intent: str) -> None:
        """Records an authorized interaction pattern for recommendation analysis."""
        self._history_events.append(intent.lower().strip())
        if len(self._history_events) > 100:
            self._history_events.pop(0)

        # Pattern detection: e.g. frequent email checks
        email_checks = sum(1 for e in self._history_events if "email" in e or "gmail" in e)
        if email_checks >= 3 and "sug_important_email_radar" not in self._suggestions:
            self._suggestions["sug_important_email_radar"] = AutomationSuggestion(
                id="sug_important_email_radar",
                name="Priority Email Radar",
                problem_solved="You frequently ask to check emails — automate priority alerts.",
                trigger="New email matching priority",
                connected_apps=["Gmail", "Telegram"],
                required_permissions=["Read email metadata"],
                schedule="Real-time",
            )

    def list_pending_suggestions(self) -> list[AutomationSuggestion]:
        return [s for s in self._suggestions.values() if s.status == "PENDING"]

    def accept_suggestion(self, suggestion_id: str) -> Optional[AutomationSuggestion]:
        sug = self._suggestions.get(suggestion_id)
        if sug:
            sug.status = "ACCEPTED"
            return sug
        return None

    def dismiss_suggestion(self, suggestion_id: str) -> None:
        sug = self._suggestions.get(suggestion_id)
        if sug:
            sug.status = "DISMISSED"


_GLOBAL_SUGGESTION_ENGINE: Optional[SuggestionEngine] = None


def get_suggestion_engine() -> SuggestionEngine:
    global _GLOBAL_SUGGESTION_ENGINE
    if _GLOBAL_SUGGESTION_ENGINE is None:
        _GLOBAL_SUGGESTION_ENGINE = SuggestionEngine()
    return _GLOBAL_SUGGESTION_ENGINE
