---
name: tdd-verification
description: Test-Driven Development verification gates, regression prevention, and exit code 0 enforcement.
---

# TDD Verification Skill (NEURON.ONE GodMode Edition)

## Objective
Guarantee software correctness before shipping any modification:
1. **Red-Green-Refactor**: Always write or identify a failing test for a bug, apply the minimal fix, and confirm the test turns green.
2. **Strict Verification**: Never claim a task or test passed without executing the test runner command and verifying exit code 0.
3. **Non-Regressive Verification**: Run the entire regression suite (`pytest tests/`) to ensure new changes do not break existing audio, dashboard, memory, or provider capabilities.
4. **Mock External Networks in Unit Tests**: Unit tests must use mock fixtures for remote LLM APIs to maintain fast execution (<10s) and zero cost.
