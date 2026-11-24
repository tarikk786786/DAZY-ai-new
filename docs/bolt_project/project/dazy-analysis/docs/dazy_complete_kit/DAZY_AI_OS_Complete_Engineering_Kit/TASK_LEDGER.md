# DAZY implementation task ledger

Use status values: `NOT STARTED`, `IN PROGRESS`, `IMPLEMENTED`, `TESTED`, `VERIFIED`, `BLOCKED`.

| Work item | Initial status | Evidence required |
|---|---|---|
| Full repository audit | NOT STARTED | Audit report + baseline |
| Canonical profile / Tarik identity | NOT STARTED | Web/desktop/prompt regression tests |
| Main Command Center UI | NOT STARTED | Playwright screenshots + API-backed states |
| Repo Radar read-only research | NOT STARTED | GitHub API contract tests |
| License and dependency checks | NOT STARTED | Reports and notices |
| Adapter contract | NOT STARTED | Schema/contract tests |
| Nanobot adapter prototype | NOT STARTED | One end-to-end task, single process |
| OpenManus optional executor | NOT STARTED | On-demand task test |
| AgenticSeek optional isolated adapter | BLOCKED until license/resource review | Legal review + isolated runtime test |
| n8n external adapter | NOT STARTED | Authenticated webhook test; license review |
| Tools / skills / MCP registry | NOT STARTED | Discovery, permission and failure tests |
| 8 GB resource profile | NOT STARTED | Before/after measurements |
| 3D telemetry graph | NOT STARTED | Backend graph/event parity tests |
| Diagnostics and controlled repair | NOT STARTED | Failure injection + rollback test |
| Desktop companion | NOT STARTED | Windows package and backend control tests |
| Security and release gates | NOT STARTED | Threat model, SBOM, backup/restore test |

Never promote `IMPLEMENTED` to `VERIFIED` without attached evidence.
