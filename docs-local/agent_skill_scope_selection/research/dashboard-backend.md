# Dashboard ↔ Backend Interaction: Agent/Skill Configuration

**Research Date:** 2026-02-28
**Researcher:** dashboard-researcher (scope-abstraction-research team)
**Codebase Branch:** ui-agents-skills-config

---

## Executive Summary

The claude-mpm dashboard is a SvelteKit application that communicates with a Python/aiohttp backend via REST API and Socket.IO. It provides a full CRUD interface for deploying/undeploying agents and skills. **Critically, scope (project vs. user) is completely absent from the dashboard UI and hardcoded to `ConfigScope.PROJECT` in the backend API handlers.** The `ConfigScope` enum and resolution functions exist but are never exposed to the frontend.

---

## Dashboard Component Inventory

### Location
`src/claude_mpm/dashboard-svelte/` — SvelteKit application

### Main Entry Points
| File | Role |
|------|------|
| `src/routes/+page.svelte` | Root page; hosts all tabs (Events, Tools, Files, Agents, Config), Socket.IO config_event subscription |
| `src/routes/+layout.svelte` | App shell/layout wrapper |

### Configuration Components (`src/lib/components/config/`)

| Component | Purpose |
|-----------|---------|
| `ConfigView.svelte` | Main container; dual-panel layout (left=list, right=detail); tab host for Agents / Skills / Sources / Skill Links |
| `AgentsList.svelte` | Lists deployed + available agents; deploy/undeploy buttons; search, sort, category grouping |
| `SkillsList.svelte` | Lists deployed + available skills; deploy/undeploy buttons; toolchain grouping; deployment mode badge |
| `AgentDetailPanel.svelte` | Right-panel detail for selected agent: metadata grid, skill chips, collaboration links, deploy/undeploy |
| `SkillDetailPanel.svelte` | Right-panel detail for selected skill: full metadata, agent usage, content viewer |
| `AgentSkillPanel.svelte` | Skill panel within agent detail context |
| `AgentFilterBar.svelte` | Filter dropdowns for agents (category, status, resource tier) |
| `SkillFilterBar.svelte` | Filter dropdowns for skills (toolchain, status) |
| `SourcesList.svelte` | Source management UI; sync triggers |
| `SourceForm.svelte` | Add/edit source form |
| `SkillLinksView.svelte` | Skill-to-agent linkage visualization |
| `ModeSwitch.svelte` | Modal to switch skill deployment mode (selective/full/user_defined) |
| `AutoConfigPreview.svelte` | Preview modal for auto-configuration |
| `DeploymentPipeline.svelte` | Pipeline visualization during auto-config |
| `SyncProgress.svelte` | Source sync progress indicator |
| `ValidationPanel.svelte` | Config validation issues panel |
| `ValidationIssueCard.svelte` | Individual validation issue display |
| `SkillChip.svelte` / `SkillChipWithStatus.svelte` / `SkillChipList.svelte` | Inline skill representation with deploy status |

### Shared Components (`src/lib/components/shared/`)
Reusable primitives: `Chip`, `Badge`, `Modal`, `ConfirmDialog`, `Toast`, `PaginationControls`, `ProgressBar`, `SearchInput`, `VersionBadge`, `HighlightedText`, `MetadataGrid`, `CollapsibleSection`, `EmptyState`, etc.

### State Management
| Store | File | Contents |
|-------|------|---------|
| `projectSummary` | `config.svelte.ts` | Counts of deployed agents/skills/sources, deployment_mode |
| `deployedAgents` | `config.svelte.ts` | Array of DeployedAgent |
| `availableAgents` | `config.svelte.ts` | Array of AvailableAgent |
| `deployedSkills` | `config.svelte.ts` | Array of DeployedSkill |
| `availableSkills` | `config.svelte.ts` | Array of AvailableSkill |
| `configSources` | `config.svelte.ts` | Array of ConfigSource |
| `configLoading` | `config.svelte.ts` | Per-resource loading booleans |
| `configErrors` | `config.svelte.ts` | Last 5 errors |
| `syncStatus` | `config.svelte.ts` | Per-source sync state |
| `mutating` | `config.svelte.ts` | Global mutation in-progress flag |
| `configSelectedAgent` | `config.svelte.ts` | Shared selection (syncs left/right panels) |
| `configSelectedSkill` | `config.svelte.ts` | Shared selection |
| `configSelectedSource` | `config.svelte.ts` | Shared selection |
| `configActiveSubTab` | `config.svelte.ts` | Active sub-tab |
| `socketStore` | `socket.svelte.ts` | Socket.IO connection, events, streams, working directory |

