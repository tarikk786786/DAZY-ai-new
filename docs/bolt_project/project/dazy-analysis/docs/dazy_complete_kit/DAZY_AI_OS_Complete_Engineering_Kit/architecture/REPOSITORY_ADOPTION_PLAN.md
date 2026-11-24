# Repository Adoption Plan — Four Candidate Projects

**Review basis:** Public GitHub repository metadata, README and license files fetched for this package on 24 November 2026. This is an architecture fit review, not a complete security audit or runtime benchmark.

## Executive decision

| Project | License observed in repository | DAZY role | Default on 8 GB PC |
|---|---|---|---|
| HKUDS/nanobot | MIT | First adapter candidate for personal-agent capabilities | Off until installed/configured; one process only |
| FoundationAgents/OpenManus | MIT | Optional complex-task executor | Off; invoke on demand |
| Fosowl/agenticSeek | GPL-3.0 | Optional isolated browser/coding runtime | Not installed by default; preferably remote |
| n8n-io/n8n | Sustainable Use License + separate Enterprise files | External workflow engine | Remote/external; do not self-host locally by default |

## 1. Nanobot — first candidate to prototype

Repository: https://github.com/HKUDS/nanobot  
License: https://github.com/HKUDS/nanobot/blob/main/LICENSE  
Architecture: https://github.com/HKUDS/nanobot/blob/main/docs/architecture.md  
Automations: https://github.com/HKUDS/nanobot/blob/main/docs/automations.md  
Memory: https://github.com/HKUDS/nanobot/blob/main/docs/memory.md

### Observed capabilities from upstream documentation
- Python personal agent.
- Single Python gateway powers WebUI, terminal UI and chat channels.
- Provider adapters and tool execution loop.
- MCP tool support.
- Memory with conversation summaries, resident profile/memory and on-demand knowledge wiki.
- Scheduled automations, local triggers and heartbeat checks.
- README states Python 3.11 or newer.
- README describes a lightweight core and a Python SDK.

### Recommended use in DAZY
Use Nanobot as the first candidate for an optional adapter/prototype around personal-agent tools, scheduled tasks and memory concepts. Evaluate its Python SDK and source boundaries. Keep DAZY's own identity/profile, data store, command center and primary orchestrator authoritative.

### Do not
- Run a separate Nanobot WebUI as a competing DAZY home screen.
- Run a second always-on gateway if DAZY already has a gateway.
- Duplicate its memory with DAZY's memory without a migration/ownership plan.
- Assume upstream "lightweight" guarantees a specific memory footprint; benchmark one process on the actual PC.

## 2. OpenManus — optional complex-task executor

Repository: https://github.com/FoundationAgents/OpenManus  
License: https://github.com/FoundationAgents/OpenManus/blob/main/LICENSE

### Observed capabilities from upstream README
- Python multi-step agent framework.
- Python 3.12 and `uv` are recommended in the current README.
- Uses LLM API configuration.
- Optional flow/multi-agent mode.
- Browser Use CLI is described as a default MCP server in the current README.
- Browser automation and optional chart/data-analysis dependencies.

### Recommended use in DAZY
Treat it as an on-demand task executor behind the DAZY adapter contract. Give it one bounded job and a result schema. Start it only when DAZY delegates a suitable task. Return outputs and artifacts to DAZY for verification.

### 8 GB rules
- Do not run its browser stack in the background.
- Do not enable optional multi-agent or chart dependencies unless the task requires them.
- Prefer remote model APIs.
- Run one job at a time in a constrained environment.
- Inspect requirements and Python version compatibility before installation.

## 3. AgenticSeek — isolated optional runtime

Repository: https://github.com/Fosowl/agenticSeek  
License: https://github.com/Fosowl/agenticSeek/blob/main/LICENSE

### Observed capabilities from upstream README
- Describes itself as a local/private autonomous assistant for browsing and coding.
- Uses agent selection and multi-step planning.
- Voice is described as in progress in the fetched README.
- README recommends Python 3.10.x and Docker Engine/Compose for bundled services such as SearxNG.
- README documents both local model providers and external API configuration.
- Repository license is GPL-3.0.

### Recommended use in DAZY
Keep it optional and isolated behind a remote-runner or separate-process adapter. On an 8 GB machine, do not enable local model loading by default. A remote or better-resourced host is preferable for local model workloads.

### License warning
Do not copy or tightly combine AgenticSeek source into a DAZY distributable without a GPL-3.0 compatibility review. If you distribute a combined or derivative work, GPL obligations may apply. A separate process/service boundary can reduce technical coupling but is not a legal guarantee. Obtain legal review for the intended distribution model.

## 4. n8n — external workflow integration

Repository: https://github.com/n8n-io/n8n  
License: https://github.com/n8n-io/n8n/blob/master/LICENSE.md  
Documentation: https://docs.n8n.io

### Observed capabilities from upstream README
- Visual workflow automation.
- AI workflows and agents.
- 1,500+ integrations claimed by the repository README.
- Self-hosted and cloud deployment options.
- API/webhook-based workflow composition.

### License warning
The fetched LICENSE.md describes the Sustainable Use License for covered files and separately restricts `.ee.` files/directories. Its terms limit use to internal business purposes or non-commercial/personal use, with additional distribution conditions. Review the current license and intended use before commercial use, redistribution or embedding. It is not conventional OSI open-source licensing.

### Recommended use in DAZY
Use n8n as a user-configured external workflow endpoint via webhooks/API. Do not run its complete stack locally by default on the 8 GB PC. Do not copy n8n source into DAZY.

## 5. Recommended adoption order

1. Prototype Nanobot adapter, but only after the DAZY repository audit.
2. Create the DAZY adapter contract and verify a single end-to-end task.
3. Add OpenManus as an on-demand executor if there is a real capability gap.
4. Add AgenticSeek only for a clearly needed isolated browser/coding capability and after license/resource review.
5. Add n8n as an external workflow connection, not another local always-on service.

## 6. Repository Radar evaluation checklist

Before any repository install:
- Confirm owner and official repository URL.
- Inspect LICENSE and license exceptions.
- Inspect latest release and recent commits.
- Check archived status and maintenance.
- Inspect Python/Node versions and lockfiles.
- Inspect installation scripts and post-install hooks.
- Inspect Docker services and model/browser prerequisites.
- Scan dependency vulnerabilities and secrets.
- Identify duplicate capability already built into DAZY.
- Estimate resource impact qualitatively; do not invent numeric RAM claims.
- Run tests in a disposable environment only after approval.
- Save exact commit SHA and review date.
- Provide uninstall and data-retention plan.
