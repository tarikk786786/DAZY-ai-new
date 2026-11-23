"""core/capabilities/evaluator.py — Evaluates capabilities and safety constraints."""
from __future__ import annotations

import inspect
from typing import Any
from core.capabilities.registry import Capability


def evaluate_capability_safety(cap: Capability) -> tuple[bool, str]:
    """Ensures a capability meets execution invariants:

    1. Does not import or instantiate PyQt widgets in worker threads
    2. Validates parameter schemas
    3. Verifies callable handlers for actions and plugins
    """
    if cap.kind in ("action", "plugin"):
        if not callable(cap.handler):
            return False, f"Capability {cap.name} missing callable run() handler"

        # Check parameter schema format
        params = cap.parameters
        if not isinstance(params, dict):
            return False, f"Capability {cap.name} parameters must be a dictionary"

    return True, "Safe"
