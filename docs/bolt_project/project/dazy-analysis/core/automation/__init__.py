"""core/automation/ — DAZY Universal Automation Subsystem & Personal Automation Advisor."""
from .manager import AutomationManager, get_automation_manager
from .planner import AutomationPlanner, WorkflowSpec
from .suggestion_engine import SuggestionEngine, AutomationSuggestion, get_suggestion_engine
from .approval import require_approval_for_action, ActionRiskLevel

__all__ = [
    "AutomationManager",
    "get_automation_manager",
    "AutomationPlanner",
    "WorkflowSpec",
    "SuggestionEngine",
    "AutomationSuggestion",
    "get_suggestion_engine",
    "require_approval_for_action",
    "ActionRiskLevel",
]
