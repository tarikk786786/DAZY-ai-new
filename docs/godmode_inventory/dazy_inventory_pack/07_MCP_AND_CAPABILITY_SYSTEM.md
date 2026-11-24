# 07 — MCP and the unified capability system

## MCP code present

- `core/mcp/client.py` — MCP client/transport handling.
- `core/mcp/manager.py` — attaches/detaches external servers, asks for tools and mounts capability handlers.
- `core/mcp/registry.py` — `MCPServerRecord` with ID/name/transport/command/args/URL/env/enabled/tools/status/error fields.
- `core/mcp/tool_adapter.py` — converts MCP tool definitions to DAZY tool definitions.
- `core/mcp/security.py` — security/confirmation support.
- `core/mcp/activepieces_adapter.py` — Activepieces bridge.

The registry comments allow `stdio`, `sse` and `http` transport labels. The capability docs describe stdio and HTTP/SSE. This is an implementation framework, not evidence that any particular community MCP server is currently connected.

## Unified capability registry

`core/capabilities/registry.py` uses capability kinds:

- `action`
- `plugin`
- `skill`
- `mcp`

`core/capabilities/discovery.py` scans:

- `actions/*.py` for a `TOOL` declaration and `run()` function.
- `plugins/*.py` for `PLUGIN` metadata and `run()`.
- `agents/skills/*/SKILL.md` for skill metadata/content.
- Connected MCP tools are mounted by the MCP manager.

There are also capability evaluator, installer and router modules. `core/action_loader.py` and `core/plugin_loader.py` are separate discovery/loading paths.

## Candidate official/community MCP sources — not confirmed connected

- Official MCP servers: https://github.com/modelcontextprotocol/servers
- MCP TypeScript SDK: https://github.com/modelcontextprotocol/typescript-sdk
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- GitHub MCP Server: https://github.com/github/github-mcp-server
- Playwright MCP: https://github.com/microsoft/playwright-mcp
- Awesome MCP lists: https://github.com/AlexMili/Awesome-MCP

Potential MCP categories to evaluate: filesystem; fetch/search; GitHub; browser; PostgreSQL; calendar; email; local desktop; notifications; device discovery; research; monitoring.

## Safe MCP adoption checklist

1. Verify official repository/maintainer and licence.
2. Pin a release/commit; do not use floating unreviewed code in production.
3. Define least-privilege filesystem/database/network scope.
4. Keep secrets in environment/secret manager, not MCP JSON checked into Git.
5. Distinguish read-only from write/destructive tools.
6. Require explicit confirmation for deleting, sending, publishing, spending or changing system settings.
7. Log tool name, args redacted for secrets, actor, permission result, outcome and duration.
8. Add timeouts, output limits and allowlists.
9. Run untrusted tools in a sandbox.
10. Revoke credentials and disconnect a server cleanly.
