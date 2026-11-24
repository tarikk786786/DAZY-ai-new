# External Runtime Adapter Contract

## Purpose
DAZY owns identity, orchestration, policy, user interface, task ledger, memory governance and verification. External repositories provide bounded capabilities only.

## Runtime interface

```ts
type RuntimeStatus =
  | "unavailable" | "untested" | "ready" | "degraded" | "busy" | "failed";

interface RuntimeCapabilities {
  text: boolean;
  vision?: boolean;
  audio?: boolean;
  browser?: boolean;
  codeExecution?: boolean;
  mcp?: boolean;
  scheduling?: boolean;
  memory?: boolean;
  toolCalling?: boolean;
}

interface RuntimeTask {
  requestId: string;
  taskId: string;
  correlationId: string;
  userId: string;
  displayName: string;
  profileVersion: number;
  instruction: string;
  inputs: Record<string, unknown>;
  capabilityRequirements: string[];
  permissionScope: string[];
  maxDurationSeconds: number;
  maxConcurrentJobs: number;
  resourceProfile: "low" | "balanced" | "high";
}

interface RuntimeResult {
  runId: string;
  status: "completed" | "failed" | "cancelled" | "needs_approval";
  output?: unknown;
  artifactRefs?: string[];
  sourceRuntime: string;
  usage?: {
    inputTokens?: number;
    outputTokens?: number;
    estimatedCost?: number;
    elapsedMs?: number;
  };
  warnings: string[];
  verificationState: "unverified" | "passed" | "failed";
}
```

## Required adapter operations

- `discoverCapabilities()`
- `healthCheck()`
- `execute(task)`
- `getRun(runId)`
- `cancel(runId)`
- `getUsage(runId)`
- `shutdown()`

## Adapter isolation requirements

- Run external processes with a dedicated service identity.
- Work only in an assigned workspace.
- Use read-only file access by default.
- Use explicit output/artifact directories.
- Set CPU, memory, process-count and wall-time limits where the OS/runtime supports them.
- Deny network destinations by default; allowlist only required endpoints.
- Require explicit permission for file writes, browser actions and shell commands.
- No access to the DAZY database directly; use adapter APIs.
- Never expose DAZY's master API keys to a child process.
- Keep secrets in server-side credential references.
- Capture sanitized stdout/stderr and correlation IDs.
- Terminate runaway child processes after graceful cancellation timeout.
- Do not run untrusted repository scripts on the host.

## Nanobot adapter
First evaluate Python SDK / library integration. If embedding is not appropriate, use a separately managed gateway with explicit lifecycle and one process. Disable duplicate WebUI and duplicate scheduled tasks if DAZY already owns those capabilities. Agree on memory ownership before sharing user facts.

## OpenManus adapter
Launch only for a delegated complex task. Disable unused browser, chart and multi-agent extras. Run in a separate virtual environment and bounded process. Return structured output.

## AgenticSeek adapter
Optional isolated runtime. Prefer remote or separate machine for local LLM and browser-heavy jobs. Do not package source into a proprietary combined binary without GPL review.

## n8n adapter
Connect to user-owned n8n URL using API/webhook credential. Test reachability, authentication and a harmless test workflow. Store endpoint and secret reference only. Do not run a local n8n container by default.

## Failure behavior
- If runtime unhealthy, mark unavailable/degraded and do not show green status.
- Retry transient failures only with bounded exponential backoff.
- Never retry destructive actions without checking idempotency.
- Fallback only when task capabilities and permissions match.
- External runtime failure must not crash the DAZY primary backend.
