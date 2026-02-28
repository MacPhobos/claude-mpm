# Abstraction Opportunities: CLI vs API Configuration Paths

**Research Date**: 2026-02-28
**Researcher**: abstraction-researcher agent
**Scope**: Shared concepts between `claude-mpm configure` CLI and `/api/config` endpoints

---

## Executive Summary

The CLI and API configuration paths share the same *intent* (deploy/undeploy agents and skills) but diverge significantly in their *safety mechanisms*, *scope handling*, and *underlying services*. A unified abstraction layer is feasible and would offer meaningful DRY gains, but requires resolving four structural mismatches before insertion.

**Key finding**: `core/config_scope.py` is the closest thing to a shared abstraction today. It should serve as the foundation for a unified layer.

---

## 1. System Map

### CLI Path

Entry: `claude-mpm configure` → `cli/commands/configure.py` → `ConfigureCommand`

Key components:
- **State tracking**: `cli/commands/agent_state_manager.py` → `SimpleAgentManager`
  Tracks agent enable/disable preference in `.claude-mpm/agent_states.json`
- **Path resolution**: `cli/commands/configure_paths.py` (pure functions)
  `get_config_directory(scope, project_dir)` → `.claude-mpm/`
  `get_agents_directory(scope, project_dir)` → `.claude-mpm/agents/`
- **Deploy mechanism**: `_deploy_single_agent()` in `configure.py:3047`
  Uses `shutil.copy2(source_file, target_file)` — no backup, no verification
- **Skills management**: `_manage_skills()` → `configure.py:672`
  Reads deployed from `Path.cwd() / ".claude" / "skills"` (direct filesystem scan)
  Installs via `shutil.copy2()` to `.claude/skills/{deploy_name}/skill.md`
- **Scope**: String `"project"` or `"user"`, passed through via `args.scope`

### API Path

Entry: HTTP routes in `services/monitor/config_routes.py` (read-only)
Write routes in:
- `services/config_api/agent_deployment_handler.py` — agents
- `services/config_api/skill_deployment_handler.py` — skills
- `services/config_api/autoconfig_handler.py` — toolchain detection

Key components:
- **Scope**: `core/config_scope.py` → `ConfigScope` enum (PROJECT/USER)
  `resolve_agents_dir(scope, project_path)` → `.claude/agents/` or `~/.claude/agents/`
  **Current limitation**: ALL handlers hardcode `ConfigScope.PROJECT` — no user scope
- **Safety protocol**: Every write follows: backup → journal → execute → verify
  - `services/config_api/backup_manager.py` → `BackupManager`
  - `services/config_api/operation_journal.py` → `OperationJournal`
  - `services/config_api/deployment_verifier.py` → `DeploymentVerifier`
- **Agent deploy**: Calls `AgentDeploymentService.deploy_agent(name, agents_dir, force_rebuild)`
- **Skill deploy**: Calls `SkillsDeployerService.deploy_skills(collection, skill_names, force, selective)`
- **Notifications**: Socket.IO events via `ConfigEventHandler` after every mutation

---

## 2. Common Operations Matrix

| Operation | CLI Location | API Location | Shared Service? |
|-----------|-------------|--------------|----------------|
| List agents | `SimpleAgentManager.discover_agents()` | `AgentManager` (config_routes) | **No** — different classes |
| Deploy agent | `_deploy_single_agent()` → `shutil.copy2()` | `AgentDeploymentService.deploy_agent()` | **No** — different mechanisms |
| Undeploy agent | Direct `unlink()` in `_remove_agents()` | `backup→journal→unlink→verify` | **No** — different safety |
| List skills | `_get_deployed_skill_ids()` — dir scan | `SkillsDeployerService.check_deployed_skills()` | **No** — different services |
| Deploy skill | `shutil.copy2()` to `.claude/skills/` | `SkillsDeployerService.deploy_skills()` | **No** — different mechanisms |
| Undeploy skill | `_uninstall_skill_by_name()` | `SkillsDeployerService.remove_skills()` | **No** — different services |
| Scope resolution | `configure_paths.py` string-based functions | `core/config_scope.py` `ConfigScope` enum | **Partial** — `ConfigScope` is shared model |
| Config persistence | `agent_states.json` + `configuration.yaml` | `configuration.yaml` (with `ConfigFileLock`) | **Partial** — same YAML, different writers |
| Input validation | None (trusts TUI) | `validate_safe_name()` + `validate_path_containment()` | **No** — API-only |
| Backup/recovery | None | `BackupManager` + `OperationJournal` | **No** — API-only |
| Post-deploy verify | None | `DeploymentVerifier` | **No** — API-only |
| Event notification | Console `print()` | Socket.IO `config_event` | **No** — different channels |

