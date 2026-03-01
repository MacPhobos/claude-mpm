# Implementation Strategies: Unified Configuration Abstraction

**Research by:** strategy-researcher
**Date:** 2026-02-28
**Task:** Propose concrete strategies for unifying CLI and API configuration code paths

---

## Executive Summary

The codebase already has a solid foundation for scope-based path resolution in `core/config_scope.py`. The existing `ConfigScope` enum and `resolve_*` functions handle the "project → .claude/agents/" vs "user → ~/.claude/agents/" mapping cleanly. The underlying deployment services (`AgentDeploymentService`, `SkillsDeployerService`) already accept scope-resolved paths as parameters — they are already scope-agnostic.

**The gap is narrow and well-defined:** The API handlers (`services/config_api/agent_deployment_handler.py`, `skill_deployment_handler.py`, `services/monitor/config_routes.py`) hardcode `ConfigScope.PROJECT` and `Path.cwd()`. The CLI (`cli/commands/configure.py`) uses the scope correctly but doesn't share a reusable abstraction with the API.

**Recommended strategy:** Strategy 1 (Scoped Deployment Context + Adapter) — it closes the gap with the least disruption by lifting the path-resolution logic into a thin context object and threading it through the API layer.

---

## Current Architecture Analysis

### Path Resolution: Already Centralized

```python
# core/config_scope.py — already exists and works
class ConfigScope(str, Enum):
    PROJECT = "project"  # → {project}/.claude/agents/
    USER    = "user"     # → ~/.claude/agents/

resolve_agents_dir(scope, project_path) → Path
resolve_skills_dir(scope, project_path) → Path
resolve_archive_dir(scope, project_path) → Path
resolve_config_dir(scope, project_path) → Path
```

### Underlying Services: Already Scope-Agnostic

```python
# AgentDeploymentService
def deploy_agent(self, agent_name: str, target_dir: Path, ...) → bool
def deploy_agents(self, target_dir: Optional[Path] = None, ...) → Dict

# SkillsDeployerService
def deploy_skills(self, ..., skills_dir: Optional[Path] = None) → Dict
def check_deployed_skills(self, skills_dir: ...) → Dict
def remove_skills(self, skill_names: List[str], skills_dir=None) → Dict
```

The services already accept target directories — they don't embed scope assumptions. The scope only determines *which* directory to pass in.

### The Hardcoding Problem (API Path)

```python
# services/config_api/agent_deployment_handler.py — current
agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())  # ← hardcoded

# services/config_api/skill_deployment_handler.py — current
def _get_config_path() -> Path:
    return Path.cwd() / ".claude-mpm" / "configuration.yaml"  # ← hardcoded
```

### CLI: Scope Managed Ad Hoc

```python
# cli/commands/configure.py — current
self.current_scope = getattr(args, "scope", "project")  # ← string
if self.current_scope == "project":
    config_dir = self.project_dir / ".claude-mpm"
else:
    config_dir = Path.home() / ".claude-mpm"
# target_dir = self.project_dir / ".claude" / "agents"  ← hardcoded in deploy
```

The CLI handles scope correctly but through ad-hoc string comparisons scattered across multiple methods, without sharing logic with the API.

---

## Strategy 1: Scoped Deployment Context (Recommended)

### Architecture Description

Introduce a lightweight `ScopedDeploymentContext` dataclass that captures scope + project path together. Both CLI and API resolve paths from this context. The context is created at the entry point (CLI arg parsing or HTTP request handling) and flows through as a parameter.

This is a **thin Adapter** that bridges the two entry points to the already-working services.

### Key Interfaces / Classes

