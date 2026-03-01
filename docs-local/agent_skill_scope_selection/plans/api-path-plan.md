# API Path: Phased Implementation Plan for Scope Abstraction

**Planner:** api-planner agent
**Date:** 2026-02-28
**Branch:** agent_skill_scope_selection
**Source research:** `docs-local/agent_skill_scope_selection/research/`

---

## Executive Summary

The API path (`/api/config/` endpoints) hardcodes `ConfigScope.PROJECT` in 14+ call sites across
four handler files. The `ConfigScope` enum and `resolve_*` functions in `core/config_scope.py`
already provide scope-aware path resolution — the gap is purely in the HTTP layer and service
singletons.

This plan follows Strategy 1 (DeploymentContext) from `implementation-strategies.md`. The key
design choices:

1. **DeploymentContext** — a ~50-line frozen dataclass that captures scope + project_path and
   exposes `agents_dir`, `skills_dir`, `config_dir`, `configuration_yaml` properties.
2. **Scope parameter defaults to "project"** — all existing API clients continue working unchanged.
3. **Singleton trap is fixed first** (before any scope is added to endpoints) — prevents silent
   bugs where read operations return wrong-scope data.
4. **Safety protocol (backup→journal→execute→verify) is preserved and extended** to accept
   scope-resolved paths rather than hardcoded project paths.

---

## Architecture Before and After

### Before (current state)

```
POST /api/config/agents/deploy  {agent_name: "engineer"}
         │
         ▼
deploy_agent() handler
  agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())  ← hardcoded
         │
         ▼
_agent_manager singleton (created at first call with Path.cwd()/.claude/agents)  ← singleton trap
```

### After (target state)

```
POST /api/config/agents/deploy  {agent_name: "engineer", scope: "user"}
         │
         ▼
deploy_agent() handler
  ctx = DeploymentContext.from_string(body.get("scope", "project"))
  agents_dir = ctx.agents_dir   ← scope-resolved
         │
         ▼
No singleton trap: _agent_managers["project"] / _agent_managers["user"]  ← per-scope dict
```

---

## Phase 0: Pre-conditions (Safety Net Before Any Code Change)

**Objective:** Establish tests that characterize the current behavior so refactoring does not
silently break anything. Also document what "user scope" means to remove ambiguity.

**Dependencies:** None — this is the starting gate.

### Task 0.1: Document the user scope contract

- **File to modify:** `src/claude_mpm/core/config_scope.py` docstring
- **Change:** Add a section clarifying the semantics of each scope:
  - `PROJECT`: Deploys to `<cwd>/.claude/agents/` and `<cwd>/.claude/skills/`. The CWD is the
    project root where the monitor server was started. This is the only scope currently supported
    by the API.
  - `USER`: Deploys to `~/.claude/agents/` and `~/.claude/skills/`. Agents deployed here are
    visible to Claude Code from any project on this machine.
- **Acceptance criteria:** Docstring is clear enough that a new contributor understands why
  `Path.cwd()` is used for PROJECT scope and is NOT used for USER scope.

### Task 0.2: Write characterization tests for existing API behavior

- **File to create:** `tests/unit/services/config_api/test_scope_current_behavior.py`
- **Tests to write:**

```python
# Characterize what the CURRENT API does — PROJECT hardcoding
def test_agent_deploy_uses_cwd_agents_dir(tmp_path, monkeypatch):
    """Current behavior: agents always land in {cwd}/.claude/agents/."""
    monkeypatch.chdir(tmp_path)
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    # ... call deploy handler with no scope param
    # assert file created in tmp_path/.claude/agents/

def test_skill_config_path_uses_cwd(tmp_path, monkeypatch):
    """Current behavior: configuration.yaml is always at {cwd}/.claude-mpm/."""
    monkeypatch.chdir(tmp_path)
    # assert _get_config_path() returns tmp_path/.claude-mpm/configuration.yaml

def test_agent_manager_singleton_is_per_process(tmp_path, monkeypatch):
    """Characterize singleton behavior before fix."""
    # Shows that calling _get_agent_manager() twice returns same object
```

- **Acceptance criteria:** All characterization tests pass on the unmodified codebase. They will
  continue to pass after refactoring (proving behavior preservation).

### Task 0.3: Write integration test fixtures

- **File to create:** `tests/integration/api/conftest.py`
- **Contents:** Shared fixtures for aiohttp test client, tmp project dirs, tmp user home dirs.
  These will be used in later phases.
- **Acceptance criteria:** Fixtures are importable; `pytest --collect-only` lists the test module.

**Phase 0 milestone:** A clean test baseline exists. `make test` passes on the current code with
the new characterization tests in place.

**Phase 0 risk:** Low. Tests only read existing code.

---

## Phase 1: Introduce DeploymentContext (Zero Behavior Change)

**Objective:** Create the `DeploymentContext` dataclass. No existing code is changed — this is
purely additive. The devil's advocate warned against adding a "fourth resolver." The counter-
argument that applies here: the dashboard **will** need user scope when scope UI is added, and
`DeploymentContext` is the clean threading mechanism. We add it now so Phase 3 changes are small
and focused.