---

## 3. Existing Abstractions

### 3a. `core/config_scope.py` — Best Existing Abstraction

```python
class ConfigScope(str, Enum):
    PROJECT = "project"
    USER = "user"

def resolve_agents_dir(scope: ConfigScope, project_path: Path) -> Path
def resolve_skills_dir(scope: ConfigScope, project_path: Path | None = None) -> Path
def resolve_archive_dir(scope: ConfigScope, project_path: Path) -> Path
def resolve_config_dir(scope: ConfigScope, project_path: Path) -> Path
```

**Used by**: `services/config_api/agent_deployment_handler.py`, `services/config_api/backup_manager.py`, `services/config_api/deployment_verifier.py`, `services/config_api/autoconfig_handler.py`

**NOT used by**: `cli/commands/configure.py` — the CLI uses `cli/commands/configure_paths.py` instead

**Strength**: Already scope-aware, handles both project and user, resolves to BOTH path namespaces (`.claude/` and `.claude-mpm/`)

**Gap**: API handlers always pass `ConfigScope.PROJECT` — user scope is architecturally supported but operationally unused

### 3b. `core/shared/path_resolver.py` — Orphaned Third Resolver

`PathResolver` class in `core/shared/path_resolver.py` provides path resolution but resolves to `.claude-mpm/` (MPM config space), not `.claude/` (Claude Code deploy space). It's not used by either the CLI configure command or the API handlers, making it a **dead abstraction** that contributes to confusion.

### 3c. `services/config_api/validation.py` — API-Only Security Layer

```python
def validate_safe_name(name: str, entity_type: str) -> Tuple[bool, str]
def validate_path_containment(constructed_path, parent_dir, entity_type) -> Tuple[bool, str]
```

Used by all API mutation handlers but absent from CLI. A unified abstraction would want this at the service layer, not per-handler.

### 3d. `core/interfaces.py` — Declared But Thin

`AgentDeploymentInterface` exists as a Protocol base for `AgentDeploymentService`. This is the right pattern but under-utilized — the interface doesn't cover skills, listing, or scope.

---

## 4. Where the Paths Diverge (and Why)

### Divergence 1: Safety Protocol

| Aspect | CLI | API |
|--------|-----|-----|
| Pre-operation backup | ❌ None | ✅ `BackupManager.create_backup()` |
| Write-ahead journal | ❌ None | ✅ `OperationJournal.begin_operation()` |
| Post-deploy verify | ❌ None | ✅ `DeploymentVerifier.verify_agent_deployed()` |
| File locking | ❌ None | ✅ `ConfigFileLock` for YAML writes |

**Why it diverged**: CLI was built for interactive use where the user is present to recover from errors. API was built for programmatic use from the dashboard where crash recovery is critical.

**Implication for abstraction**: Safety protocol should be in the service layer, not per-path. Both paths should eventually use it.

### Divergence 2: Scope Support

CLI supports `scope = "project"` or `scope = "user"` via the `_switch_scope()` TUI action. The user scope deploys to `~/.claude-mpm/` (MPM config, not Claude Code deploy).

API is **hardcoded** to `ConfigScope.PROJECT`. `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` appears in every mutation handler. The `ConfigScope` enum has `USER` defined but the API never uses it.

**Implication**: A unified abstraction cannot simply route user scope to the API — the API would need to add user scope support first.

### Divergence 3: Two Different Path Namespaces

This is the most important structural issue:

| Path | Purpose | Used by |
|------|---------|---------|
| `.claude-mpm/agents/` | MPM agent templates/JSON configs | CLI `configure_paths.py` |
| `.claude/agents/` | Claude Code deployment targets (`.md` files) | API `config_scope.py`, CLI `_deploy_single_agent()` target |
| `.claude/skills/` | Claude Code skill deployment | Both paths (CLI scans, API deploys) |

The CLI uses `.claude-mpm/agents/` as its working directory (through `SimpleAgentManager.config_dir`) and deploys *to* `.claude/agents/`. The API works directly with `.claude/agents/` as the primary namespace.

`configure_paths.py` (CLI) and `config_scope.py` (API) are resolving **different namespaces** even though they look structurally similar. This is a naming collision risk.

### Divergence 4: State Model Mismatch

- **CLI state**: An agent is "enabled" (intent stored in `agent_states.json`)
  An agent can be enabled but not yet deployed, or disabled but still on disk.

