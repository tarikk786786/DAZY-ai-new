# Universal Capability Atlas

A standalone, machine-readable catalogue of free and open-source AI-assistant
capabilities: libraries, frameworks, models, MCP servers, APIs and datasets.

**Core honesty rule:** every entry's licence, cost class and maintenance status
default to `unknown` and change ONLY when the live GitHub verification engine
has real API evidence in hand. Nothing is assumed free because a repo is
public, and nothing is guessed. Failures are recorded too.

## Status (honest, as of last run)

| | |
|---|---|
| Total entries | 71 across 15 categories |
| Verified against live GitHub API | **5** (LiteLLM, LangGraph, Pydantic AI, smolagents, pysentimiento) |
| Unverified (explicitly `unknown`) | 66 |
| GitHub token | none — unauthenticated 60 req/hr limit applies; verification is incremental by design |
| Test suite | 16/16 passing (all GitHub calls mocked; no live network in tests) |

Live-verified evidence from the first run:
- `litellm` — licence `custom (NOASSERTION)`, maintenance `active`
- `langgraph` — MIT, `active`
- `pydantic-ai` — MIT, `active`
- `smolagents` — Apache-2.0, `active`
- `pysentimiento` — custom (NOASSERTION), `stale` (no commit in 180+ days)

The remaining 66 entries are NOT marked free, active or anything else — they
sit at `unknown` until a verification run covers them. Run `verify-all`
repeatedly; each run verifies another batch and caches results for 7 days.

## No auto-installation

This project **never** installs, downloads or executes anything it discovers.
It is a read-only registry with evidence. Adding an entry stores a URL;
verifying an entry performs exactly two GET requests against api.github.com
(repo metadata + licence file) and stores the raw evidence JSON.

## No API keys collected

The Atlas stores no credentials. Setting a `GITHUB_TOKEN` env var is optional
(raises the rate limit from 60 to 5000 req/hr) and is used only as an
Authorization header — it is never written to the database.

## Run it

```bash
python3 -m atlas            # migrates, seeds, serves dashboard on 127.0.0.1:8790
python3 -m pytest atlas/tests/ -q
```

The dashboard lives at `http://127.0.0.1:8790` and shows every entry with its
verification state. API surface:

- `GET /api/v1/entries?q=&category=&verified=&cost=&maintenance=` — search/filter
- `GET /api/v1/entries/{id}` — full entry incl. evidence JSON
- `GET /api/v1/categories`, `GET /api/v1/stats`
- `POST /api/v1/entries/{id}/verify` — verify one against GitHub
- `POST /api/v1/verify-all?limit=25` — verify the next batch (rate-limit aware)
- `GET /api/v1/export?fmt=json|markdown`

## Registry fields

Each entry carries: `name`, `capability`, `subcapability`, `category`,
`repo_url`, `docs_url`, `entry_type`, `languages`, and the verification-driven
`licence`, `cost_class`, `maintenance`, `runtime`, `platform`, `stars`,
`last_commit`, `archived`, `verified_at`, `verified_evidence` (raw API
evidence JSON) and `last_verified_status`.

Verification writes `cost_class: oss` for public repos, but that is a claim
about the code's licence only — hosted-API costs of the same tool are a
separate judgement recorded as `unknown` unless separately classified.