```python
# New file: core/deployment_context.py

from dataclasses import dataclass
from pathlib import Path
from .config_scope import ConfigScope, resolve_agents_dir, resolve_skills_dir
from .config_scope import resolve_archive_dir, resolve_config_dir


@dataclass(frozen=True)
class DeploymentContext:
    """Immutable context capturing scope and project path.

    Created once at the request/command entry point and passed to services.
    Thread-safe (frozen dataclass) for use in async API handlers.
    """
    scope: ConfigScope
    project_path: Path

    @classmethod
    def from_project(cls, project_path: Path = None) -> "DeploymentContext":
        return cls(scope=ConfigScope.PROJECT, project_path=project_path or Path.cwd())

    @classmethod
    def from_user(cls) -> "DeploymentContext":
        return cls(scope=ConfigScope.USER, project_path=Path.cwd())

    @classmethod
    def from_string(cls, scope_str: str, project_path: Path = None) -> "DeploymentContext":
        """Backward-compatible factory for CLI (which uses raw "project"/"user" strings)."""
        scope = ConfigScope(scope_str)
        return cls(scope=scope, project_path=project_path or Path.cwd())

    @property
    def agents_dir(self) -> Path:
        return resolve_agents_dir(self.scope, self.project_path)

    @property
    def skills_dir(self) -> Path:
        return resolve_skills_dir(self.scope, self.project_path)

    @property
    def archive_dir(self) -> Path:
        return resolve_archive_dir(self.scope, self.project_path)

    @property
    def config_dir(self) -> Path:
        return resolve_config_dir(self.scope, self.project_path)

    @property
    def configuration_yaml(self) -> Path:
        return self.config_dir / "configuration.yaml"
```

### CLI Integration (Minimal Change)

```python
# cli/commands/configure.py — after change
def run(self, args) -> CommandResult:
    scope_str = getattr(args, "scope", "project")
    project_dir = Path(getattr(args, "project_dir", None) or Path.cwd())

    # One line to create context — replaces ad-hoc if/else blocks
    self._ctx = DeploymentContext.from_string(scope_str, project_dir)

    # Replace: config_dir = self.project_dir / ".claude-mpm"
    config_dir = self._ctx.config_dir
    self.agent_manager = SimpleAgentManager(config_dir)
    ...

# In _install_agent():
    # Replace: target_dir = self.project_dir / ".claude" / "agents"
    target_dir = self._ctx.agents_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target_dir / target_name)
```

### API Integration

The scope for API calls can come from:
- **Query parameter:** `?scope=project` (default) or `?scope=user`
- **Request body field:** `"scope": "user"` in JSON body

```python
# services/config_api/agent_deployment_handler.py — after change

async def deploy_agent(request: web.Request) -> web.Response:
    body = await request.json()

    # Parse scope from request (defaults to project for backward compat)
    scope_str = body.get("scope", "project")
    try:
        ctx = DeploymentContext.from_string(scope_str)
    except ValueError:
        return _error_response(400, f"Invalid scope: {scope_str}", "VALIDATION_ERROR")

    agents_dir = ctx.agents_dir  # ← was: resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())
    agent_path = agents_dir / f"{agent_name}.md"
    ...

# services/config_api/skill_deployment_handler.py — after change
def _get_config_path(scope_str: str = "project") -> Path:
    ctx = DeploymentContext.from_string(scope_str)
    return ctx.configuration_yaml  # ← was: Path.cwd() / ".claude-mpm" / "configuration.yaml"
```

### Migration Plan

1. **Phase 1 (no behavior change):** Add `core/deployment_context.py` with `DeploymentContext`. Add tests.
2. **Phase 2 (CLI refactor, no user-visible change):** Replace ad-hoc if/else scope blocks in `configure.py` with `DeploymentContext.from_string(scope, project_dir)`. All path derivations use `ctx.agents_dir`, `ctx.config_dir`, etc. No behavioral change.
3. **Phase 3 (API scope support):** Thread `scope` through API request body/query params. Replace hardcoded `ConfigScope.PROJECT` with `DeploymentContext.from_string(body.get("scope", "project"))`. Add `scope` field to API docs.
4. **Phase 4 (Lazy singleton cleanup):** Scoped lazy singletons: `_get_agent_deployment_service(scope)` keyed by scope, if needed.