- **API state**: An agent is "deployed" (presence of `.md` file in `.claude/agents/`)
  Binary: the file either exists or doesn't.

These are orthogonal concepts. The CLI tracks *user preference*; the API tracks *filesystem reality*. A unified abstraction needs both:
- `is_enabled(agent_name)` — user preference layer
- `is_deployed(agent_name)` — filesystem reality layer

### Divergence 5: Discovery vs. Listing

- **CLI**: `SimpleAgentManager.discover_agents()` discovers from local templates AND remote Git sources
  Returns `List[AgentConfig]` with metadata including `source_dict`, `full_agent_id`, `is_deployed`

- **API**: `AgentManager` (the larger one in `services/agents/management/`) handles listing
  Used via `config_routes.py` with pagination support

These are entirely different classes with different APIs.

---

## 5. Proposed Interface Boundaries

### 5a. Candidate Unified Service Interface

```python
from typing import Protocol, List
from dataclasses import dataclass

@dataclass
class AgentInfo:
    name: str
    is_enabled: bool       # user preference
    is_deployed: bool      # filesystem reality
    source: str            # "local", "git:<repo>"

@dataclass
class SkillInfo:
    name: str
    is_deployed: bool
    is_immutable: bool     # core/PM skills

@dataclass
class DeployResult:
    success: bool
    entity_name: str
    backup_id: str | None
    verification: dict | None
    error: str | None

class ConfigurationService(Protocol):
    """Unified interface for both CLI and API to use."""

    def list_agents(self, scope: ConfigScope) -> List[AgentInfo]: ...
    def deploy_agent(self, name: str, scope: ConfigScope, force: bool = False) -> DeployResult: ...
    def undeploy_agent(self, name: str, scope: ConfigScope) -> DeployResult: ...

    def list_skills(self, scope: ConfigScope) -> List[SkillInfo]: ...
    def deploy_skill(self, name: str, scope: ConfigScope, mark_user_requested: bool = False) -> DeployResult: ...
    def undeploy_skill(self, name: str, scope: ConfigScope) -> DeployResult: ...

    def get_deployment_mode(self) -> str: ...
    def set_deployment_mode(self, mode: str, scope: ConfigScope) -> DeployResult: ...
```

### 5b. Where to Insert the Abstraction

```
CLI (ConfigureCommand)          API (aiohttp handlers)
        |                               |
        v                               v
+-------+-------------------------------+-------+
|           ConfigurationService                |  ← NEW abstraction layer
|   (handles scope, validation, safety)         |
+-------+-------------------------------+-------+
        |                               |
        v                               v
AgentDeploymentService      SkillsDeployerService
(existing, unchanged)       (existing, unchanged)
```

The abstraction layer would:
1. Normalize scope (string → `ConfigScope` enum)
2. Apply `validate_safe_name()` before all operations
3. Optionally run the backup/journal/verify safety protocol (configurable per caller)
4. Route to the correct underlying service

### 5c. Seam Locations

The clearest insertion seams are:

**Agent deploy seam**:
- CLI: `configure.py:3047` `_deploy_single_agent()` → **remove shutil.copy2, call service**
- API: `agent_deployment_handler.py:158` `_deploy_sync()` → **delegate to same service**
- Shared service: `AgentDeploymentService.deploy_agent()` already exists

**Skill deploy seam**:
- CLI: `configure.py:1295` `_install_skill()` → **remove shutil.copy2, call service**
- API: `skill_deployment_handler.py:153` `_deploy_sync()` → **delegate to same service**
- Shared service: `SkillsDeployerService.deploy_skills()` already exists

**Scope resolution seam**:
- CLI: `configure_paths.py` functions → **retire, use `config_scope.py` instead**
- API: `config_scope.py` already used → **extend to enable USER scope in API handlers**

---

## 6. Key Decision Points for Abstraction Design

### Decision 1: Safety Protocol Opt-in vs Mandatory

The CLI doesn't use backup/journal/verify. If the abstraction mandates the safety protocol, the CLI will slow down for interactive use. If optional, two code paths still diverge.

**Recommendation**: Make safety protocol a constructor parameter. CLI uses `safety=False` for fast interactive mode; API uses `safety=True` always.

### Decision 2: Scope → API: Add User Scope or Leave It?

Currently the API only supports project scope. Adding user scope to the API means:
- API handlers need to accept `scope` parameter in request body
- `ConfigScope.USER` needs to be properly wired up in all handlers