---

## API Calls Made by the Dashboard

All calls use base `API_BASE = '/api/config'`. Backend is aiohttp running at `localhost:8765`.

### Read Endpoints (GET)

| Endpoint | Purpose | Called When |
|----------|---------|-------------|
| `GET /api/config/project/summary` | Agent/skill/source counts + deployment mode | On tab open, after mutations |
| `GET /api/config/agents/deployed` | List deployed agents with enriched metadata | On tab open, after deploy/undeploy |
| `GET /api/config/agents/available` | List available agents from sources | On tab open (deferred), after deploy/undeploy |
| `GET /api/config/skills/deployed` | List deployed skills with manifest enrichment | On tab open (deferred), after deploy/undeploy |
| `GET /api/config/skills/available` | List available skills from manifest | On tab open (deferred), after deploy/undeploy |
| `GET /api/config/sources` | List configured agent/skill sources | On tab open, after source mutations |
| `GET /api/config/agents/{name}/detail` | Full agent metadata (skills, dependencies, knowledge) | On agent selection (client-cached 50 entries) |
| `GET /api/config/skills/{name}/detail` | Full skill metadata (content, tokens, references) | On skill selection (client-cached 50 entries) |
| `GET /api/config/skill-links/` | Skill-to-agent linkage map | Skill Links sub-tab |
| `GET /api/config/validate` | Config validation issues | ValidationPanel |
| `GET /api/config/skills/deployment-mode` | Current deployment mode | ModeSwitch component |
| `GET /api/config/active-sessions` | Check for active Claude Code sessions | After every deploy/undeploy |
| `GET /api/working-directory` | Server's CWD | On Socket.IO connect |

### Mutation Endpoints (POST/PUT/PATCH/DELETE)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/config/agents/deploy` | Deploy single agent; body: `{agent_name, source_id?, force?}` |
| `DELETE` | `/api/config/agents/{name}` | Undeploy agent |
| `POST` | `/api/config/agents/deploy-collection` | Batch deploy agents; body: `{agent_names[], source_id?, force?}` |
| `POST` | `/api/config/skills/deploy` | Deploy skill; body: `{skill_name, mark_user_requested?, force?}` |
| `DELETE` | `/api/config/skills/{name}` | Undeploy skill |
| `PUT` | `/api/config/skills/deployment-mode` | Switch mode; body: `{mode, preview?, confirm?, skills?}` |
| `POST` | `/api/config/sources/agent` | Add agent source |
| `POST` | `/api/config/sources/skill` | Add skill source |
| `PATCH` | `/api/config/sources/{type}?id=...` | Update source |
| `DELETE` | `/api/config/sources/{type}?id=...` | Remove source |
| `POST` | `/api/config/sources/{type}/sync?id=...` | Sync single source (async, 202) |
| `POST` | `/api/config/sources/sync-all` | Sync all sources |
| `POST` | `/api/config/auto-configure/detect` | Detect project toolchain |
| `POST` | `/api/config/auto-configure/preview` | Preview auto-configuration |
| `POST` | `/api/config/auto-configure/apply` | Apply auto-configuration (async, 202) |

---

## Data Flow Diagram (Text)