**Dependencies:** Phase 0 complete (test baseline exists).

### Task 1.1: Create `core/deployment_context.py`

- **File to create:** `src/claude_mpm/core/deployment_context.py`
- **Class to add:**

```python
from dataclasses import dataclass
from pathlib import Path
from .config_scope import ConfigScope, resolve_agents_dir, resolve_skills_dir
from .config_scope import resolve_archive_dir, resolve_config_dir


@dataclass(frozen=True)
class DeploymentContext:
    """Immutable context capturing scope and project path.

    Created once at the request or command entry point and passed to
    services. Thread-safe (frozen dataclass) for use in async API handlers.

    Usage in API handlers:
        ctx = DeploymentContext.from_request_scope(body.get("scope", "project"))
        agents_dir = ctx.agents_dir
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
    def from_request_scope(cls, scope_str: str, project_path: Path = None) -> "DeploymentContext":
        """Create from an HTTP request scope string (default: 'project').

        Raises:
            ValueError: If scope_str is not 'project' or 'user'.
        """
        if scope_str not in ("project", "user"):
            raise ValueError(f"Invalid scope '{scope_str}'. Must be 'project' or 'user'.")
        return cls(scope=ConfigScope(scope_str), project_path=project_path or Path.cwd())

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

- **Acceptance criteria:**
  - `DeploymentContext.from_project(Path("/p")).agents_dir == Path("/p/.claude/agents")`
  - `DeploymentContext.from_user().agents_dir == Path.home() / ".claude" / "agents"`
  - `DeploymentContext.from_request_scope("project", Path("/p")).skills_dir == Path("/p/.claude/skills")`
  - `DeploymentContext.from_request_scope("user").configuration_yaml == Path.home() / ".claude-mpm" / "configuration.yaml"`
  - `DeploymentContext.from_request_scope("workspace")` raises `ValueError`
  - The dataclass is frozen (immutable) — `ctx.scope = ConfigScope.USER` raises `FrozenInstanceError`

### Task 1.2: Unit tests for DeploymentContext

- **File to create:** `tests/unit/core/test_deployment_context.py`
- **Tests:**

```python
def test_from_project_resolves_correct_dirs(tmp_path):
    ctx = DeploymentContext.from_project(tmp_path)
    assert ctx.agents_dir == tmp_path / ".claude" / "agents"
    assert ctx.skills_dir == tmp_path / ".claude" / "skills"
    assert ctx.config_dir == tmp_path / ".claude-mpm"
    assert ctx.configuration_yaml == tmp_path / ".claude-mpm" / "configuration.yaml"

def test_from_user_resolves_home_dirs():
    ctx = DeploymentContext.from_user()
    assert ctx.agents_dir == Path.home() / ".claude" / "agents"
    assert ctx.skills_dir == Path.home() / ".claude" / "skills"
    assert ctx.config_dir == Path.home() / ".claude-mpm"

def test_from_request_scope_project(tmp_path):
    ctx = DeploymentContext.from_request_scope("project", tmp_path)
    assert ctx.scope == ConfigScope.PROJECT

def test_from_request_scope_user():
    ctx = DeploymentContext.from_request_scope("user")
    assert ctx.scope == ConfigScope.USER

def test_from_request_scope_invalid_raises():
    with pytest.raises(ValueError, match="Invalid scope"):
        DeploymentContext.from_request_scope("workspace")

def test_is_frozen():
    ctx = DeploymentContext.from_project()
    with pytest.raises(FrozenInstanceError):
        ctx.scope = ConfigScope.USER
```

- **Acceptance criteria:** All 6 tests pass.

**Phase 1 milestone:** `DeploymentContext` exists and is unit-tested. No existing file has been
modified.

**Phase 1 risk:** Zero. No existing code is changed.

---

## Phase 2: Fix the Singleton Trap (Critical Safety Gate)

**Objective:** Eliminate the singleton trap in `config_routes.py` before any scope parameter is
added to endpoints. This is the most important phase — skipping it would cause silent data
corruption where user-scope requests read project-scope data.

**The devil's advocate warning (from `devils-advocate.md`, section 6):**
> Adding `scope` to the API without fixing the singleton architecture first will introduce subtle,
> hard-to-debug bugs where read and write operations disagree about which directory is authoritative.

**Dependencies:** Phase 1 complete (DeploymentContext exists).

### Task 2.1: Replace `_agent_manager` global singleton with per-scope dict in `config_routes.py`

- **File to modify:** `src/claude_mpm/services/monitor/config_routes.py`
- **Functions to change:** `_get_agent_manager()`

**Current code (lines 28-45):**
```python
_agent_manager = None

def _get_agent_manager(project_dir: Optional[Path] = None):
    global _agent_manager
    if _agent_manager is None:
        agents_dir = project_dir or (Path.cwd() / ".claude" / "agents")
        _agent_manager = AgentManager(project_dir=agents_dir)
    return _agent_manager
```

**Replacement:**
```python
# Replace single singleton with per-scope dict
_agent_managers: Dict[str, Any] = {}

