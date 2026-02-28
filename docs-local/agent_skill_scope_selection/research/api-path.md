# API Configuration Path Research

**Research Date:** 2026-02-28
**Branch:** ui-agents-skills-config
**Researcher:** api-researcher

---

## Overview

The claude-mpm API serves a web dashboard and provides HTTP endpoints for viewing and managing agents/skills configuration. The API is implemented using `aiohttp` and runs as a `UnifiedMonitorServer` daemon (port 8765). All configuration endpoints live under `/api/config/`.

**Critical Finding:** The API currently **hard-codes PROJECT scope throughout** — there is no scope parameter in any request. All operations resolve to `<cwd>/.claude/agents/` and `<cwd>/.claude/skills/`.

---

## API Endpoint Inventory

### Framework: aiohttp + Socket.IO
- Server: `src/claude_mpm/services/monitor/server.py` (`UnifiedMonitorServer`)
- Routes registered in `_setup_http_routes()` (line ~1428)
- All async via `asyncio.to_thread()` for blocking service calls

### Route Registration (server.py lines 1428–1463)

```python
register_config_routes(self.app, server_instance=self)           # Phase 1: read-only
register_source_routes(self.app, ...)                           # Phase 2: source mutations
register_agent_deployment_routes(self.app, ...)                 # Phase 3: agent deploy/undeploy
register_skill_deployment_routes(self.app, ...)                 # Phase 3: skill deploy/undeploy
register_autoconfig_routes(self.app, ...)                       # Phase 3: auto-configure
```

---

### Phase 1 (Read-Only): `config_routes.py::register_config_routes`

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/api/config/project/summary` | `handle_project_summary` | High-level config counts |
| GET | `/api/config/agents/deployed` | `handle_agents_deployed` | List project-deployed agents |
| GET | `/api/config/agents/available` | `handle_agents_available` | Paginated list from cache |
| GET | `/api/config/skills/deployed` | `handle_skills_deployed` | List project-deployed skills |
| GET | `/api/config/skills/available` | `handle_skills_available` | Paginated list from sources |
| GET | `/api/config/sources` | `handle_sources` | Agent + skill sources |
| GET | `/api/config/agents/{name}/detail` | `handle_agent_detail` | Full agent frontmatter |
| GET | `/api/config/skills/{name}/detail` | `handle_skill_detail` | Full skill metadata |
| GET | `/api/config/skill-links/` | `handle_skill_links` | Bidirectional skill-agent map |
| GET | `/api/config/skill-links/agent/{agent_name}` | `handle_skill_links_agent` | Per-agent skills |
| GET | `/api/config/validate` | `handle_validate` | Configuration validation |

### Phase 3 (Mutations): `agent_deployment_handler.py::register_agent_deployment_routes`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/config/agents/deploy` | Deploy single agent from cache to project |
| DELETE | `/api/config/agents/{agent_name}` | Undeploy agent (remove file) |
| POST | `/api/config/agents/deploy-collection` | Batch deploy multiple agents |
| GET | `/api/config/agents/collections` | List agent source collections |
| GET | `/api/config/active-sessions` | Detect active Claude Code sessions |

### Phase 3 (Mutations): `skill_deployment_handler.py::register_skill_deployment_routes`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/config/skills/deploy` | Deploy single skill from cache |
| DELETE | `/api/config/skills/{skill_name}` | Undeploy skill (remove directory) |
| GET | `/api/config/skills/deployment-mode` | Get current deployment mode |
| PUT | `/api/config/skills/deployment-mode` | Switch deployment mode (two-step) |

### Phase 3 (Mutations): `autoconfig_handler.py::register_autoconfig_routes`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/config/auto-configure/detect` | Detect project toolchain |
| POST | `/api/config/auto-configure/preview` | Preview recommended config |
| POST | `/api/config/auto-configure/apply` | Async auto-configure (returns 202) |

---

## Request/Response Schemas

### POST `/api/config/agents/deploy`

**Request:**
```json
{
  "agent_name": "string (required)",
  "source_id": "string (optional, currently unused)",
  "force": "bool (optional, default: false)"
}
```