```
User clicks "Deploy" on an agent in AgentsList
         |
         v
AgentsList.svelte calls handleDeploy(agent)
         |
         v
deployAgent(agent.agent_id) [config.svelte.ts store function]
         |
         v
POST /api/config/agents/deploy
  body: { agent_name: "engineer", force: false }
         |
         v
[Python aiohttp backend]
agent_deployment_handler.py::deploy_agent()
  1. validate_safe_name(agent_name)
  2. agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())
     → <cwd>/.claude/agents/
  3. BackupManager.create_backup()
  4. OperationJournal.begin_operation()
  5. AgentDeploymentService.deploy_agent(agent_name, agents_dir)
     → copies .md file from cache → <cwd>/.claude/agents/engineer.md
  6. DeploymentVerifier.verify()
  7. OperationJournal.complete_operation()
  8. ConfigEventHandler.emit("agent_deployed") via Socket.IO
         |
         v
Response: { success: true, message: "...", agent_name: "...", verification: {...} }
         |
         v
store refetches: fetchDeployedAgents() + fetchAvailableAgents()
         |
         v
Stores update → Svelte reactivity → UI re-renders
         |
         v
Socket.IO "config_event" { operation: "agent_deployed" }
         |
         v
handleConfigEvent() in +page.svelte
  → triggers additional store refetches if needed
```

### Real-time Update Flow
```
Backend file watcher detects external config change
    → emits "config_event" { operation: "external_change" } via Socket.IO
    → +page.svelte: sock.on('config_event', handleConfigEvent)
    → handleConfigEvent() → fetchSources() / fetchDeployedAgents() / etc.
    → stores update → UI re-renders
```

---

## Scope Handling in UI — CRITICAL FINDING: **Absent**

### What Exists
- `ConfigScope` enum (`PROJECT` / `USER`) in `src/claude_mpm/core/config_scope.py`
- `resolve_agents_dir(scope, project_path)` function that resolves to:
  - `PROJECT`: `<project>/.claude/agents/`
  - `USER`: `~/.claude/agents/`
- Similar `resolve_skills_dir()` and `resolve_archive_dir()` functions

### What the Dashboard Does
The dashboard UI has **zero scope-related elements**:
- No scope selector dropdown
- No "project" vs "user" toggle
- No scope badges on listed items
- No scope-based filtering

### What the Backend Does
Every API handler **hardcodes `ConfigScope.PROJECT`** and uses `Path.cwd()` as the project root:

```python
# agent_deployment_handler.py line 140
agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())
# → <server_cwd>/.claude/agents/
```

**The server's CWD is captured at startup time.** The dashboard cannot redirect operations to user scope (`~/.claude/agents/`) or to a different project directory.

### The `currentWorkingDirectory` Variable (Misleading Name)
The socket store tracks `currentWorkingDirectory` but this is **only used for event stream filtering** (to show events matching the current project). It is completely separate from config scope — it does not influence any API call to `/api/config/`.

---

## Frontend State Management for Configuration

### Architecture Pattern
Mixed Svelte 4/5 hybrid:
- **Svelte 4 writable stores** for global state (imported from `config.svelte.ts` using `writable`)
- **Svelte 5 runes** (`$state`, `$derived`, `$effect`, `$props`) within components

### Store Lifecycle
1. `ConfigView.svelte` mounts → calls `fetchAllConfig()` once
2. `fetchAllConfig()` fires parallel requests for summary + deployed agents + sources, then defers heavier requests (available agents, deployed/available skills)
3. Stores update reactively; components re-render
4. Mutations (`deployAgent`, `undeploySkill`, etc.) call `mutating.set(true)`, execute, then refetch affected stores
5. Socket.IO events (`config_event`) trigger additional refetches in response to external changes

### Client-Side Caching
- Detail panels cache API responses in `Map<string, DetailData>` with LRU eviction at 50 entries
- `invalidateAgentDetailCache(name)` / `invalidateSkillDetailCache(name)` called after deploy/undeploy
- No HTTP caching headers are used

### Cross-Panel State Synchronization
`ConfigView` is rendered **twice** (left panel = list, right panel = detail). Both instances share the same writable stores for selection state (`configSelectedAgent`, `configSelectedSkill`, etc.), enabling synchronized left↔right panel behavior without prop drilling.