### Pros

- **Minimal surface area.** One new file, ~50 lines of logic.
- **Zero breaking changes.** CLI still passes "project"/"user" strings; `from_string()` accepts them.
- **Thread-safe.** Frozen dataclass — safe for async API handlers.
- **Easy to test.** `DeploymentContext` is a pure value object, no mocking needed.
- **Leverages existing `ConfigScope` and resolvers.** No duplication.
- **Backward compatible.** `from_project()` factory replicates current API default behavior.

### Cons

- `DeploymentContext` must be passed explicitly through several layers — callers must opt in. The lazy-initialized module-level singletons in the API handlers (`_backup_manager`, `_operation_journal`, etc.) are scope-agnostic (they manage backups generically), so they don't need scoping.
- Lazy singletons like `_agent_deployment_service` are not affected by scope (they deploy to wherever `target_dir` points), so no changes needed there.

### Risk Assessment

**Low risk.** No existing behavior changes in Phase 1–2. Phase 3 adds scope to API as an optional param (defaults to "project"), maintaining 100% backward compatibility with existing API clients.

---

## Strategy 2: Facade Pattern (ConfigurationService)

### Architecture Description

Introduce a `ConfigurationService` class that provides a unified interface over all configuration operations. Both CLI and API use this service instead of calling deployment services directly. The service receives scope at construction time.

```
CLI args        →  ConfigurationService(scope=PROJECT)  →  AgentDeploymentService
API request     →  ConfigurationService(scope=PROJECT)  →  SkillsDeployerService
                                                         →  BackupManager
                                                         →  OperationJournal
```

### Key Interfaces / Classes

```python
# New file: services/configuration_service.py

class ConfigurationService:
    """Facade over all agent/skill configuration operations.

    Encapsulates scope, project path, and the safety protocol
    (backup → journal → execute → verify → prune).
    """

    def __init__(self, scope: ConfigScope, project_path: Path = None):
        self.ctx = DeploymentContext(scope, project_path or Path.cwd())
        self._agent_svc = None
        self._skills_svc = None
        self._backup_mgr = None
        self._journal = None
        self._verifier = None

    def deploy_agent(self, agent_name: str, force: bool = False) -> DeployResult:
        """Deploy agent with full safety protocol (backup/journal/verify)."""
        ...

    def undeploy_agent(self, agent_name: str) -> DeployResult:
        ...

    def deploy_skill(self, skill_name: str, ...) -> DeployResult:
        ...

    def undeploy_skill(self, skill_name: str) -> DeployResult:
        ...

    def list_deployed_agents(self) -> List[AgentInfo]:
        ...

    def list_deployed_skills(self) -> List[SkillInfo]:
        ...

    def get_deployment_mode(self) -> DeploymentMode:
        ...

    def set_deployment_mode(self, mode: str) -> None:
        ...
```

### CLI Integration

```python
# cli/commands/configure.py
class ConfigureCommand(BaseCommand):
    def run(self, args):
        scope = ConfigScope(getattr(args, "scope", "project"))
        project_dir = Path.cwd()

        self._config_svc = ConfigurationService(scope=scope, project_path=project_dir)
        # All operations go through self._config_svc
```

### API Integration

```python
# services/config_api/agent_deployment_handler.py
async def deploy_agent(request):
    body = await request.json()
    scope = ConfigScope(body.get("scope", "project"))
    svc = ConfigurationService(scope=scope)
    result = await asyncio.to_thread(svc.deploy_agent, agent_name, force)
    ...
```

### Migration Plan