def _get_agent_manager(scope: str = "project") -> Any:
    """Return a scope-appropriate AgentManager.

    Keyed by scope string so project-scope and user-scope managers are
    independent. The user-scope manager reads from ~/.claude/agents/.
    """
    global _agent_managers
    if scope not in _agent_managers:
        from claude_mpm.services.agents.management.agent_management_service import AgentManager
        from claude_mpm.core.deployment_context import DeploymentContext
        ctx = DeploymentContext.from_request_scope(scope)
        _agent_managers[scope] = AgentManager(project_dir=ctx.agents_dir)
    return _agent_managers[scope]
```

- **Call sites to update within config_routes.py:**
  - `handle_project_summary`: `_get_agent_manager()` → `_get_agent_manager("project")` (unchanged
    behavior; explicit for clarity)
  - `handle_agents_deployed`: same
  - `handle_agent_detail`: same
  - All other callers of `_get_agent_manager()` in config_routes.py

- **Note:** At this phase, all callers pass `"project"` (no change in behavior). The scope param
  is wired to request context in Phase 4.

- **Acceptance criteria:**
  - `_get_agent_manager("project")` returns an `AgentManager` for `{cwd}/.claude/agents/`
  - `_get_agent_manager("user")` returns an `AgentManager` for `~/.claude/agents/`
  - Calling `_get_agent_manager("project")` twice returns the same object (cached)
  - Calling `_get_agent_manager("user")` after `_get_agent_manager("project")` returns a
    DIFFERENT object (not the singleton trap)
  - All existing API tests still pass (behavior unchanged for project scope)

### Task 2.2: Fix DeploymentVerifier to accept scope-resolved paths at call sites

- **File to modify:** `src/claude_mpm/services/config_api/agent_deployment_handler.py`
- **File to read first:** `src/claude_mpm/services/config_api/deployment_verifier.py`

**Analysis:** `DeploymentVerifier.__init__` captures `default_agents_dir` at construction time
(hardcoded PROJECT scope, lines 63-66 of deployment_verifier.py). However, the methods already
accept an optional `agents_dir` override:
```python
def verify_agent_deployed(self, agent_name: str, agents_dir: Optional[Path] = None)
```

The singleton is created as `DeploymentVerifier()` with no args — so the default is
`<cwd>/.claude/agents/`. For user-scope operations, this default is wrong.

**Fix:** Pass `agents_dir` explicitly in the handler instead of relying on the default:

In `agent_deployment_handler.py`, `_deploy_sync()` inner function (currently line 185):
```python
# Before:
verification = verifier.verify_agent_deployed(agent_name)

# After (Phase 2 prep — still project scope, but explicit):
verification = verifier.verify_agent_deployed(agent_name, agents_dir=agents_dir)
```

Same for `verify_agent_undeployed()` in `_undeploy_sync()` and the batch deploy loop.

- **Acceptance criteria:**
  - `verifier.verify_agent_deployed(name)` is never called without `agents_dir` in the handlers
  - Existing deploy/undeploy tests pass

### Task 2.3: Fix DeploymentVerifier for skills

- **File to modify:** `src/claude_mpm/services/config_api/skill_deployment_handler.py`
- **Check:** Does `verify_skill_deployed()` accept `skills_dir` param?
  Read `deployment_verifier.py` to confirm signature, then make handlers explicit.
- **Change:** Pass `skills_dir` explicitly in `_deploy_sync()` in skill_deployment_handler.py
- **Acceptance criteria:** No handler calls `verify_skill_*()` without explicit dir param.

### Task 2.4: Write regression tests for singleton behavior

- **File to create:** `tests/unit/services/monitor/test_agent_manager_scoping.py`
- **Tests:**

```python
def test_project_and_user_managers_are_independent():
    """Ensure the singleton trap is gone."""
    # Clear module-level dict first
    import claude_mpm.services.monitor.config_routes as routes
    routes._agent_managers.clear()

    proj_mgr = routes._get_agent_manager("project")
    user_mgr = routes._get_agent_manager("user")

    assert proj_mgr is not user_mgr

def test_same_scope_returns_cached_manager():
    import claude_mpm.services.monitor.config_routes as routes
    routes._agent_managers.clear()

    a = routes._get_agent_manager("project")
    b = routes._get_agent_manager("project")
    assert a is b
```

- **Acceptance criteria:** Both tests pass.

**Phase 2 milestone:** The singleton trap is eliminated. Read endpoints still use project scope
(no behavioral change). The architecture is now safe to extend with user scope.

**Phase 2 risk:** Low-medium. The `_agent_manager` replacement is a small, focused change.
Risk: If any code in `config_routes.py` accesses `_agent_manager` directly (not through
`_get_agent_manager()`), it would break. Search the file before making the change:
```bash
grep -n "_agent_manager" src/claude_mpm/services/monitor/config_routes.py
```

---

## Phase 3: Add Scope to Mutation Endpoints

**Objective:** Add optional `scope` parameter to all deploy/undeploy endpoints. Use
`DeploymentContext` to thread the scope through to all service calls. Default to "project" for
100% backward compatibility.

**Dependencies:** Phase 2 complete (singleton trap fixed, verifier calls are explicit).

### Task 3.1: Add scope to `POST /api/config/agents/deploy`

- **File to modify:** `src/claude_mpm/services/config_api/agent_deployment_handler.py`
- **Function:** `deploy_agent()` (line 121)

**Changes:**

1. Parse scope from request body:
```python
# After extracting agent_name, _source_id, force:
scope_str = body.get("scope", "project")
try:
    ctx = DeploymentContext.from_request_scope(scope_str)