**Recommendation**: This should be a prerequisite before building a shared abstraction, otherwise the abstraction paper-covers the gap.

### Decision 3: State Model Reconciliation

"Enabled" (CLI intent) and "deployed" (API reality) must both exist in the abstraction. They're not the same concept.

**Recommendation**: The unified `AgentInfo` should carry both `is_enabled` and `is_deployed` fields. The CLI's `SimpleAgentManager` remains as the "intent" layer above the unified service.

### Decision 4: Retire configure_paths.py

`configure_paths.py` and `config_scope.py` are solving the same problem with different implementations. Having both creates confusion.

**Recommendation**: Retire `configure_paths.py`. Move all CLI path resolution to use `config_scope.py`. The `PathResolver` in `core/shared/path_resolver.py` should also be retired or documented as serving a different concern.

### Decision 5: Async/Sync Boundary

API handlers use `asyncio.to_thread()` to wrap sync service calls. CLI is purely synchronous.

**Recommendation**: Keep the service itself synchronous (like it is today). The API continues to wrap in `asyncio.to_thread()`. The CLI calls directly. This is the correct pattern — don't push async into the service layer.

---

## 7. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| CLI regression from removing shutil.copy2 | Medium | Both deploy paths need full test coverage before seam insertion |
| Scope confusion: `.claude-mpm/` vs `.claude/` | High | Document the two namespaces clearly in `config_scope.py` |
| Safety protocol performance regression in CLI | Low | Make safety protocol optional with `safety=False` default for CLI |
| Breaking existing API contract during refactor | Medium | Route API through adapter if internal signatures change |
| `SimpleAgentManager.discover_agents()` not unified | Low | Discovery is legitimately different (CLI discovers from templates; API lists deployed) |

---

## 8. File Inventory

| File | Role | Status |
|------|------|--------|
| `core/config_scope.py` | Scope enum + resolution functions | **Good — foundation for abstraction** |
| `services/config_api/validation.py` | Input validation | **Good — move to `core/`** |
| `services/config_api/backup_manager.py` | Pre-op backup | **Good — keep as-is** |
| `services/config_api/operation_journal.py` | Write-ahead log | **Good — keep as-is** |
| `services/config_api/deployment_verifier.py` | Post-op verification | **Good — keep as-is** |
| `services/agents/deployment/agent_deployment.py` | Agent deploy engine | **Good — the canonical deployer** |
| `cli/commands/configure_paths.py` | CLI path resolution | **Retire — duplicate of config_scope.py** |
| `cli/commands/agent_state_manager.py` | Agent intent tracking | **Keep — unique to CLI, not duplicated in API** |
| `cli/commands/configure.py` `_deploy_single_agent()` | CLI deploy shim | **Replace with service call** |
| `cli/commands/configure.py` `_install_skill()` | CLI skill install shim | **Replace with service call** |
| `core/shared/path_resolver.py` | Third path resolver | **Retire or clarify scope** |

---

## 9. Recommended Abstraction Phases

### Phase 1: Scope Unification (Low Risk, High Value)
- Migrate `cli/commands/configure_paths.py` usages to `core/config_scope.py`
- Add USER scope support to API handlers (accept `scope` param from request body)
- Add user scope tests for `config_scope.py` functions

### Phase 2: Validation Centralization (Low Risk)
- Move `services/config_api/validation.py` → `core/validation.py`
- Apply in CLI's `_deploy_single_agent()` before any file operations

### Phase 3: Deploy Seam Insertion (Medium Risk)
- Create `ConfigurationService` class wrapping both `AgentDeploymentService` and `SkillsDeployerService`
- CLI's `_deploy_single_agent()` and `_install_skill()` delegate to `ConfigurationService`
- API handlers continue using their safety-wrapped path but call same underlying service
- Add integration tests covering both paths for same operations

### Phase 4: Safety Protocol for CLI (Low Priority)
- Optionally extend CLI deploy to use backup/verify when `--safe` flag passed
- Makes CLI suitable for scripted/CI use cases

---

## 10. Conclusion

The most impactful single change is **scope unification**: retiring `configure_paths.py` in favor of `core/config_scope.py` and adding user scope to the API. This immediately reduces three separate path resolution implementations to one.

The second most impactful change is **moving validation to core**: the security-relevant `validate_safe_name()` and `validate_path_containment()` functions should protect both paths, not just the API.

A full `ConfigurationService` abstraction is feasible but requires resolving the two-namespace confusion (`.claude-mpm/` vs `.claude/`) and the state model mismatch (enabled vs deployed) before it will be clean to implement.
