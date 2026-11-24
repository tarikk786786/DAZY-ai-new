# 00 — Audit scope, repository identity and evidence

## Repositories inspected

| Project | Repository | Branch/ref observed | Commit observed | Notes |
|---|---|---|---|---|
| Desktop assistant | https://github.com/tarikk786786/DAZY-ai-new | `main` and `dazy-transformation` | `48c9952d47485fee2f244595bc60a4d665c8be7a` | Both branches pointed to the same commit when inspected. Git tree contained 434 tracked paths. |
| Web companion | https://github.com/tarikk786786/DAZY-web | `main` | `0f8803261c69377379587745c21942c68935d26a` | Small React/Vite + Supabase app; no migration directory visible in the returned tree. |

Repository root links:
- Desktop: https://github.com/tarikk786786/DAZY-ai-new
- Web: https://github.com/tarikk786786/DAZY-web

## What was inspected

Desktop: recursive Git tree; `readme.md`; `requirements.txt`; `backend/requirements.txt`; `setup.py`; `skills-lock.json`; `.agent/PROJECT_STATE.md`; `.agent/PROJECT_TASK_LEDGER.md`; `.agent/EXECUTION_LOG.md`; `docs/CAPABILITIES.md`; `docs/PROVIDERS.md`; `docs/DAZY_ARCHITECTURE.md`; `main.py`; provider registry/base and representative provider adapters; MCP registry/manager; capability registry/discovery; action/plugin/integration examples; memory, emotion, voice and wake-word modules; local skill definitions.

Web: recursive Git tree; `README.md`; `package.json`; `package-lock.json`; `src/App.tsx`; `src/hud.tsx`; `src/useDazy.ts`; `src/useVoiceInput.ts`; `src/lib/speech.ts`; `src/lib/supabase.ts`; `src/lib/types.ts`; `supabase/config.toml`; `supabase/functions/dazy-chat/index.ts`; Vite and TypeScript configuration.

## Evidence limits

1. The desktop repo includes machine-local settings under ignored `config/api_keys.json`; it is not possible to infer live credentials or selected providers from the public repository.
2. Source files prove code is present, not that dependencies/models are installed or services are reachable.
3. README and project-state claims can disagree with source. Where they do, this inventory calls out the mismatch.
4. External MCP server connections are not confirmed merely because an MCP client/manager exists.
5. The desktop task ledger/execution log reports 97/97 tests passing at a previous session. This audit did not execute those tests.
6. The web `package.json` exposes `dev`, `build`, and `preview`; no test or lint script was declared.
7. Model names, API quotas, terms and hosted free tiers can change. Confirm with official providers before use.

## Important repository branding mismatch

The desktop code and docs describe DAZY, but `readme.md`, setup comments and some requirements comments still contain the inherited MARK/Mark-LVII name. Treat the checked-in docs/config and actual runtime registry as evidence; do not assume inherited branding text represents a separate running product.