except ValueError as e:
    return _error_response(400, str(e), "VALIDATION_ERROR")
```

2. Replace hardcoded path (line 140):
```python
# Before:
agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())

# After:
agents_dir = ctx.agents_dir
```

3. Pass `agents_dir` to verifier (from Task 2.2):
```python
verification = verifier.verify_agent_deployed(agent_name, agents_dir=agents_dir)
```

4. Add scope to Socket.IO event data:
```python
await _handler.emit_config_event(
    operation="agent_deployed",
    entity_type="agent",
    entity_id=agent_name,
    status="completed",
    data={"agent_name": agent_name, "action": "deploy", "scope": scope_str},
)
```

5. Add scope to HTTP response:
```python
return web.json_response({
    "success": True,
    "message": f"Agent '{agent_name}' deployed successfully",
    "agent_name": agent_name,
    "scope": scope_str,          # ← new field
    "backup_id": result["backup_id"],
    "verification": result["verification"],
    ...
})
```

- **Import to add:**
```python
from claude_mpm.core.deployment_context import DeploymentContext
```
(Remove the now-unused direct import of `ConfigScope` if no longer referenced elsewhere in file.)

- **Acceptance criteria:**
  - `POST /api/config/agents/deploy {"agent_name": "x"}` deploys to `{cwd}/.claude/agents/x.md`
    (backward compatible — no scope in body → defaults to "project")
  - `POST /api/config/agents/deploy {"agent_name": "x", "scope": "project"}` same as above
  - `POST /api/config/agents/deploy {"agent_name": "x", "scope": "user"}` deploys to
    `~/.claude/agents/x.md`
  - `POST /api/config/agents/deploy {"agent_name": "x", "scope": "workspace"}` returns HTTP 400
    `{"success": false, "code": "VALIDATION_ERROR"}`
  - Response body includes `"scope": "project"` or `"scope": "user"` field

### Task 3.2: Add scope to `DELETE /api/config/agents/{agent_name}`

- **File to modify:** `src/claude_mpm/services/config_api/agent_deployment_handler.py`
- **Function:** `undeploy_agent()` (line 240)

**Changes:**

1. Parse scope from query string (DELETE requests don't have bodies by convention):
```python
scope_str = request.rel_url.query.get("scope", "project")
try:
    ctx = DeploymentContext.from_request_scope(scope_str)
except ValueError as e:
    return _error_response(400, str(e), "VALIDATION_ERROR")
```

2. Replace hardcoded path (line 258):
```python
# Before:
agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())

# After:
agents_dir = ctx.agents_dir
```

3. Pass `agents_dir` to verifier in `_undeploy_sync()`.

4. Add scope to Socket.IO event and response.

- **Acceptance criteria:**
  - `DELETE /api/config/agents/x` undeployes from `{cwd}/.claude/agents/x.md`
  - `DELETE /api/config/agents/x?scope=user` undeployes from `~/.claude/agents/x.md`
  - `DELETE /api/config/agents/x?scope=bad` → HTTP 400

### Task 3.3: Add scope to `POST /api/config/agents/deploy-collection`

- **File to modify:** `src/claude_mpm/services/config_api/agent_deployment_handler.py`
- **Function:** `deploy_collection()` (line 335)

**Changes:**

1. Parse scope from body once (before the loop):
```python
scope_str = body.get("scope", "project")
try:
    ctx = DeploymentContext.from_request_scope(scope_str)
except ValueError as e:
    return _error_response(400, str(e), "VALIDATION_ERROR")
```

2. In `_deploy_one(name=agent_name)` closure (currently line 371):
```python
# Before:
agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())

# After: use ctx from outer scope
agents_dir = ctx.agents_dir
```

3. Add scope to batch response summary.

- **Acceptance criteria:** Same as Task 3.1 but for batch endpoint.

### Task 3.4: Add scope to `POST /api/config/skills/deploy`

- **File to modify:** `src/claude_mpm/services/config_api/skill_deployment_handler.py`
- **Function:** `deploy_skill()` (line 131)

**Changes:**

1. Parse scope from body:
```python
scope_str = body.get("scope", "project")
try:
    ctx = DeploymentContext.from_request_scope(scope_str)
except ValueError as e:
    return _error_response(400, str(e), "VALIDATION_ERROR")
```

2. Fix `_get_config_path()` — this is the critical change for skills. Currently:
```python
def _get_config_path() -> Path:
    return Path.cwd() / ".claude-mpm" / "configuration.yaml"
