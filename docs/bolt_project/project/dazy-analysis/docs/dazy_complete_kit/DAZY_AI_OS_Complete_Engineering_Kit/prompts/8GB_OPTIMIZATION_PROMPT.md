# Prompt — 8 GB RAM / CPU / GPU / Storage Optimization

My PC has 8 GB RAM and runs DAZY web + desktop. RAM, storage, CPU and GPU usage are high; the PC is slow and builds take too long.

Audit first. Record baseline process RAM, total/free memory, CPU, GPU/VRAM, project folder sizes, Docker/WSL, dependency caches and build duration. Do not invent values.

Then:
- Ensure web and desktop use one shared backend, guarded by a single-instance lock.
- Use one shared bounded worker pool; concurrency one by default.
- Treat agent identities as logical roles, not one OS process each.
- Prefer configured hosted model APIs; local models disabled by default.
- Start OpenManus/AgenticSeek only when delegated; n8n remote only.
- Nanobot at most one managed process if enabled; avoid its separate WebUI/gateway where DAZY already provides these.
- Lazy-load 3D; pause when hidden; adaptive resolution, instancing, resource disposal, 2D fallback.
- Close idle MCP/runtime sessions.
- Use scoped/paginated memory retrieval and bounded caches.
- Rotate/compress logs.
- Scan storage before proposing cleanup; require approval for deletion.
- Reuse DB/queue/cache instances.
- Profile build steps, use existing package manager and incremental builds.
- Add resource-pressure policies and status UI.
- Preserve task state; never kill database or delete data to free memory.
- Test before/after under equivalent workload.

Report actual measurements, files changed, tests and remaining bottlenecks.
