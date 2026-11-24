"""plugins/automation.py — DAZY Universal Automation & Activepieces Manager.

Allows DAZY to plan, create, inspect, and manage 24/7 background automations
via Activepieces and the DAZY Personal Automation Advisor.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

PLUGIN = {
    "name": "manage_automation",
    "description": (
        "Plans, creates, or inspects 24/7 Activepieces workflows and requests recommendations "
        "from the DAZY Personal Automation Advisor (e.g. morning briefing, email alerts, reminders)."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "enum": ["status", "list_flows", "create_flow", "get_advice", "publish_flow"],
                "description": "Operation to perform",
            },
            "prompt": {
                "type": "STRING",
                "description": "Natural language request describing the desired automation (for create_flow)",
            },
            "flow_id": {
                "type": "STRING",
                "description": "Identifier of the workflow to publish or inspect",
            },
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    """Executes automation management operations safely on worker threads."""
    action = str(parameters.get("action", "status")).lower()
    prompt = str(parameters.get("prompt", ""))
    flow_id = str(parameters.get("flow_id", ""))

    from core.automation.manager import get_automation_manager

    mgr = get_automation_manager()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if action == "status":
            overview = loop.run_until_complete(mgr.get_overview())
            conn = "connected" if overview["health"].get("connected") else "offline"
            return (
                f"Activepieces instance is {conn}. {overview['active_count']} persistent workflows active. "
                f"{len(overview['pending_suggestions'])} recommendations available."
            )

        elif action == "list_flows":
            overview = loop.run_until_complete(mgr.get_overview())
            flows = overview.get("flows", [])
            if not flows:
                return "Activepieces me abhi koi workflow configured nahi hai."
            names = [f"{f['name']} ({f['status']})" for f in flows]
            return f"Active workflows: {', '.join(names)}"

        elif action == "create_flow":
            if not prompt:
                return "Workflow banane ke liye prompt specify karein."
            res = loop.run_until_complete(mgr.create_automation_from_speech(prompt))
            if player:
                player.write_log(f"AUTO: Draft created — {res['spec']['name']}")
            return res.get("message", "Draft workflow successfully created.")

        elif action == "publish_flow":
            if not flow_id:
                return "Publish karne ke liye flow_id required hai."
            res = loop.run_until_complete(mgr.approve_and_publish(flow_id))
            return res.get("message", f"Workflow {flow_id} publish ho chuka hai.")

        elif action == "get_advice":
            sugs = mgr.advisor.list_pending_suggestions()
            if not sugs:
                return "Abhi koi naya recommendation pending nahi hai."
            advice = sugs[0]
            return f"DAZY Advisor Recommendation: {advice.name} — {advice.problem_solved}"

    except Exception as e:
        return f"Automation operation failed: {e}"
    finally:
        loop.close()

    return "Operation complete."