```

The function signature must change to accept scope context. Options:
- Pass `ctx` as a parameter to calls that need it (preferred — avoids shared mutable state)
- Replace with an inline expression in callers

**Recommended approach:** Replace `_get_config_path()` with `ctx.configuration_yaml` at each call
site inside `_deploy_sync()`. The module-level `_get_config_path()` function can remain for the
`get_deployment_mode` / `set_deployment_mode` handlers (which don't yet support scope — see
Phase 3.6).

3. Pass `skills_dir` to `SkillsDeployerService.deploy_skills()`:
```python
# Before:
result = svc.deploy_skills(
    collection=collection,
    skill_names=[skill_name],
    force=force,
    selective=False,
)

# After:
result = svc.deploy_skills(
    collection=collection,
    skill_names=[skill_name],
    force=force,
    selective=False,
    skills_dir=ctx.skills_dir,   # ← added
)
```

**Prerequisite check:** Verify `SkillsDeployerService.deploy_skills()` accepts `skills_dir`.
Read `src/claude_mpm/services/skills_deployer.py` to confirm. If it doesn't, that function needs
a `skills_dir` parameter added as part of this task.

4. Fix `mark_user_requested` section to use `ctx.configuration_yaml`:
```python
if mark_user_requested:
    config_path = ctx.configuration_yaml   # ← was _get_config_path()
    with config_file_lock(config_path):
        ...
```

5. Pass `skills_dir` to verifier:
```python
verification = verifier.verify_skill_deployed(skill_name, skills_dir=ctx.skills_dir)
```

- **Acceptance criteria:**
  - `POST /api/config/skills/deploy {"skill_name": "x"}` → `{cwd}/.claude/skills/x/`
  - `POST /api/config/skills/deploy {"skill_name": "x", "scope": "user"}` → `~/.claude/skills/x/`
  - `mark_user_requested=true, scope="user"` writes to `~/.claude-mpm/configuration.yaml`
  - Missing user-scope `configuration.yaml` is created on first write (parent dirs created)

### Task 3.5: Add scope to `DELETE /api/config/skills/{skill_name}`

- **File to modify:** `src/claude_mpm/services/config_api/skill_deployment_handler.py`
- **Function:** `undeploy_skill()` (line 248)

**Changes:**

1. Parse scope from query param: `scope_str = request.rel_url.query.get("scope", "project")`
2. Pass `skills_dir=ctx.skills_dir` to `svc.remove_skills()` (verify signature first)
3. Pass `skills_dir` to verifier: `verifier.verify_skill_undeployed(skill_name, skills_dir=ctx.skills_dir)`

- **Acceptance criteria:**
  - `DELETE /api/config/skills/x` removes from `{cwd}/.claude/skills/x/`
  - `DELETE /api/config/skills/x?scope=user` removes from `~/.claude/skills/x/`

### Task 3.6: Scope for deployment-mode endpoints (deferred scope, backward-compat stub)

- **Files to modify:** `src/claude_mpm/services/config_api/skill_deployment_handler.py`
- **Functions:** `get_deployment_mode()`, `set_deployment_mode()`

**Decision:** These two endpoints read/write `configuration.yaml`. At this phase, scope can be
added as a query param but the `_get_config_path()` calls inside can use a scope-aware version.

For `GET /api/config/skills/deployment-mode`:
```python
scope_str = request.rel_url.query.get("scope", "project")
# ... validate scope ...
# Inside _get_mode():
config_path = DeploymentContext.from_request_scope(scope_str).configuration_yaml
```

For `PUT /api/config/skills/deployment-mode`:
```python
scope_str = body.get("scope", "project")
# ... validate scope ...
# Inside _preview() and _apply():
config_path = DeploymentContext.from_request_scope(scope_str).configuration_yaml
```

**Special handling for user-scope configuration.yaml:**
- If `~/.claude-mpm/configuration.yaml` does not exist, `_load_config()` already handles this
  gracefully (returns `{}`)
- On write, `config_path.parent.mkdir(parents=True, exist_ok=True)` must be called before write
  (already present in the confirm branch)

- **Acceptance criteria:**
  - `GET /api/config/skills/deployment-mode?scope=project` reads `{cwd}/.claude-mpm/configuration.yaml`
  - `GET /api/config/skills/deployment-mode?scope=user` reads `~/.claude-mpm/configuration.yaml`
  - `PUT /api/config/skills/deployment-mode {"mode": "selective", "confirm": true, "scope": "user"}`
    writes to `~/.claude-mpm/configuration.yaml`

**Phase 3 milestone:** All mutation endpoints (deploy/undeploy agents and skills, mode switch)
accept an optional `scope` parameter defaulting to "project". Existing clients see no change.

**Phase 3 risks:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `SkillsDeployerService.deploy_skills()` does not accept `skills_dir` | Medium | Check signature before coding; add param if missing |
| `verify_skill_deployed()` does not accept `skills_dir` | Medium | Check `deployment_verifier.py` full implementation first |
| `~/.claude-mpm/configuration.yaml` missing for user-scope mode switch | High | Test for missing file; `_load_config()` already handles gracefully |
| Closure captures wrong `agents_dir` in batch loop | Low | Use `ctx.agents_dir` computed once before loop, captured in closure |

---

## Phase 4: Add Scope to Read-Only Endpoints

**Objective:** Add `?scope=project|user` query param to GET endpoints. Use the per-scope
`_agent_managers` dict (from Phase 2) to read from the correct directory.

**Dependencies:** Phase 3 complete (mutations are scope-aware). Phase 2 complete (singleton fixed).

### Task 4.1: Add scope to `GET /api/config/agents/deployed`

- **File to modify:** `src/claude_mpm/services/monitor/config_routes.py`
- **Function:** `handle_agents_deployed()` (line 305)

**Changes:**

1. Parse scope from query:
```python
scope_str = request.rel_url.query.get("scope", "project")
try:
    DeploymentContext.from_request_scope(scope_str)  # validate only