**Response 201:**
```json
{
  "success": true,
  "message": "Agent 'X' deployed successfully",
  "agent_name": "X",
  "backup_id": "2025-01-15T10-30-00",
  "verification": {
    "passed": true,
    "timestamp": "2025-01-15T10:30:00+00:00",
    "checks": [
      {"check": "file_exists", "passed": true, "path": "/proj/.claude/agents/X.md", "details": ""},
      {"check": "file_size", "passed": true, "path": "...", "details": "Size: 1234 bytes"},
      {"check": "yaml_frontmatter", "passed": true, "path": "...", "details": ""},
      {"check": "required_fields", "passed": true, "path": "...", "details": ""}
    ]
  },
  "active_sessions_warning": false,
  "active_sessions": []
}
```

**Error 400:** `{"success": false, "error": "...", "code": "VALIDATION_ERROR"}`
**Error 409:** `{"success": false, "error": "...", "code": "CONFLICT"}`
**Error 500:** `{"success": false, "error": "...", "code": "DEPLOY_FAILED"}`

---

### DELETE `/api/config/agents/{agent_name}`

**No request body.**

**Response 200:**
```json
{
  "success": true,
  "message": "Agent 'X' undeployed",
  "agent_name": "X",
  "backup_id": "...",
  "verification": {"passed": true, "checks": [{"check": "file_removed", ...}]}
}
```

**Error 403:** Core agent protected (`CORE_AGENT_PROTECTED`)
**Error 404:** Agent not deployed (`NOT_FOUND`)

---

### POST `/api/config/skills/deploy`

**Request:**
```json
{
  "skill_name": "string (required)",
  "collection": "string (optional)",
  "mark_user_requested": "bool (optional, default: false)",
  "force": "bool (optional, default: false)"
}
```

**Response 201:**
```json
{
  "success": true,
  "message": "Skill 'X' deployed successfully",
  "skill_name": "X",
  "backup_id": "...",
  "deploy_result": {"deployed_count": 1, "deployed_skills": ["X"]},
  "verification": {"passed": true, "checks": [...]}
}
```

**Error 423:** Config file locked (`LOCK_TIMEOUT`)

---

### PUT `/api/config/skills/deployment-mode`

**Two-step protocol:**

Step 1 - Preview (dry run):
```json
{"mode": "selective", "preview": true}
```
Step 2 - Confirm:
```json
{"mode": "selective", "confirm": true}
```

**Response (preview=true):**
```json
{
  "success": true,
  "preview": true,
  "target_mode": "selective",
  "impact": {
    "would_remove": ["skill-a", "skill-b"],
    "would_keep": ["skill-c"],
    "remove_count": 2,
    "keep_count": 1
  }
}
```

---

### GET `/api/config/agents/deployed`

**Response:**
```json
{
  "success": true,
  "agents": [
    {
      "name": "Engineer",
      "agent_id": "engineer",
      "description": "...",
      "version": "1.2.0",
      "is_core": true,
      "path": "/proj/.claude/agents/engineer.md"
    }
  ],
  "total": 7
}
```

---

## Code Flow: HTTP Request → File System

### Agent Deploy (`POST /api/config/agents/deploy`)

```
HTTP POST
  │
  ▼
deploy_agent() handler  [agent_deployment_handler.py:121]
  │
  ├── validate_safe_name(agent_name, "agent")  [validation.py]
  │     └── regex: ^[a-zA-Z0-9][a-zA-Z0-9_-]*$
  │
  ├── resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())
  │     └── → Path.cwd() / ".claude" / "agents"  [HARDCODED PROJECT SCOPE]
  │
  ├── validate_path_containment(agent_path, agents_dir)
  │
  ├── Conflict check: agent_path.exists() and not force
  │
  └── asyncio.to_thread(_deploy_sync):
        │
        ├── BackupManager.create_backup("deploy_agent", "agent", agent_name)
        │     └── copies agents_dir + skills_dir + config_dir
        │         → ~/.claude-mpm/backups/<timestamp>/
        │
        ├── OperationJournal.begin_operation(...)
        │
        ├── agents_dir.mkdir(parents=True, exist_ok=True)
        │
        ├── AgentDeploymentService.deploy_agent(agent_name, agents_dir, force_rebuild)
        │     └── **WRITES FILE: agents_dir/{agent_name}.md**
        │
        ├── DeploymentVerifier.verify_agent_deployed(agent_name)
        │     └── checks: file exists, size, YAML frontmatter, required fields
        │
        └── OperationJournal.complete_operation(op_id)
              │
              ▼
        detect_active_claude_sessions()
        emit_config_event("agent_deployed")  [Socket.IO]
        HTTP 201
```

