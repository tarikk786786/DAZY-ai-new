---
name: software-development
title: Software Development & Desktop Engineering
description: System-level automation, desktop controls, file operations, and safe code modifications.
---

# Software Development Skill

## Directives
1. Strictly obey the UI-thread invariant: background tasks never touch Qt widgets directly.
2. Execute file modifications and system actions with evidence-based verification (`core/outcome.py`).
3. Protect against accidental data loss through confirmation gates (`core/confirm.py`) and undo stacks (`core/undo.py`).
4. Ensure all commands and tests exit with code 0 before claiming completion.
