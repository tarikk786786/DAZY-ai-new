# ADR-0007: Layered Architecture Enforcement with Import Linter

* **Status:** Accepted
* **Deciders:** Principal Architect, Software Developer
* **Date:** 2026-11-24

## Context and Problem Statement
In past iterations, circular and reverse dependencies leaked across modules (e.g. `core/audio_devices.py` importing `actions.computer_settings`, or `main.py` directly mutating subsystem internals). This degraded modularity and increased regression risk during refactoring.

## Decision Drivers
* Strict architectural layers with automated CI/lint enforcement.
* Domain independence: core audio and DSP must never depend on high-level tools or actions.
* Prevention of circular import regressions.

## Considered Options
1. **Import Linter (`.importlinter`) Contract**:
   Define explicit layers:
   `gui` / `dashboard` $\to$ `main` $\to$ `providers` $\to$ `actions` $\to$ `core` $\to$ `memory`.
   Forbid reverse imports.
2. Manual code reviews without automated linting.
3. Completely separate monorepo packages.

## Decision Outcome
Chosen option: **Import Linter (`.importlinter`) Contract**.
Automated layer boundary checks are configured in `.importlinter` and validated via `python -c "import importlinter.cli; import sys; sys.argv=['lint-imports']; importlinter.cli.lint_imports()"`. System audio controls in `actions/computer_settings.py` now delegate to `core/audio_devices.py` rather than the reverse.

### Positive Consequences
* CI fails immediately if an illegal dependency is introduced.
* Modules remain cleanly testable in isolation.
* Clear architectural hierarchy across the entire repository.
