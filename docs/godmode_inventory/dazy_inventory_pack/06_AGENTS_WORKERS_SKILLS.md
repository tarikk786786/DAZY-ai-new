# 06 — Agents, workers, planners and skills

## Agent profiles

- `agents/general.md` — general assistant profile.
- `agents/researcher.md` — researcher profile.
- `agents/dazy_companion.md` — DAZY companion profile.

## Agent runtime and task orchestration

- `agent/planner.py` — plan tasks.
- `agent/executor.py` — execute tasks.
- `agent/task_queue.py` — task queue.
- `agent/error_handler.py` — error handling.
- `core/agent_orchestrator.py` — agent coordination.
- `core/tasks/agents.py` — task-agent helpers.
- `core/tasks/brain.py` — task reasoning/brain.
- `core/tasks/engine.py` — task engine.
- `core/tasks/store.py` — task storage.
- `core/tasks/tools.py` — task-tool integration.
- `core/ai_os/orchestrator.py`, `graph.py`, `events.py`, `schemas.py`, `registry.py`, `telemetry.py`, `repair.py` — AI OS orchestration, event, registry, telemetry and repair components.

Project task ledger mentions a LangGraph multi-agent coordination task, but the exact active runtime dependency/configuration must be checked. `requirements.txt` does not list LangGraph as a base dependency. Do not treat a passing test label as proof a third-party orchestration package is installed.

## Six project-local skill definitions

1. `agents/skills/automation-advisor/SKILL.md`
2. `agents/skills/dazy-personality/SKILL.md`
3. `agents/skills/emotional-intelligence/SKILL.md`
4. `agents/skills/indian-languages/SKILL.md`
5. `agents/skills/islamic-research/SKILL.md`
6. `agents/skills/software-development/SKILL.md`

## Two locked external agent skills

`skills-lock.json` records two skills sourced from `supabase/agent-skills` at commit `c9be0e931b7930f7d02126d04774d904c381e7d7`:

- `supabase` → `.agents/skills/supabase/SKILL.md`
- `supabase-postgres-best-practices` → `.agents/skills/supabase-postgres-best-practices/SKILL.md`

The latter includes detailed references for query performance, connection management, security/RLS, schema design, locking, data access, monitoring and advanced features.

## Skills are not APIs or MCP servers

A skill is reusable instructions/knowledge. A plugin/action is executable capability. An MCP server exposes tools via a protocol. A model decides when to invoke a capability, subject to permissions. Keep those concepts distinct.

## Candidate agent frameworks — not integrated by this audit

- LangChain: https://github.com/langchain-ai/langchain
- LangGraph: https://github.com/langchain-ai/langgraph
- Pydantic AI: https://github.com/pydantic/pydantic-ai
- Google ADK: https://github.com/google/adk-python
- Agno: https://github.com/agno-agi/agno
- CrewAI: https://github.com/crewAIInc/crewAI
- smolagents: https://github.com/huggingface/smolagents
- Mastra: https://github.com/mastra-ai/mastra
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- DSPy: https://github.com/stanfordnlp/dspy
- Vercel AI SDK: https://github.com/vercel/ai
- LiteLLM: https://github.com/BerriAI/litellm
