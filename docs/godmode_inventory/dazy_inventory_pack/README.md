# DAZY — Complete Project, Tools, Libraries, Skills, MCP & Knowledge Inventory

**Prepared:** 24 November 2026  
**Scope:** the two DAZY repositories inspected for this inventory: desktop `DAZY-ai-new` and web companion `DAZY-web`.  
**Purpose:** one detailed, link-rich engineering reference separating what exists in source, what is configured/documented, what is optional, and what is only a candidate for future adoption.

## Start here

1. [Audit scope, repositories and evidence rules](00_AUDIT_SCOPE_AND_STATUS.md)
2. [System architecture and stack](01_SYSTEM_ARCHITECTURE.md)
3. [LLM brains and providers](02_MODEL_PROVIDERS.md)
4. [Audio, hearing and speaking](03_AUDIO_VOICE.md)
5. [Emotion, personality and language intelligence](04_EMOTION_PERSONALITY_LANGUAGE.md)
6. [Memory, knowledge, research and retrieval](05_MEMORY_KNOWLEDGE_RESEARCH.md)
7. [Agents, workers and skills](06_AGENTS_WORKERS_SKILLS.md)
8. [MCP and capability registry](07_MCP_AND_CAPABILITY_SYSTEM.md)
9. [Actions, plugins and integrations](08_ACTIONS_PLUGINS_INTEGRATIONS.md)
10. [Desktop, automation, computer and vision tools](09_DESKTOP_AUTOMATION_COMPUTER_VISION.md)
11. [Web companion inventory](10_WEB_COMPANION.md)
12. [Dependencies and packages](11_DEPENDENCIES.md)
13. [Security, limitations and verification gaps](12_SECURITY_AND_GAPS.md)
14. [Full capability roadmap](13_FULL_CAPABILITY_ROADMAP.md)
15. [Additional free/open-source library candidates](14_FREE_OPEN_SOURCE_CANDIDATE_LIBRARY_CATALOG.md)
16. [Source link index](15_SOURCE_LINK_INDEX.md)
17. [Machine-readable inventory](data/inventory.json)
18. [Dependency CSV](data/dependencies.csv)
19. [Repository map CSV](data/repository_map.csv)

## Status labels

- **Implemented in source** — code exists in the inspected Git commit. This does not prove it works on the user's machine.
- **Registered/discoverable** — code is included in an explicit registry or discovery mechanism.
- **Documented/configurable** — described in docs/config, but live availability or credentials are not verified.
- **Optional** — requires extra installation, a model download, a service or an API key.
- **Partial/stub** — adapter or interface exists, but key functionality is incomplete, returns no result, or is not fully wired.
- **Candidate only** — discussed/recommended library, not found as an integrated dependency in these repositories.
- **Unknown/unverified** — runtime state, deployed configuration, external server or credential could not be read.

## Critical interpretation

This ZIP is a source inventory, not a runtime health certificate. It does not claim all tools are currently installed, authenticated, connected, deployed, or working. Project logs report historical test results; those tests were not re-run while preparing this ZIP. Never paste API keys into this archive, GitHub, chat or frontend code.
