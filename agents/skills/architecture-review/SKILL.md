---
name: architecture-review
description: System architecture review, boundary validation, and anti-pattern detection for DAZY and connected subagents.
---

# Architecture Review Skill (NEURON.ONE GodMode Edition)

## Objective
Evaluate system components, boundaries, and dependencies to preserve DAZY's sovereign architecture:
1. Single Master Orchestrator rule: DAZY is the sole controller.
2. Unified Memory: All conversation, memory, and facts reside in local SQLite / `memory/` ledgers.
3. Asynchronous Worker Isolation: Background tasks must never block the primary voice/WebSocket conversational loop.

## Checklist
- **Coupling & Cohesion**: Are services cleanly decoupled with standard event payloads?
- **Resource Footprint**: Does any daemon exceed 200 MB RAM or create runaway background loops?
- **Error Boundaries**: Are network calls and LLM provider queries protected by timeout handlers and circuit breakers?
- **Zero Duplication**: Ensure no redundant or competing agents conflict with the core orchestrator.