1. **Phase 1:** Create `ConfigurationService` as a thin wrapper over existing service calls. Copy logic from `agent_deployment_handler.py` and `skill_deployment_handler.py`.
2. **Phase 2:** Refactor API handlers to use `ConfigurationService`. Remove duplicate logic from handlers.
3. **Phase 3:** Refactor CLI's `ConfigureCommand` to use `ConfigurationService` for deploy/undeploy operations.
4. **Phase 4:** Move backup/journal/verify protocol into service. Remove from handlers.

### Pros

- **Single place for the safety protocol** (backup → journal → execute → verify). Currently duplicated between agent and skill handlers.
- **Testable** — service can be tested directly without HTTP layer.
- **Clean API** — callers don't need to know about BackupManager, OperationJournal, etc.
- **Extensible** — adding new operations (e.g., "restore from backup") happens in one place.

### Cons

- **Larger scope of change.** Requires moving significant logic from handlers into the service.
- **Risk of regressions** in the safety protocol if logic is incorrectly ported.
- **Two levels of lazy loading** — service must lazy-init BackupManager etc. internally, adding complexity.
- **More indirection** — harder to trace from an API endpoint to the actual file operation.
- Existing `agent_deployment_handler.py` is ~526 lines; combining agent + skill logic adds ~800 more. The facade could become a god class unless carefully subdivided.

### Risk Assessment

**Medium risk.** Moving the safety protocol into a new class risks subtle behavioral changes. Requires thorough testing coverage before and after migration. The gain (removing duplication) is real but not urgent — the current duplication is localized and manageable.

---

## Strategy 3: Repository Pattern with Factory

### Architecture Description

Introduce a `DeploymentRepository` interface, with `ProjectDeploymentRepository` and `UserDeploymentRepository` implementations. A factory creates the appropriate implementation based on scope.

```
DeploymentRepository (Protocol/ABC)
├── ProjectDeploymentRepository  →  resolves to .claude/agents/
└── UserDeploymentRepository     →  resolves to ~/.claude/agents/
DeploymentRepositoryFactory.create(scope, project_path) → DeploymentRepository
```

### Key Interfaces / Classes

```python
# New file: core/deployment_repository.py

from typing import Protocol, runtime_checkable

@runtime_checkable
class DeploymentRepository(Protocol):
    """Read/write access to a scoped deployment directory."""

    @property
    def agents_dir(self) -> Path: ...
    @property
    def skills_dir(self) -> Path: ...

    def deploy_agent(self, agent_name: str, source_path: Path, force: bool) -> None: ...
    def undeploy_agent(self, agent_name: str) -> None: ...
    def agent_exists(self, agent_name: str) -> bool: ...
    def list_agents(self) -> List[str]: ...

    def deploy_skill(self, skill_name: str, source_path: Path, force: bool) -> None: ...
    def undeploy_skill(self, skill_name: str) -> None: ...
    def skill_exists(self, skill_name: str) -> bool: ...
    def list_skills(self) -> List[str]: ...


class ProjectDeploymentRepository:
    def __init__(self, project_path: Path):
        self._project_path = project_path

    @property
    def agents_dir(self) -> Path:
        return self._project_path / ".claude" / "agents"

    @property
    def skills_dir(self) -> Path:
        return self._project_path / ".claude" / "skills"

    def deploy_agent(self, agent_name: str, source_path: Path, force: bool) -> None:
        target = self.agents_dir / f"{agent_name}.md"
        if target.exists() and not force:
            raise ConflictError(agent_name)
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)

    # ... other methods


class UserDeploymentRepository:
    @property
    def agents_dir(self) -> Path:
        return Path.home() / ".claude" / "agents"

    # ... mirrors ProjectDeploymentRepository but with home dir paths


class DeploymentRepositoryFactory:
    @staticmethod
    def create(scope: ConfigScope, project_path: Path = None) -> DeploymentRepository:
        if scope == ConfigScope.PROJECT:
            return ProjectDeploymentRepository(project_path or Path.cwd())
        return UserDeploymentRepository()
```

### Migration Plan