except ValueError:
    return web.json_response({"success": False, "error": "Invalid scope", "code": "VALIDATION_ERROR"}, status=400)
```

2. Use scoped manager:
```python
def _list_deployed():
    agent_mgr = _get_agent_manager(scope_str)   # ← was _get_agent_manager()
    agents_data = agent_mgr.list_agents(location="project")  # "project" = primary location
    ...
```

**Note on `list_agents(location=...)`:** The `AgentManager` `location` parameter refers to the
manager's internal location concept (primary vs framework), NOT to the deploy scope. The
manager's `project_dir` was set to the scope-resolved path at construction. So `location="project"`
always means "this manager's configured directory." Do NOT confuse this with ConfigScope.

- **Acceptance criteria:**
  - `GET /api/config/agents/deployed` returns agents from `{cwd}/.claude/agents/`
  - `GET /api/config/agents/deployed?scope=user` returns agents from `~/.claude/agents/`
  - Response includes `"scope": "project"` or `"scope": "user"` field

### Task 4.2: Add scope to `GET /api/config/project/summary`

- **File to modify:** `src/claude_mpm/services/monitor/config_routes.py`
- **Function:** `handle_project_summary()` (line 242)

**Changes:**

1. Parse scope from query param.
2. Use scoped agent manager: `_get_agent_manager(scope_str)`
3. Use scope-resolved skills dir:
```python
# Before (line 258):
project_skills_dir = Path.cwd() / ".claude" / "skills"

# After:
ctx = DeploymentContext.from_request_scope(scope_str)
project_skills_dir = ctx.skills_dir
```

4. Use scope-resolved config path:
```python
# Before:
config_path = Path.cwd() / ".claude-mpm" / "configuration.yaml"

# After:
config_path = ctx.configuration_yaml
```

- **Acceptance criteria:**
  - `GET /api/config/project/summary?scope=user` returns counts from user-scope directories

### Task 4.3: Add scope to `GET /api/config/skills/deployed`

- **File to modify:** `src/claude_mpm/services/monitor/config_routes.py`
- **Function:** `handle_skills_deployed()`

Read the handler at line ~258 to find exact hardcoding:
```python
project_skills_dir = Path.cwd() / ".claude" / "skills"
```

**Changes:** Replace with `ctx.skills_dir` using scope from query param.

- **Acceptance criteria:**
  - `GET /api/config/skills/deployed?scope=user` lists skills from `~/.claude/skills/`

### Task 4.4: Add scope to remaining GET endpoints

The research identified these additional hardcoded sites:
- `config_routes.py:441` — likely in `handle_skills_available` or `handle_skill_detail`
- `config_routes.py:523` — likely in `handle_skill_links`
- `config_routes.py:834` — likely in `handle_validate`

**For each:**
1. Read the function to understand what path is used
2. Add `scope_str = request.rel_url.query.get("scope", "project")`
3. Replace `Path.cwd() / ".claude" / ...` with `ctx.skills_dir` or `ctx.agents_dir`
4. Add acceptance test

**Note:** `handle_agents_available` reads from the git cache (not scope-dependent). The cache
stores source agent templates, not deployed agents. Do NOT add scope to this endpoint — the
available agents list is global regardless of scope.

**Note:** `handle_validate` runs validation checks. Adding scope changes which directories it
validates. If the user-scope directory doesn't exist, validation should return an appropriate
empty-but-valid result, not an error.

**Phase 4 milestone:** All GET endpoints accept `?scope=` query param. The dashboard can display
user-scope deployed agents and skills (even before UI scope selectors are added, developers can
test via curl).

**Phase 4 risks:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `AgentManager.list_agents()` fails for empty `~/.claude/agents/` dir | Medium | Test with missing directory; should return empty list |
| `SkillsDeployerService.check_deployed_skills()` fails for missing dir | Medium | Same — should return empty |
| Scope-aware validation errors for user-scope configs with different structure | Low | Validation should handle missing files gracefully |

---

## Phase 5: Scope-Aware Socket.IO Events and Dashboard Integration Points

**Objective:** Add scope metadata to Socket.IO `config_event` payloads. Document (but do not
implement) the dashboard changes needed to surface scope in the UI.

**Dependencies:** Phase 3 complete (mutations emit events).

### Task 5.1: Add scope field to all `config_event` emissions in mutation handlers

Every `emit_config_event()` call in the mutation handlers should include the scope in `data`:

- **Files to modify:**
  - `src/claude_mpm/services/config_api/agent_deployment_handler.py`
  - `src/claude_mpm/services/config_api/skill_deployment_handler.py`

**Change pattern (already partially done in Task 3.1):**
```python
# Before:
data={"agent_name": agent_name, "action": "deploy"}

