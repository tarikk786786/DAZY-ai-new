---
name: autonomous-worker
description: Background worker execution lifecycle, DAG task dependency management, and heartbeat monitoring.
---

# Autonomous Worker Skill (GodMode-Team & NEURON.ONE Edition)

## Objective
Govern autonomous background agents executing complex multi-step goals without human micromanagement:
1. **DAG Decomposition**: Complex goals are broken down into a Directed Acyclic Graph of subtasks.
2. **Subagent Execution**: Each subtask executes with an isolated scope, specific tools, and a clear definition of done.
3. **Telemetry & Progress**: Each task step emits lifecycle events (`pending` -> `running` -> `completed` / `failed`) streamed to the dashboard via WebSocket.
4. **Sovereign Supervision**: The main DAZY brain monitors progress, reviews outputs, and synthesizes the final answer for Tarik.