1. **Phase 1:** Define `DeploymentRepository` Protocol and both implementations.
2. **Phase 2:** Create `DeploymentRepositoryFactory`.
3. **Phase 3:** Use factory in API handlers.
4. **Phase 4:** Use factory in CLI.
5. **Phase 5:** Move backup/journal/verify above the repository (in service layer).

### Pros

- **Clean separation of concerns.** Repository handles persistence; service handles business logic.
- **Testable with simple test doubles** — any object satisfying the Protocol works.
- **Polymorphic** — adding a third scope (e.g., "workspace") requires only a new repository class.
- **Domain modeling.** Captures "deployment directory" as a first-class concept.

### Cons

- **Most invasive.** Requires changing how all deployment logic interacts with the file system.
- **Overkill for the problem.** The existing `resolve_*` functions already centralize path logic; a repository adds a full abstraction layer for what is essentially path resolution + file copy.
- **The backup/journal protocol** sits above the repository in the existing design — it's unclear where it belongs in the repository hierarchy.
- **Two more classes to maintain** (both implementations must stay in sync).
- Risk of divergence between `ProjectDeploymentRepository` and `UserDeploymentRepository` implementations.

### Risk Assessment

**High risk relative to benefit.** The pattern is appropriate for complex domain logic, but the core operations here are file copies with path resolution. Strategy 3 introduces abstraction for its own sake rather than to solve a real maintenance problem. Recommended only if a future requirement (e.g., remote deployment, transactional rollback across both scopes, database-backed state) makes the abstraction necessary.

---

## Recommended Strategy: Strategy 1

### Rationale

1. **The problem is path resolution, not business logic.** `ConfigScope` and the `resolve_*` functions already solve this. The gap is that the API hardcodes `PROJECT`. Adding `DeploymentContext` closes this gap without touching business logic.

2. **Smallest blast radius.** No existing behavior changes until Phase 3. CLI works identically. API defaults to "project" scope for backward compatibility.

3. **Leverages what already works.** `AgentDeploymentService.deploy_agent(name, target_dir)` and `SkillsDeployerService.deploy_skills(skills_dir=...)` already accept the path as a param. The only change is computing that path from `DeploymentContext` instead of hardcoding it.

4. **Testable.** `DeploymentContext` is a pure value object. `from_string("project", Path("/my/proj")).agents_dir` can be asserted without mocking anything.

5. **Incrementally adoptable.** Phases 1–2 are pure refactors (no behavior change). Phase 3 adds scope to the API as an opt-in feature. Teams can adopt at their own pace.

---

## Backward Compatibility Analysis

| Component | Current Behavior | After Strategy 1 | Breaking? |
|-----------|-----------------|-------------------|-----------|
| `claude-mpm configure` CLI | scope="project" by default | Same — `from_string("project", ...)` | No |
| CLI with `--scope user` | switches to user dir | Same — `from_string("user", ...)` | No |
| `POST /api/config/agents/deploy` | always project scope | defaults to project; accepts `"scope": "user"` | No (additive) |
| `DELETE /api/config/agents/{name}` | always project scope | defaults to project; accepts `?scope=user` | No (additive) |
| `POST /api/config/skills/deploy` | always project scope | defaults to project; accepts `"scope": "user"` | No (additive) |
| Lazy singletons (`_backup_manager`, etc.) | shared, scope-unaware | unchanged — backup/journal are scope-agnostic | No |
| `_get_config_path()` | returns project `.claude-mpm/configuration.yaml` | returns scope-appropriate path | No for existing calls |

**Note on lazy singletons:** The `_agent_deployment_service` singleton in the API handler is stateless with respect to scope (it accepts `target_dir` at call time). No changes needed.

---

## Error Handling and Validation Considerations

### Scope Validation

```python
# In API handler
scope_str = body.get("scope", "project")
if scope_str not in ("project", "user"):
    return _error_response(400, f"Invalid scope '{scope_str}'. Must be 'project' or 'user'.", "VALIDATION_ERROR")
```