# After:
data={"agent_name": agent_name, "action": "deploy", "scope": scope_str}
```

- **Acceptance criteria:**
  - All `config_event` emissions include `"scope": "project"` or `"scope": "user"` in `data`
  - No `config_event` emission is missing scope

### Task 5.2: Document dashboard integration points (no code changes)

Create a documentation file listing exactly what the Svelte dashboard would need to change to
expose scope selection. This is informational for the frontend team.

- **File to create:** `docs-local/agent_skill_scope_selection/plans/dashboard-integration-notes.md`

**Contents:**
1. **Scope selector component**: A `ScopeSelector.svelte` dropdown with "Project" / "User" options
   to be placed in `ConfigView.svelte` toolbar area.
2. **Store changes needed in `config.svelte.ts`**:
   - Add `configScope` writable store (default: `"project"`)
   - Modify all fetch functions to append `?scope=${get(configScope)}`
   - Modify `deployAgent()`, `undeployAgent()`, `deploySkill()`, `undeploySkill()` to include
     `scope` in request body
3. **Type changes needed**:
   - Add `scope: 'project' | 'user'` to `DeployedAgent`, `DeployedSkill` response types
   - Add `scope?: 'project' | 'user'` to deploy request body types
4. **Socket.IO event handling**: `config_event.data.scope` is now available; use it to decide
   which store to invalidate when a user-scope vs project-scope operation completes.
5. **Feature flag**: Add `SCOPE_SELECTOR: false` to `src/lib/config/features.ts` so scope UI
   can be shipped behind a flag.

- **Acceptance criteria:** Document exists and is reviewed by a frontend team member.

**Phase 5 milestone:** Events carry scope metadata. Backend is fully ready for a frontend scope
selector without further API changes.

---

## Cross-Cutting Concerns

### BackupManager and Scope

The `BackupManager` in `backup_manager.py:94` hardcodes `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` for determining what to back up. For user-scope operations, this means the backup will snapshot the project agents directory (which is irrelevant to the user-scope operation).

**Decision for this plan:** Leave `BackupManager` with its current behavior. The backup still
provides journaling and recovery for the operation that matters (the one being executed). A future
improvement could pass scope to `BackupManager` so it snapshots the correct directory, but this
is not required for correctness of the user-scope feature.

**Document this limitation** in `backup_manager.py` as a TODO comment:
```python
# TODO: BackupManager currently always backs up project-scope directories.
# For user-scope operations, consider passing scope here to snapshot the
# correct directory. See: docs-local/agent_skill_scope_selection/plans/api-path-plan.md
```

### Autoconfig Handler

`autoconfig_handler.py` has two hardcoded sites (lines 535, 576). Autoconfig detects the project
toolchain and always operates on the current project. It does not make semantic sense to autoconfig
at user scope (you'd auto-install agents globally based on one project's toolchain). Therefore:

**Decision:** Autoconfig endpoints are explicitly excluded from scope support. Add a comment and
return HTTP 400 if `scope=user` is passed to these endpoints:
```python
# POST /api/config/auto-configure/* — project scope only
if request.rel_url.query.get("scope", "project") == "user":
    return _error_response(400, "Auto-configure only supports project scope", "SCOPE_NOT_SUPPORTED")
