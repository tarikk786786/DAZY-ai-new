# DAZY 8 GB Low-Resource Architecture

## 1. Objective
Retain DAZY's essential features while avoiding simultaneous heavyweight workloads. This is a workload policy, not a promise that every combination will fit into 8 GB. Measure on the actual PC.

## 2. Default profile

| Area | Default |
|---|---|
| Shared backend | One instance |
| Desktop | Thin Tauri shell connected to same backend |
| Worker pool | 1 concurrent job initially |
| Maximum initial concurrency | 2 only after measurements |
| Primary brain | One lightweight orchestrator |
| Secondary runtimes | Start on demand |
| LLM | Hosted API by default |
| Local model | Disabled by default |
| Nanobot | Optional, one managed instance |
| OpenManus | On-demand, one task |
| AgenticSeek | Disabled by default; remote preferred |
| n8n | External endpoint, not local service |
| MCP | Lazy connection / idle close |
| 3D brain | Lazy mount; no idle render loop |
| Memory | Scoped retrieval, paginated |
| Logs | Rotation, compression, retention |
| Database | Existing shared DB; no duplicates |

## 3. Resource pressure policy

Thresholds are configurable and must be based on available memory and host telemetry:
- Normal: no throttling.
- Soft pressure: reduce nonessential polling, pause repo scans and background consolidation.
- Elevated pressure: set worker concurrency to one, unload inactive 3D scene, close idle optional runtime sessions.
- Critical pressure: reject new heavy jobs, checkpoint/cancel nonessential work, show alert, preserve active data.
- Recovery: gradually resume paused work after sustained headroom.

Never kill the database, delete data or terminate active work abruptly just to hit a numeric target.

## 4. 3D performance
- Load Three.js route on demand.
- Home page shows a static/2D thumbnail.
- Pause requestAnimationFrame when hidden or idle.
- Cap to 30 FPS during activity; lower on pressure.
- Adaptive pixel ratio.
- Use InstancedMesh where practical.
- Reuse geometries, materials and textures.
- Dispose WebGL resources on unmount.
- Avoid continuously animated background particles.
- Limit graph nodes displayed at once; virtualize detail panels.
- 2D graph fallback if GPU/driver/WebGL is constrained.

## 5. Worker and model efficiency
- Logical agents do not equal operating-system processes.
- Use shared worker pool and task queue.
- Set per-task memory, CPU and wall-clock budgets where possible.
- Share provider clients and connection pools.
- Do not preload every model.
- Use hosted APIs where the user has configured them.
- Local model loading requires explicit selection and measurement.
- Use a semaphore to prevent multiple browser sessions.
- External runtimes start, execute and shut down with clear timeouts.

## 6. Storage controls
Implement a read-only scan first:
- node_modules / package stores.
- `.next`, `dist`, `build`, coverage.
- Python environments and caches.
- downloaded repositories.
- model files and model caches.
- Docker images/containers/build cache.
- application logs.
- browser caches.
- database data and backup directories.

Then present a cleanup plan with path, size, last modified time, purpose, safe-to-delete assessment and rollback. Require approval for deletion. Never automatically prune Docker volumes, databases, model files, user files or backups.

## 7. Build optimization
- Detect existing package manager from lockfiles; do not create a second lockfile.
- Use incremental TypeScript/compiler caches.
- Split heavy routes and 3D bundles.
- Avoid duplicate dependency versions.
- Reuse package/build caches.
- Avoid multiple dev servers and duplicate watchers.
- Build only changed packages during iteration, then run full CI before release.
- Inspect bundle size and slow build steps before changing tooling.

## 8. Suggested Windows diagnostic commands
Use the read-only script in `diagnostics/`. Do not run destructive cleanup commands automatically.

## 9. Verification
Record before/after:
- Total/free RAM and process working set.
- CPU over a defined observation window.
- GPU engine and dedicated/shared memory where supported.
- Disk usage by project folder.
- Container and WSL footprint.
- Cold and warm build time.
- 3D route active vs idle resource use.
- Worker task throughput and memory.
Use equivalent test conditions and report hardware/model/browser versions.