---

## Integration Points Between Frontend and Backend

### 1. HTTP REST API
- Protocol: HTTP/1.1 fetch API (no axios, no GraphQL)
- All responses: `{ success: bool, data?: ..., error?: str, code?: str }`
- Error codes: `VALIDATION_ERROR`, `CONFLICT`, `SERVICE_ERROR`, `NOT_FOUND`

### 2. Socket.IO (Real-time)
- Connection: `io('http://localhost:8765', { transports: ['polling', 'websocket'] })`
- Config-relevant event: `config_event` — structured as `{ type, operation, entity_type, entity_id, status, data, timestamp }`
- Operations streamed: source CRUD, sync progress, agent deploy/undeploy, skill deploy/undeploy, auto-config progress/completion
- Auto-config results delivered exclusively via Socket.IO (HTTP returns only job_id, HTTP 202)

### 3. Feature Flags
`src/lib/config/features.ts` controls UI feature rollout:
```typescript
RICH_DETAIL_PANELS: true    // Collapsible sections, metadata grids
FILTER_DROPDOWNS: true      // Category/status/toolchain filter dropdowns
VERSION_MISMATCH: true      // Deployed vs. available version comparison
COLLABORATION_LINKS: true   // Clickable agent collaboration links
SKILL_LINKS_MERGE: true     // Skill links merged into detail panels
SEARCH_ENHANCEMENTS: true   // Search text highlighting
```

---

## Secondary Dashboard (d2/)

There is a second, simpler Svelte app at `src/claude_mpm/d2/` with components:
- `App.svelte`, `Header.svelte`, `MainContent.svelte`, `Sidebar.svelte`, `EventsTab.svelte`

This appears to be an older/alternative dashboard focused on event viewing only. It has **no config management components**.

---

## Key Findings for Scope Abstraction

### Finding 1: Scope is Invisible to the UI
The entire config UI operates on a single implicit scope — the project scope, determined by the server's CWD. There are no API fields, data properties, or UI elements that distinguish project-scoped from user-scoped items.

### Finding 2: `ConfigScope` Infrastructure is Ready
`config_scope.py` already defines both scopes and path resolution functions. The gap is in the API layer (all handlers hardcode `ConfigScope.PROJECT`) and the frontend (no scope field in API responses or requests).

### Finding 3: Adding Scope Would Require
1. **Backend**: Pass `scope` parameter through API request body/query string; use it in `resolve_agents_dir()` / `resolve_skills_dir()` calls
2. **Frontend API types**: Add `scope: 'project' | 'user'` fields to `DeployedAgent`, `AvailableAgent`, `DeployedSkill`, `AvailableSkill`
3. **Frontend store functions**: Add `scope` param to `deployAgent()`, `undeployAgent()`, `deploySkill()`, `undeploySkill()`
4. **Frontend UI**: Add scope selector (e.g., tab or dropdown) in ConfigView; display scope badge on list items

### Finding 4: Auto-Config Uses project_path but not scope
`detectToolchain(project_path?)` and `previewAutoConfig(project_path?)` accept an optional `project_path` parameter (exposed in API call bodies), but the UI never passes it — it always uses the server's CWD.

### Finding 5: Socket.IO Config Events Carry No Scope
`config_event` messages don't include scope metadata. If scope is added, event routing would need to include it so the right stores update.

---

## Appendix: Backend Route Registration Summary

```
config_routes.py (read-only):      11 routes under /api/config/
config_sources.py:                  7 routes under /api/config/sources/
agent_deployment_handler.py:        5 routes under /api/config/agents/
skill_deployment_handler.py:        4 routes under /api/config/skills/
autoconfig_handler.py:              3 routes under /api/config/auto-configure/
─────────────────────────────────────────────────────────────────
Total:                             30 config API routes
```

Backend framework: aiohttp (async Python). Routes registered by calling `register_*_routes(app)` from `UnifiedMonitorServer._setup_http_routes()`.
