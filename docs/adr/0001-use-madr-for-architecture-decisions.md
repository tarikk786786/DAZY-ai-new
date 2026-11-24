# ADR-0001: Use MADR for Architecture Decisions

* **Status:** Accepted
* **Deciders:** Principal Architect, Core Engineers
* **Date:** 2026-11-24

## Context and Problem Statement
As DAZY expands across dual-engine conversational pipelines, multi-speaker voice diarization, desktop GUI, and remote web dashboards, architectural choices require permanent, version-controlled records. Tribal knowledge or scattered comments in code lead to regressions and conflicting assumptions.

## Decision Drivers
* Need for version-controlled, lightweight architectural decisions.
* Clear visibility into design trade-offs, options considered, and consequences.
* Direct integration with GitHub pull requests and developer workflows.

## Considered Options
1. **MADR (Markdown Any Architecture Decision Records)**
2. Unstructured README notes
3. Confluence / Wiki pages

## Decision Outcome
Chosen option: **MADR (Markdown Any Architecture Decision Records)**.
All significant structural, protocol, and cross-cutting decisions are recorded as MADRs in `docs/adr/`.

### Positive Consequences
* Versioned alongside source code in git.
* Fast review during PRs and refactoring.
* Explicit rationale preserved across sessions.
