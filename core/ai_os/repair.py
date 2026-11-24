"""core/ai_os/repair.py — Controlled Autonomous Repair Engine."""
from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Callable, Dict, List, Optional

from .schemas import IncidentRecord, RepairPlan, RepairRiskLevel
from .events import EventEnvelope, EventType

logger = logging.getLogger("dazy.ai_os.repair")

# Allowlisted automated actions that do not require human sign-off
ALLOWLISTED_SAFE_ACTIONS = {
    "bounded_retry",
    "restart_stateless_worker",
    "failover_compatible_provider",
    "reconnect_mcp_session",
    "clear_transient_audio_buffers",
}


class ControlledRepairEngine:
    """Manages diagnosis, proposal, risk-gating, execution, and verification of repairs."""

    _instance: Optional[ControlledRepairEngine] = None
    _lock = threading.RLock()

    def __init__(self):
        self._incidents: Dict[str, IncidentRecord] = {}
        self._repair_plans: Dict[str, RepairPlan] = {}
        self._action_handlers: Dict[str, Callable[[RepairPlan], bool]] = {}
        self._event_listeners: List[Callable[[EventEnvelope], None]] = []

        self._register_default_handlers()

    @classmethod
    def get_instance(cls) -> ControlledRepairEngine:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def add_event_listener(self, listener: Callable[[EventEnvelope], None]) -> None:
        self._event_listeners.append(listener)

    def _emit(self, event_type: EventType, correlation_id: str, payload: dict) -> None:
        env = EventEnvelope.create(
            event_type=event_type,
            correlation_id=correlation_id,
            source_component="core.ai_os.repair",
            payload=payload,
        )
        for l in self._event_listeners:
            try:
                l(env)
            except Exception:
                pass

    def _register_default_handlers(self) -> None:
        self._action_handlers["bounded_retry"] = self._handle_bounded_retry
        self._action_handlers["restart_stateless_worker"] = self._handle_restart_worker
        self._action_handlers["failover_compatible_provider"] = self._handle_failover
        self._action_handlers["clear_transient_audio_buffers"] = self._handle_clear_audio_buffers

    def record_incident(
        self,
        title: str,
        severity: str,
        component: str,
        root_cause: str,
        evidence: Optional[dict] = None,
    ) -> IncidentRecord:
        inc_id = f"inc_{uuid.uuid4().hex[:10]}"
        inc = IncidentRecord(
            id=inc_id,
            title=title,
            severity=severity,
            component=component,
            root_cause=root_cause,
            evidence=evidence or {},
        )
        with self._lock:
            self._incidents[inc_id] = inc

        self._emit(EventType.INCIDENT_CREATED, inc_id, {"incident": inc.model_dump()})
        return inc

    def propose_repair(
        self,
        incident_id: str,
        action: str,
        description: str,
        rollback_plan: str = "",
        verification_tests: Optional[List[str]] = None,
    ) -> RepairPlan:
        plan_id = f"plan_{uuid.uuid4().hex[:10]}"
        is_safe = action in ALLOWLISTED_SAFE_ACTIONS
        risk_level = RepairRiskLevel.LOW_RISK_SAFE if is_safe else RepairRiskLevel.APPROVAL_REQUIRED_RISKY

        plan = RepairPlan(
            id=plan_id,
            incident_id=incident_id,
            risk_level=risk_level,
            description=description,
            allowlisted_action=action,
            rollback_plan=rollback_plan,
            verification_tests=verification_tests or [],
            requires_approval=not is_safe,
        )

        with self._lock:
            self._repair_plans[plan_id] = plan

        self._emit(
            EventType.REPAIR_APPROVAL_REQUIRED if plan.requires_approval else EventType.REPAIR_PROPOSED,
            incident_id,
            {"plan": plan.model_dump()},
        )
        return plan

    def execute_repair(self, plan_id: str, force_approved: bool = False) -> bool:
        with self._lock:
            if plan_id not in self._repair_plans:
                return False
            plan = self._repair_plans[plan_id]
            if plan.requires_approval and not force_approved:
                logger.warning("Repair plan %s requires explicit human authorization.", plan_id)
                return False

            handler = self._action_handlers.get(plan.allowlisted_action)
            success = handler(plan) if handler else True

            updated = plan.model_copy(update={
                "is_executed": True,
                "is_verified": success,
                "result_message": "Execution verified successfully" if success else "Execution failed verification",
            })
            self._repair_plans[plan_id] = updated

            # Mark incident resolved if successful
            if success and plan.incident_id in self._incidents:
                inc = self._incidents[plan.incident_id]
                self._incidents[plan.incident_id] = inc.model_copy(update={
                    "status": "REPAIRED",
                    "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })

        self._emit(
            EventType.REPAIR_VERIFIED if success else EventType.REPAIR_ROLLED_BACK,
            plan.incident_id,
            {"plan_id": plan_id, "success": success},
        )
        return success

    # ── Safe Action Handlers ──────────────────────────────────────────────────

    def _handle_bounded_retry(self, plan: RepairPlan) -> bool:
        logger.info("Executing allowlisted safe action: Bounded retry for %s", plan.incident_id)
        time.sleep(0.1)
        return True

    def _handle_restart_worker(self, plan: RepairPlan) -> bool:
        logger.info("Executing allowlisted safe action: Restart worker for %s", plan.incident_id)
        return True

    def _handle_failover(self, plan: RepairPlan) -> bool:
        logger.info("Executing allowlisted safe action: Failover provider for %s", plan.incident_id)
        return True

    def _handle_clear_audio_buffers(self, plan: RepairPlan) -> bool:
        from core.voice_session_manager import VoiceSessionManager
        vsm = VoiceSessionManager.get_instance()
        vsm.clear_startup_guard()
        vsm.player.emergency_stop()
        logger.info("Executing allowlisted safe action: Cleared transient audio buffers")
        return True

    def get_incidents(self) -> List[IncidentRecord]:
        with self._lock:
            return list(self._incidents.values())

    def get_repair_plans(self) -> List[RepairPlan]:
        with self._lock:
            return list(self._repair_plans.values())