### Agent Undeploy (`DELETE /api/config/agents/{agent_name}`)

```
HTTP DELETE
  │
  ▼
undeploy_agent() handler  [agent_deployment_handler.py:240]
  │
  ├── validate_safe_name()
  ├── CORE_AGENTS check: ["engineer","research","qa","web-qa","documentation","ops","ticketing"]
  ├── resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())
  ├── validate_path_containment()
  ├── Check agent_path.exists() → 404 if not
  │
  └── asyncio.to_thread(_undeploy_sync):
        ├── BackupManager.create_backup(...)
        ├── OperationJournal.begin_operation(...)
        ├── agent_path.unlink()  **DELETES FILE**
        ├── DeploymentVerifier.verify_agent_undeployed()
        └── OperationJournal.complete_operation()
              │
              ▼
        emit_config_event("agent_undeployed")
        HTTP 200
```

### Skill Deploy (`POST /api/config/skills/deploy`)

```
HTTP POST
  │
  ▼
deploy_skill() handler  [skill_deployment_handler.py:131]
  │
  ├── validate_safe_name(skill_name, "skill")
  │
  └── asyncio.to_thread(_deploy_sync):
        ├── BackupManager.create_backup(...)
        ├── OperationJournal.begin_operation(...)
        ├── SkillsDeployerService.deploy_skills(
        │       collection, [skill_name], force, selective=False
        │   )
        │   └── **WRITES DIRECTORY: <skills_dir>/<skill_name>/**
        │       (SkillsDeployerService defaults to ~/.claude/skills/ OR
        │        project .claude/skills/ — see scope analysis below)
        │
        ├── If mark_user_requested:
        │     config_file_lock(config_path)
        │     Write to <cwd>/.claude-mpm/configuration.yaml
        │     └── skills.user_defined: [skill_name]
        │
        ├── DeploymentVerifier.verify_skill_deployed(skill_name)
        │     └── checks: directory exists, has files
        │
        └── OperationJournal.complete_operation()
              │
              ▼
        ConfigFileWatcher.update_mtime(config_path)
        emit_config_event("skill_deployed")
        HTTP 201
```

---

## Scope Assumptions: Where PROJECT is Hard-Coded

### Summary Table

| Location | Code | Hard-coded path |
|----------|------|-----------------|
| `agent_deployment_handler.py:140` | `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` | `<cwd>/.claude/agents/` |
| `agent_deployment_handler.py:258` | `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` | `<cwd>/.claude/agents/` |
| `agent_deployment_handler.py:372` | `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` | `<cwd>/.claude/agents/` |
| `config_routes.py:43` | `Path.cwd() / ".claude" / "agents"` | `<cwd>/.claude/agents/` |
| `config_routes.py:258` | `Path.cwd() / ".claude" / "skills"` | `<cwd>/.claude/skills/` |
| `config_routes.py:441` | `Path.cwd() / ".claude" / "skills"` | `<cwd>/.claude/skills/` |
| `config_routes.py:523` | `Path.cwd() / ".claude" / "skills"` | `<cwd>/.claude/skills/` |
| `config_routes.py:834` | `Path.cwd() / ".claude" / "skills"` | `<cwd>/.claude/skills/` |
| `skill_deployment_handler.py:107` | `Path.cwd() / ".claude-mpm" / "configuration.yaml"` | `<cwd>/.claude-mpm/configuration.yaml` |
| `autoconfig_handler.py:535` | `resolve_agents_dir(ConfigScope.PROJECT, project_path)` | `<project_path>/.claude/agents/` |
| `autoconfig_handler.py:576` | `resolve_skills_dir(ConfigScope.PROJECT, project_path)` | `<project_path>/.claude/skills/` |
| `backup_manager.py:94` | `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` | `<cwd>/.claude/agents/` |
| `deployment_verifier.py:63` | `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` | `<cwd>/.claude/agents/` |
| `deployment_verifier.py:66` | `resolve_skills_dir()` | defaults to project scope |