### Path Containment (Existing Security Controls)

The existing `validate_path_containment` in `services/config_api/validation.py` must be called with the scope-resolved `agents_dir`. This already works correctly because `agents_dir` is computed from `ctx.agents_dir` rather than hardcoded.

```python
agents_dir = ctx.agents_dir
agent_path = agents_dir / f"{agent_name}.md"
valid, err_msg = validate_path_containment(agent_path, agents_dir, "agent")
```

### Config File Locking

The `config_file_lock` in `skill_deployment_handler.py` locks on `_get_config_path()`. After change, the lock path becomes `ctx.configuration_yaml`. The lock is file-path based, so project-scope and user-scope operations lock separate files — no cross-scope contention.

---

## Configuration Persistence and State Management

The `configuration.yaml` at `{scope_dir}/.claude-mpm/configuration.yaml` stores deployment mode, `user_defined` skills, and `agent_referenced` skills. After scoping:

- **Project scope:** `{project}/.claude-mpm/configuration.yaml` (unchanged from current)
- **User scope:** `~/.claude-mpm/configuration.yaml` (new, for user-level config)

The `deployment_mode` in user scope controls `~/.claude/skills/` deployment behavior. This is a valid and meaningful configuration (e.g., a user who wants all skills globally).

---

## Testing Implications

### Strategy 1 Testing

```python
# tests/unit/core/test_deployment_context.py

def test_project_context_resolves_correct_agents_dir():
    ctx = DeploymentContext.from_project(Path("/my/project"))
    assert ctx.agents_dir == Path("/my/project/.claude/agents")

def test_user_context_resolves_home_agents_dir():
    ctx = DeploymentContext.from_user()
    assert ctx.agents_dir == Path.home() / ".claude" / "agents"

def test_from_string_project():
    ctx = DeploymentContext.from_string("project", Path("/my/project"))
    assert ctx.scope == ConfigScope.PROJECT

def test_from_string_user():
    ctx = DeploymentContext.from_string("user")
    assert ctx.scope == ConfigScope.USER

def test_from_string_invalid():
    with pytest.raises(ValueError):
        DeploymentContext.from_string("workspace")
```

### API Handler Tests (after change)

```python
# Existing tests pass unchanged (default scope = "project")
# New tests cover scope parameter:

async def test_deploy_agent_user_scope(client):
    response = await client.post("/api/config/agents/deploy", json={
        "agent_name": "engineer",
        "scope": "user"
    })
    assert response.status == 201
    # Verify file was placed in ~/.claude/agents/, not .claude/agents/

async def test_deploy_agent_invalid_scope(client):
    response = await client.post("/api/config/agents/deploy", json={
        "agent_name": "engineer",
        "scope": "workspace"  # invalid
    })
    assert response.status == 400
```

### CLI Tests (after Phase 2 refactor)

The CLI refactor is behavior-preserving. Existing CLI tests should pass without modification. Integration tests verifying file placement in `{project}/.claude/agents/` and `~/.claude/agents/` cover the scope logic.

---

## Summary

| Criterion | Strategy 1 (Recommended) | Strategy 2 | Strategy 3 |
|-----------|--------------------------|------------|------------|
| Risk | Low | Medium | High |
| Lines changed | ~150 | ~500 | ~400+ |
| Breaking changes | None | None | None |
| Testability | High | High | High |
| Duplication removed | Moderate | High | Moderate |
| Complexity added | Minimal | Moderate | High |
| Future extensibility | Good | Good | Best |

**Decision:** Implement Strategy 1. It solves the stated problem (unify CLI and API scope handling) with the minimum change surface, preserves all existing behavior, and creates a clean, testable abstraction (`DeploymentContext`) that can serve as the foundation for Strategies 2 or 3 if future requirements demand them.