```

### Backward Compatibility Guarantee

All scope changes follow this contract:
- Request without `scope` field/param → behavior identical to current (project scope)
- Request with `scope: "project"` or `?scope=project` → identical to current
- Request with `scope: "user"` or `?scope=user` → new behavior (user scope paths)
- Request with invalid scope string → HTTP 400 `VALIDATION_ERROR`

No existing API client that does not send a `scope` field will be affected.

---

## Testing Strategy Per Phase

| Phase | Test type | Key scenarios |
|-------|-----------|---------------|
| 0 | Unit (characterization) | Current paths, singleton behavior |
| 1 | Unit | DeploymentContext properties for both scopes |
| 2 | Unit | `_get_agent_manager` returns independent objects per scope |
| 3 | Integration | Deploy agent to user scope; file lands in `~/.claude/agents/` |
| 3 | Integration | Deploy skill with `mark_user_requested=true, scope=user` writes to `~/.claude-mpm/` |
| 3 | Integration | Backward compat: no scope param → project scope |
| 4 | Integration | GET deployed returns empty list for user scope with no user-scope agents |
| 4 | Integration | GET deployed returns user-scope agents after user-scope deploy |
| 5 | Unit | All emit_config_event calls include scope in data |

---

## File Change Summary

| File | Change | Phase |
|------|--------|-------|
| `src/claude_mpm/core/deployment_context.py` | **NEW** ~50-line frozen dataclass | 1 |
| `src/claude_mpm/services/monitor/config_routes.py` | Replace `_agent_manager` singleton with `_agent_managers` dict; add `?scope` to all GET handlers | 2, 4 |
| `src/claude_mpm/services/config_api/agent_deployment_handler.py` | Add `scope` parsing; replace 3 hardcoded `resolve_agents_dir(PROJECT, cwd())` calls; pass `agents_dir` to verifier | 2.2, 3.1, 3.2, 3.3, 5.1 |
| `src/claude_mpm/services/config_api/skill_deployment_handler.py` | Add `scope` parsing; fix `_get_config_path()`; pass `skills_dir` to services; add scope to events | 2.3, 3.4, 3.5, 3.6, 5.1 |
| `src/claude_mpm/services/config_api/deployment_verifier.py` | No structural change; verify method signatures already support `agents_dir` / `skills_dir` overrides | 2.2, 2.3 |
| `src/claude_mpm/services/config_api/backup_manager.py` | Add TODO comment only | cross-cutting |
| `src/claude_mpm/services/config_api/autoconfig_handler.py` | Add scope guard (project-scope only) | cross-cutting |
| `tests/unit/core/test_deployment_context.py` | **NEW** 6 unit tests | 1 |
| `tests/unit/services/monitor/test_agent_manager_scoping.py` | **NEW** 2 singleton tests | 2 |
| `tests/unit/services/config_api/test_scope_current_behavior.py` | **NEW** characterization tests | 0 |
| `tests/integration/api/conftest.py` | **NEW** shared fixtures | 0 |
| `docs-local/agent_skill_scope_selection/plans/dashboard-integration-notes.md` | **NEW** frontend notes | 5 |

---

## Estimated Scope of Change

- **New code:** ~200 lines (`deployment_context.py` + unit tests + integration fixtures)
- **Modified code:** ~120 lines across 4 handler/route files
- **Deleted code:** 0 lines (nothing removed)
- **Total diff:** ~320 lines, across 8 files modified + 4 files new

This is the "~150 lines for DeploymentContext" the strategy doc described, plus tests.

---

## Risk Register

| Risk | Severity | Phase | Mitigation |
|------|----------|-------|-----------|
| `_agent_manager` direct access bypasses singleton fix | High | 2 | `grep -n "_agent_manager"` before coding; fix any direct accesses |
| `SkillsDeployerService.deploy_skills()` missing `skills_dir` param | Medium | 3.4 | Read source before coding; add param if absent |
| `SkillsDeployerService.remove_skills()` missing `skills_dir` param | Medium | 3.5 | Same |
| `AgentManager` with user-scope path fails if `~/.claude/agents/` doesn't exist | Medium | 2, 4 | Test with missing dir; `AgentManager` should handle gracefully (return empty) |
| `verify_skill_deployed/undeployed` don't accept `skills_dir` param | Medium | 2.3 | Read `deployment_verifier.py` full implementation before coding |
| User-scope `~/.claude-mpm/configuration.yaml` doesn't exist on first access | High | 3.4, 3.6 | `_load_config()` already returns `{}` for missing files; `mkdir(parents=True)` before write |
| Batch deploy loop closure captures stale `agents_dir` | Low | 3.3 | Compute `agents_dir = ctx.agents_dir` before loop; capture by value in closure |
| `config_event` scope field breaks existing Svelte event handlers | Low | 5 | Svelte uses `data.agent_name` not `data.scope`; extra fields are ignored by JS |

---

## Dependencies Between Phases (Strict Ordering)

```
Phase 0 (baseline tests)
    └── Phase 1 (DeploymentContext)
            └── Phase 2 (singleton fix)   ← MUST precede Phase 3 and 4
                    ├── Phase 3 (mutation scope)
                    │       └── Phase 5 (events + dashboard notes)
                    └── Phase 4 (read scope)
```

Phase 4 could begin in parallel with Phase 5 once Phase 2 is done.

---

## Definition of Done (Full Plan)

The API-side scope implementation is complete when:

1. **All mutation endpoints** (`/agents/deploy`, `/agents/{name}`, `/agents/deploy-collection`,
   `/skills/deploy`, `/skills/{name}`, `/skills/deployment-mode`) accept an optional `scope` field
   defaulting to `"project"`.
2. **All read endpoints** accept an optional `?scope=` query param defaulting to `"project"`.
3. **No singleton trap**: `_agent_manager` is per-scope; calling with `"user"` after `"project"`
   returns a different manager instance.
4. **Backward compatibility**: All existing API tests pass without modification.
5. **User-scope deploy works end-to-end**: A POST to `/api/config/agents/deploy` with
   `{"scope": "user", "agent_name": "engineer"}` places the file in `~/.claude/agents/engineer.md`
   and the verification confirms it.
6. **Socket.IO events include scope**: All `config_event` emissions include `data.scope`.
7. **Dashboard integration document exists** at `docs-local/.../dashboard-integration-notes.md`.
8. **New test coverage**: `test_deployment_context.py`, `test_agent_manager_scoping.py`,
   integration tests for user-scope deploy/undeploy, all passing.