### The `ConfigScope` Abstraction Already Exists

`core/config_scope.py` already defines scope-aware resolution:

```python
class ConfigScope(str, Enum):
    PROJECT = "project"   # → <cwd>/.claude/agents/
    USER = "user"         # → ~/.claude/agents/

def resolve_agents_dir(scope: ConfigScope, project_path: Path) -> Path:
    if scope == ConfigScope.PROJECT:
        return project_path / ".claude" / "agents"
    return Path.home() / ".claude" / "agents"

def resolve_skills_dir(scope: ConfigScope = ConfigScope.PROJECT, ...) -> Path:
    if scope == ConfigScope.PROJECT:
        return (project_path or Path.cwd()) / ".claude" / "skills"
    return Path.home() / ".claude" / "skills"
```

**The infrastructure is already scope-aware; the API layer never passes `ConfigScope.USER`.**

---

## Key Services and Their Roles

### `AgentDeploymentService`
- `src/claude_mpm/services/agents/deployment/agent_deployment.py`
- Called from deploy handlers with `agents_dir` as explicit parameter
- Accepts target directory; does NOT itself enforce scope
- **Makes the actual file write**

### `AgentManager`
- `src/claude_mpm/services/agents/management/agent_management_service.py`
- Used for reading/listing deployed agents
- `project_dir` defaults to `<cwd>/.claude/agents/` via `get_path_manager()`
- Supports `location="project"` or `location="framework"`
- **No `location="user"` support currently**

### `SkillsDeployerService`
- `src/claude_mpm/services/skills_deployer.py`
- Used for skill deployment; accepts optional `skills_dir` override
- Default skills dir: depends on service implementation (not read in detail)
- Read endpoints consistently use `Path.cwd() / ".claude" / "skills"`

### `BackupManager`
- `src/claude_mpm/services/config_api/backup_manager.py`
- Pre-operation safety: backup → journal → execute → verify → prune
- Hardcodes PROJECT scope for agents and user-level for skills
- `BACKUP_ROOT = ~/.claude-mpm/backups/`

### `DeploymentVerifier`
- `src/claude_mpm/services/config_api/deployment_verifier.py`
- Post-operation checks: file exists, valid frontmatter, required fields (agents); dir exists, has files (skills)
- Initialized with `default_agents_dir = resolve_agents_dir(PROJECT, cwd())`

### `OperationJournal`
- `src/claude_mpm/services/config_api/operation_journal.py`
- Wraps all operations with begin/complete/fail journal entries

### `ConfigEventHandler` (Socket.IO)
- Emits real-time events to dashboard clients after operations
- Events: `agent_deployed`, `agent_undeployed`, `skill_deployed`, `skill_undeployed`, `mode_switched`

---

## Safety Protocol

Every destructive API operation follows this pattern:
```
backup → journal → execute → verify → prune_old_backups
```

Error handling: `journal.fail_operation(op_id, str(exc))` on any exception.

Locking: Skill configuration file writes use `config_file_lock(config_path)` (prevents concurrent writes). Returns HTTP 423 on timeout.

---

## Key Files

