# Main UI Specification — DAZY Command Center + Repo Radar

## 1. Visual style
- Professional dark interface with restrained cyan/blue/violet highlights.
- Clean typography, dense but readable information hierarchy.
- Responsive layout for 8 GB desktop hardware; avoid excessive blur, huge shadows and always-running canvas effects.
- CSS/SVG/Canvas 2D for lightweight charts; WebGL only for the 3D page.
- The UI must remain fully usable with 3D disabled.

## 2. Main dashboard layout

### Header
Left: DAZY icon/name and environment badge.
Center: global search / command palette.
Right: backend state, local time/timezone, notification/approval bell, settings, user avatar and **Tarik** profile name.

Identity greeting:
- “Good morning, Tarik” / “Good afternoon, Tarik” based on user timezone.
- The name is read from `/api/me` or the existing canonical authenticated profile endpoint.
- No static “John” or “Alex”.

### Left navigation
- Command Center
- Daily Briefing
- Live 3D Brain
- Primary Brain
- Secondary Runtimes
- Workers & Co-workers
- Tasks & Automations
- Memory
- LLMs & Models
- APIs & Connections
- Tools & Skills
- MCP Servers
- Repositories
- **Repo Radar**
- Knowledge Library
- Resource Monitor
- Logs & Traces
- Diagnostics
- Auto Repair
- Security & Permissions
- Settings
- Desktop Controls

### Top metric cards
- Active workers / worker budget.
- Running and queued jobs.
- Model/provider health.
- Integrations connected / degraded.
- RAM usage and available memory.
- CPU/GPU/disk pressure.
- Tokens and estimated cost with time period.

### Main center
- Optional compact live graph preview; do not run an always-animated 3D canvas on the home route.
- Task activity timeline.
- Active task and worker handoffs.
- Daily priorities and due items.

### Right rail
- System health.
- Recent activity.
- Upcoming events.
- Failed connections.
- Approval-required repairs.
- Resource pressure warnings.

### Lower workspace panels
- Connected integrations.
- Tasks and workflow statuses.
- Memory access activity.
- Recent traces.
- Repo Radar recommendations.
- Usage and cost charts.

## 3. Repo Radar — first-class main UI panel

Place a card on the Command Center titled **Repo Radar — Discover useful projects**.

It contains:
- Search GitHub field.
- Paste repository URL.
- Optional source/watchlist management.
- “Evaluate repository” action.
- Recently discovered list.
- Filters: agent framework, personal assistant, browser automation, workflow engine, MCP, memory, skills, developer tools, voice.
- Source and last-checked date.

Each repository result card:
- Repository name and owner.
- Short description.
- Official link.
- License label.
- Maintenance status.
- Last commit/release.
- Language and dependency summary.
- Required Python/Node/Docker/model/browser components.
- Capabilities matched to DAZY gaps.
- Resource classification (light / moderate / heavy / unknown, based on evidence).
- Security/license warnings.
- Proposed integration type.
- Actions: Inspect, Compare, Add to Watchlist, Create Adapter Plan, Sandbox Test (approval).

Do not display a fabricated “RAM 200 MB” type metric. If not measured, say “Not benchmarked”.

## 4. Repo Radar workflow
Input URL/search → fetch repo metadata → inspect README/license/manifest → analyze dependency graph → check activity and archived state → inspect security signals → compare against DAZY registry → create evaluation report → ask approval for sandbox clone/test → generate adapter plan → manual/approved installation.

Repo Radar is a research and evaluation system, not an automatic arbitrary code installer.

## 5. Identity/Profile UI
Top-right profile dropdown:
- Avatar.
- Display name: Tarik.
- Account identity provider.
- Email (only if verified and available).
- Timezone: Asia/Kolkata (editable).
- Preferences.
- Sign out.

Settings → Personalization:
- Display name editor.
- Greeting preview.
- Avatar.
- Locale/timezone.
- Pronouns optional and blank by default.
- Save and reload confirmation.

## 6. Live Brain page
- 3D graph is full-page and lazy loaded.
- Nodes: Primary Brain, selected secondary runtime, workers, models, memory, tool gateway, MCPs, APIs, database and task queue.
- Edges: configured connections vs observed calls should have different visual styles.
- Node selection opens inspector: health, owner, capability, current task, dependencies, permissions, last event, errors, memory/cost.
- Playback/replay reads event history.
- Search and filters.
- 2D graph fallback.
- No fake particles when there is no event data.

## 7. Resource Monitor panel
Show process-level RAM, CPU, GPU/VRAM if supported, disk usage and build cache sizes. Show data source, timestamp, sampling interval and permission limitations.

Provide profiles:
- Low Resource (default on 8 GB).
- Balanced.
- High Performance (warn user before activation).

## 8. UI interaction and accessibility
- Keyboard navigation.
- Search command palette.
- Visible loading, empty, offline, stale and error states.
- Reduced-motion option.
- WebGL unsupported fallback.
- No critical controls represented by animation-only elements.
- Confirm emergency stop and destructive operations.
