# DAZY — Capabilities, Skills & MCP Integration

## 1. Directory Conventions

DAZY preserves the strict architectural separations inherited from Mark-LVII:
* **`actions/`**: Core system and computer-driving capabilities (mouse, keyboard, files, system settings, desktop monitoring).
* **`plugins/`**: Drop-in external user tools. Self-describing via `PLUGIN` dict and `run()`.
* **`agents/`**: Autonomous sub-agent profiles (`general.md`, `researcher.md`, `dazy_companion.md`).
* **`agents/skills/`**: Reusable agent skills (`dazy-personality`, `indian-languages`, `emotional-intelligence`, `islamic-research`, `software-development`).
* **`core/mcp/`**: Model Context Protocol (MCP) server integration and dynamic tool mounting.

---

## 2. MCP Subsystem (`core/mcp/`)

* **`manager.py`**: Mounts and detaches external MCP servers dynamically.
* **`client.py`**: Manages stdio and HTTP/SSE transports.
* **`tool_adapter.py`**: Converts MCP `inputSchema` definitions into Mark-LVII tool declarations.
* **`security.py`**: Enforces confirmation gates on sensitive operations (delete, format, payment, send_email).

---

## 3. Capability Registry (`core/capabilities/`)

* Unifies all 4 execution surfaces (Actions, Plugins, Skills, and MCP) into `CapabilityRegistry`.
* Exposes automatic discovery through `discover_all_capabilities()`.
* Budgeting: Prevents overwhelming smaller language models by enforcing tool count budgets and character caps.