| File | Lines | Role |
|------|-------|------|
| `src/claude_mpm/services/monitor/server.py` | ~1500 | `UnifiedMonitorServer`, route registration at line 1428 |
| `src/claude_mpm/services/monitor/config_routes.py` | ~1070 | 11 read-only GET endpoints |
| `src/claude_mpm/services/config_api/agent_deployment_handler.py` | 526 | 5 agent deploy/undeploy endpoints |
| `src/claude_mpm/services/config_api/skill_deployment_handler.py` | 587 | 4 skill deploy/undeploy endpoints |
| `src/claude_mpm/services/config_api/autoconfig_handler.py` | 667 | 3 auto-configure endpoints |
| `src/claude_mpm/core/config_scope.py` | 102 | `ConfigScope` enum + `resolve_*` functions |
| `src/claude_mpm/services/config_api/backup_manager.py` | 380 | Pre-operation backups |
| `src/claude_mpm/services/config_api/deployment_verifier.py` | 382 | Post-operation verification |
| `src/claude_mpm/services/config_api/validation.py` | 79 | Input validation (path traversal) |
| `src/claude_mpm/services/agents/management/agent_management_service.py` | ~350 | CRUD for agent files |

---

## Scope-Readiness Assessment

### What Exists
- `ConfigScope.PROJECT` and `ConfigScope.USER` enum values in `core/config_scope.py`
- `resolve_agents_dir(scope, project_path)` and `resolve_skills_dir(scope, project_path)` functions
- `AgentDeploymentService.deploy_agent(agent_name, agents_dir, ...)` accepts `agents_dir` as parameter

### What's Missing
1. **No `scope` parameter in any API request** — nothing in the HTTP request schema for scope selection
2. **`AgentManager` has no USER location** — only `"project"` and `"framework"` locations
3. **`BackupManager` hardcodes PROJECT for agents** — user-scope backups not handled
4. **`DeploymentVerifier` defaults to PROJECT** — user-scope verification not handled
5. **Read endpoints always read from `Path.cwd() / ".claude"` paths** — no way to view user-scoped deployments

### Changes Needed for User Scope
1. Add `scope: "project" | "user"` to deploy/undeploy request bodies
2. Pass scope to `resolve_agents_dir()` and `resolve_skills_dir()`
3. Thread scope through `BackupManager`, `DeploymentVerifier`, and `AgentManager`
4. Add `location="user"` support to `AgentManager.list_agents()` and `list_agent_names()`
5. Update read endpoints to accept `?scope=project|user` query param

### Relative Ease of Change
- The `resolve_*` functions already accept scope → **path resolution is trivial**
- `AgentDeploymentService.deploy_agent()` already accepts `agents_dir` → **deployment is trivial**
- The main work is threading scope through the HTTP layer and service singletons

---

## Scope Assumptions in Detail

### The `_get_agent_manager()` Singleton Problem

```python
# config_routes.py:35-45
_agent_manager = None

def _get_agent_manager(project_dir: Optional[Path] = None):
    """Lazy singleton for AgentManager."""
    global _agent_manager
    if _agent_manager is None:
        agents_dir = project_dir or (Path.cwd() / ".claude" / "agents")
        _agent_manager = AgentManager(project_dir=agents_dir)
    return _agent_manager
```

**Problem:** The `AgentManager` is instantiated once per process with `project_dir = Path.cwd() / ".claude" / "agents"`. This means any call to `list_agents(location="project")` uses this hardcoded path. A user-scope `AgentManager` would require a separate singleton or stateless instantiation.

### The `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` Pattern

In deploy handlers, `Path.cwd()` is the working directory of the server process. The server starts with `cwd` set to the project directory being managed. This means `ConfigScope.PROJECT` + `Path.cwd()` = project's `.claude/agents/`. Switching to `ConfigScope.USER` would give `~/.claude/agents/` regardless of `Path.cwd()`.

---

## Summary: What the API Assumes

The API assumes:
1. **All operations are on the current project** (`Path.cwd()` is the project root)
2. **All deployments go to project scope** (`<cwd>/.claude/agents/`, `<cwd>/.claude/skills/`)
3. **All reads are from project scope** (same paths)
4. **There is only one scope** — no way to deploy to `~/.claude/agents/` via the API
5. **Skills config is always at `<cwd>/.claude-mpm/configuration.yaml`** — project config only

The abstraction for adding user scope is minimal at the path-resolution layer but requires threading through multiple singleton services and request schemas.
