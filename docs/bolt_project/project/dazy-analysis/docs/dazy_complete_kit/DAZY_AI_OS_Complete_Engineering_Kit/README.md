# DAZY AI OS — Complete Engineering & Implementation Kit

**Prepared:** 24 November 2026  
**Target:** Existing DAZY project — Windows desktop + web dashboard  
**Hardware profile:** 8 GB system RAM  
**Identity requirement:** Display name **Tarik** (never hard-code “John” or a fake demo user)  
**UI:** Premium command center + telemetry-backed 3D brain + Repo Radar  
**Repair policy:** Safe, allowlisted automatic recovery; approval for risky actions

## Package contents

- `prd/DAZY_AI_OS_PRD.md` — complete product requirements.
- `architecture/REFERENCE_ARCHITECTURE.md` — core, control-plane, runtime and adapter design.
- `architecture/REPOSITORY_ADOPTION_PLAN.md` — where the four supplied repositories fit.
- `integrations/REPOSITORY_ADAPTER_CONTRACT.md` — integration boundaries and contracts.
- `integrations/TOOLS_SKILLS_MCP_CATALOG.md` — tool, skill, MCP and provider management.
- `ui/MAIN_UI_AND_REPO_RADAR_SPEC.md` — main dashboard, identity, profile, Repo Radar and 3D UI.
- `ui/IDENTITY_FIX_TARIK.md` — root-cause and regression specification for the “John” greeting bug.
- `performance/8GB_LOW_RESOURCE_ARCHITECTURE.md` — 8 GB operating profile and optimization policy.
- `diagnostics/WINDOWS_READ_ONLY_DIAGNOSTICS.md` — safe PowerShell diagnostics.
- `security/LICENSE_AND_SUPPLY_CHAIN.md` — license and repository security review requirements.
- `schemas/*.json` — example typed contracts.
- `prompts/MASTER_IMPLEMENTATION_PROMPT.md` — main coding-agent prompt.
- `prompts/IDENTITY_AND_UI_FIX_PROMPT.md` — focused name/UI fix prompt.
- `prompts/REPO_RADAR_AND_ADAPTERS_PROMPT.md` — repository discovery/integration prompt.
- `prompts/8GB_OPTIMIZATION_PROMPT.md` — resource optimization prompt.
- `demo_images/` — earlier generated dashboard references and a new SVG mockup.
- `TASK_LEDGER.md` — implementation statuses and evidence gates.

## Important truthfulness rules

1. This is a specification and design reference kit. It does not modify the DAZY repository by itself.
2. Generated screenshots are concept references. Any numbers/statuses in them are dummy data.
3. Only the backend can determine whether an integration is connected, a worker is running, a repair succeeded or a test passed.
4. Repo recommendations are candidates. The coding agent must re-check current source, releases, dependencies, license files and advisories before adoption.
5. Never put secrets in the ZIP, repository, frontend, logs or screenshots.
6. Preserve the existing working DAZY stack. Audit before replacing frameworks or services.

## Recommended use

1. Open the existing DAZY repository in Cursor, Antigravity, Claude Code or another coding agent.
2. Give it `prompts/MASTER_IMPLEMENTATION_PROMPT.md` and the complete ZIP.
3. Require the repository audit before edits.
4. Implement identity correction and the shared backend/source-of-truth first.
5. Add Repo Radar in read-only mode.
6. Add only the selected agent adapters one at a time.
7. Apply the 8 GB profile and measure before/after.
8. Mark a feature VERIFIED only with test evidence.

## Repository references

- Nanobot: https://github.com/HKUDS/nanobot
- AgenticSeek: https://github.com/Fosowl/agenticSeek
- OpenManus: https://github.com/FoundationAgents/OpenManus
- n8n: https://github.com/n8n-io/n8n
- Tom Dörr profile inspiration: https://x.com/tom_doerr

The Tom Dörr reference is treated as inspiration for a curated GitHub/project discovery experience, not endorsement, affiliation or permission to copy branding/content. The supplied image URL could not be independently fetched in the research step, so the UI spec uses the textual reference and the supplied repository list.

## Testing and verification expansion

The `testing/` folder adds the recommended test stack, real-use journey matrix, tool links, PowerShell read-only preflight, tiny k6 smoke, starter Playwright tests, agent evaluation cases and Testing Center UI specification.

On an 8 GB workstation, run suites sequentially. Use hosted CI/staging for heavy load and DAST tests. Never run destructive or active security tests against production.
