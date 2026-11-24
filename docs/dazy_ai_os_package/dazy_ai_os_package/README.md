# DAZY AI OS — PRD and Design Reference Pack

This ZIP contains the product requirements, reference architecture, phased development plan, master implementation prompt, recommended technology/tool stack, agent skill roles and generated visual references.

## Files
- `PRD.md` — product scope, requirements, security, data model and acceptance criteria.
- `architecture/REFERENCE_ARCHITECTURE.md` — system boundaries and data flows.
- `architecture/DEVELOPMENT_PLAN.md` — phases, workstreams and release gates.
- `prompts/MASTER_IMPLEMENTATION_PROMPT.md` — prompt to give your coding agent.
- `skills_and_tools/TOOLS_AND_AGENT_SKILLS.md` — recommended tools, libraries and specialist agent roles.
- `demo_images/` — generated UI concept references.

## Important
The images are design references, not screenshots of a working product. All sample counts, statuses, graphs and labels in the images are illustrative. The implementation must use real backend telemetry or explicitly labeled demo data.

## Recommended use
1. Open the existing DAZY repository in your coding environment.
2. Give the coding agent `prompts/MASTER_IMPLEMENTATION_PROMPT.md`.
3. Attach or provide the complete package so it can read the PRD and architecture documents.
4. Require the repository audit before implementation.
5. Approve phases using the release gates in the development plan.
6. Do not provide production secrets in chat or commit them to the repository.
