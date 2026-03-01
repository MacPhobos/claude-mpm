# Test Development Plan: Scope Abstraction (CLI and API Paths)

**Author:** test-planner (Research Agent)
**Date:** 2026-02-28
**Branch:** agent_skill_scope_selection
**Informed by:** test-coverage.md, cli-path.md, api-path.md, implementation-strategies.md, devils-advocate.md

---

## Overview

This plan specifies every test to write for the scope abstraction work. It follows the **devil's advocate recommendation**: write characterization tests before any refactoring, then add tests for new behavior as each phase lands.

The plan covers five phases:

| Phase | Purpose | Must Complete Before |
|-------|---------|---------------------|
| 0 | Characterization tests (lock current behavior) | Any refactoring |
| 1 | `DeploymentContext` unit tests | CLI or API changes |
| 2 | CLI scope tests (agent + skills deploy paths) | Phase 1 |
| 3 | API scope parameter tests | Phase 1 |
| 4 | Integration / end-to-end tests | Phases 2 + 3 |

---

## New Fixtures (Required First)

These fixtures are needed by tests in Phases 0–4. Add them to `tests/conftest.py`.

### `project_scope_dirs`

```python
@pytest.fixture
def project_scope_dirs(tmp_path):
    """Standard PROJECT scope directory structure.

    Mimics: {project}/.claude/agents/, {project}/.claude/skills/,
            {project}/.claude-mpm/
    """
    project = tmp_path / "my_project"
    dirs = {
        "root": project,
        "agents": project / ".claude" / "agents",
        "skills": project / ".claude" / "skills",
        "archive": project / ".claude" / "agents" / "unused",
        "config": project / ".claude-mpm",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs
```

**File:** `tests/conftest.py`

---

### `user_scope_dirs`

```python
@pytest.fixture
def user_scope_dirs(tmp_path):
    """Standard USER scope directory structure (mocked home).

    Patches Path.home() to tmp_path/home so tests don't touch the real
    ~/.claude directory.

    Returns: (dirs_dict, fake_home_path)
    """
    fake_home = tmp_path / "home"
    dirs = {
        "home": fake_home,
        "agents": fake_home / ".claude" / "agents",
        "skills": fake_home / ".claude" / "skills",
        "archive": fake_home / ".claude" / "agents" / "unused",
        "config": fake_home / ".claude-mpm",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs, fake_home
```

**File:** `tests/conftest.py`

---

### `both_scopes`

```python
@pytest.fixture
def both_scopes(project_scope_dirs, user_scope_dirs):
    """Provides both scope directory structures for cross-scope isolation tests."""
    user_dirs, fake_home = user_scope_dirs
    return {
        "project": project_scope_dirs,
        "user": user_dirs,
        "fake_home": fake_home,
    }
```

**File:** `tests/conftest.py`

---

### `deployment_context_project` / `deployment_context_user`

```python
@pytest.fixture
def deployment_context_project(project_scope_dirs):
    """Pre-configured DeploymentContext for project scope."""
    from claude_mpm.core.deployment_context import DeploymentContext
    return DeploymentContext.from_project(project_scope_dirs["root"])


@pytest.fixture
def deployment_context_user(user_scope_dirs):
    """Pre-configured DeploymentContext for user scope (mocked home)."""
    from claude_mpm.core.deployment_context import DeploymentContext
    user_dirs, fake_home = user_scope_dirs
    with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
        yield DeploymentContext.from_user()
```

**File:** `tests/conftest.py`
**Note:** Only add these once `core/deployment_context.py` exists (Phase 1).

---

## Phase 0: Characterization Tests

> **Purpose:** Lock down current behavior before refactoring. These are regression anchors — if any Phase 0 test breaks after a refactor, the refactor changed behavior.
>
> **When to write:** Before ANY code changes. Write-first, commit before refactoring.

---

### Phase 0-A: CLI Configure Scope (Current Behavior)

**File:** `tests/cli/commands/test_configure_scope_characterization.py`

```
class TestConfigureScopeCurrentBehavior:
```

#### TC-0-01: `test_project_scope_sets_config_dir_under_project`
- **What it tests:** `ConfigureCommand.run()` with `scope="project"` sets `agent_manager.config_dir` to `{project_dir}/.claude-mpm/`
- **Setup:** `tmp_path` for project dir; `args = Namespace(scope="project", project_dir=str(tmp_path), ...)`; mock out `_run_interactive_tui` to prevent TUI from starting
- **Assertions:**
  - `cmd.agent_manager.config_dir == tmp_path / ".claude-mpm"`
  - `cmd.current_scope == "project"`
- **Phase:** 0 (characterization)

#### TC-0-02: `test_user_scope_sets_config_dir_under_home`
- **What it tests:** `scope="user"` sets `agent_manager.config_dir` to `~/.claude-mpm/`
- **Setup:** Same as above, `scope="user"`; patch `Path.home()` to `tmp_path / "fake_home"`
- **Assertions:**
  - `cmd.agent_manager.config_dir == tmp_path / "fake_home" / ".claude-mpm"`
- **Phase:** 0

#### TC-0-03: `test_missing_scope_attr_defaults_to_project`
- **What it tests:** When `args` has no `scope` attribute at all (not just `None`), defaults to `"project"`
- **Setup:** `args = Namespace()` (no `scope` key); mock `_run_interactive_tui`
- **Assertions:**
  - `cmd.current_scope == "project"`
- **Phase:** 0

#### TC-0-04: `test_deploy_agent_current_target_is_always_project_dir`
- **What it tests:** Documents the CURRENT (broken) behavior — `_deploy_single_agent()` uses `project_dir/.claude/agents/` even when `scope="user"`
- **Setup:** `scope="user"`; stub a remote agent (set `source_dict`); patch `shutil.copy2`
- **Assertions:**
  - `shutil.copy2` called with target in `project_dir / ".claude" / "agents"` (NOT in `~/.claude/agents/`)
- **Phase:** 0
- **Note:** This test is expected to FAIL after the Phase 2 fix is applied — at that point it becomes evidence of the behavior change

#### TC-0-05: `test_deploy_skill_current_target_is_always_cwd`
- **What it tests:** `_install_skill_from_dict()` writes to `Path.cwd() / ".claude" / "skills"` regardless of scope
- **Setup:** Mock `Path.cwd()` to a known tmp path; call `cmd._install_skill_from_dict(skill_dict)` directly
- **Assertions:**
  - Skill written to `{cwd}/.claude/skills/{deploy_name}/skill.md`
- **Phase:** 0
- **Note:** Also expected to fail after Phase 2 fix

#### TC-0-06: `test_scope_toggle_only_switches_current_scope_string`
- **What it tests:** `ConfigNavigation.switch_scope()` simply flips `current_scope` string — does NOT change deploy paths
- **Setup:** Create `ConfigNavigation` with `current_scope="project"`, call `switch_scope()`
- **Assertions:**
  - `navigation.current_scope == "user"` after one toggle
  - `navigation.current_scope == "project"` after two toggles
- **Phase:** 0

---

### Phase 0-B: CLI Skills Scope (Current Behavior)

**File:** `tests/cli/commands/test_configure_scope_characterization.py`

```
class TestSkillsScopeCurrentBehavior:
```

#### TC-0-07: `test_get_deployed_skill_ids_reads_from_cwd`
- **What it tests:** `_get_deployed_skill_ids()` always reads from `Path.cwd() / ".claude" / "skills"` regardless of `current_scope`
- **Setup:** Patch `Path.cwd()` to `tmp_path`; create two skill subdirs under `tmp_path / ".claude" / "skills"`
- **Assertions:**
  - Returned set contains the two skill names
- **Phase:** 0

#### TC-0-08: `test_uninstall_skill_removes_from_cwd`
- **What it tests:** `_uninstall_skill_by_name()` calls `shutil.rmtree` on `Path.cwd() / ".claude" / "skills" / name`
- **Setup:** Create real skill dir; patch `shutil.rmtree`
- **Assertions:**
  - `shutil.rmtree` called with path under `cwd`, not under `home`
- **Phase:** 0

---

### Phase 0-C: API Scope (Current Behavior)

**File:** `tests/services/config_api/test_scope_characterization.py`

```
class TestAPICurrentScopeAssumptions:
```

#### TC-0-09: `test_deploy_agent_handler_hardcodes_project_scope`
- **What it tests:** `agent_deployment_handler.deploy_agent()` always calls `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())`
- **Setup:** Mock the request body; patch `resolve_agents_dir`; patch `asyncio.to_thread`
- **Assertions:**
  - `resolve_agents_dir` called with `ConfigScope.PROJECT` as first arg
- **Phase:** 0

#### TC-0-10: `test_deploy_skill_handler_hardcodes_project_scope`
- **What it tests:** `skill_deployment_handler.deploy_skill()` uses `Path.cwd() / ".claude-mpm" / "configuration.yaml"` (hardcoded project path)
- **Setup:** Same as above but for skills handler
- **Assertions:**
  - Config path contains `Path.cwd()` component
- **Phase:** 0

#### TC-0-11: `test_config_routes_deployed_list_reads_from_cwd`
- **What it tests:** `GET /api/config/agents/deployed` reads from `Path.cwd() / ".claude" / "agents"`
- **Setup:** `AioHTTPTestCase` with server; put an agent file in `cwd/.claude/agents/`
- **Assertions:**
  - Response lists agents found in that directory
- **Phase:** 0

#### TC-0-12: `test_agent_manager_singleton_initializes_once_with_project_path`
- **What it tests:** `_get_agent_manager()` in `config_routes.py` creates singleton with `cwd/.claude/agents` path and never re-initializes
- **Setup:** Call `_get_agent_manager()` twice
- **Assertions:**
  - Same object returned both times
  - `agent_manager.project_dir` contains the cwd path (not home)
- **Phase:** 0

---

## Phase 1: DeploymentContext Unit Tests

> **Purpose:** Test the new `core/deployment_context.py` value object. These are pure unit tests — no mocking needed.
>
> **When to write:** Once `core/deployment_context.py` is created.

**File:** `tests/core/test_deployment_context.py`

```python
class TestDeploymentContextFactories:
class TestDeploymentContextPathProperties:
class TestDeploymentContextFromString:
class TestDeploymentContextImmutability:
class TestDeploymentContextEdgeCases:
```

---

### `TestDeploymentContextFactories`

#### TC-1-01: `test_from_project_uses_project_scope`
- **What it tests:** `DeploymentContext.from_project(path)` creates context with `scope=ConfigScope.PROJECT`
- **Setup:** `path = Path("/tmp/my_project")`
- **Assertions:**
  - `ctx.scope == ConfigScope.PROJECT`
  - `ctx.project_path == Path("/tmp/my_project")`
- **Phase:** 1

#### TC-1-02: `test_from_project_defaults_to_cwd_when_no_path`
- **What it tests:** `from_project()` without args uses `Path.cwd()` as project_path
- **Assertions:** `ctx.project_path == Path.cwd()`
- **Phase:** 1

#### TC-1-03: `test_from_user_uses_user_scope`
- **What it tests:** `DeploymentContext.from_user()` creates context with `scope=ConfigScope.USER`
- **Assertions:**
  - `ctx.scope == ConfigScope.USER`
- **Phase:** 1

#### TC-1-04: `test_from_string_project`
- **What it tests:** `from_string("project", path)` → `scope=PROJECT`
- **Assertions:** `ctx.scope == ConfigScope.PROJECT`
- **Phase:** 1

#### TC-1-05: `test_from_string_user`
- **What it tests:** `from_string("user")` → `scope=USER`
- **Assertions:** `ctx.scope == ConfigScope.USER`
- **Phase:** 1

#### TC-1-06: `test_from_string_invalid_raises_value_error`
- **What it tests:** `from_string("workspace")` raises `ValueError`
- **Assertions:** `pytest.raises(ValueError)`
- **Phase:** 1

#### TC-1-07: `test_from_string_empty_string_raises_value_error`
- **What it tests:** `from_string("")` raises `ValueError`
- **Phase:** 1

#### TC-1-08: `test_from_string_none_scope_raises_type_error`
- **What it tests:** `from_string(None)` raises `TypeError` or `ValueError`
- **Phase:** 1

---

### `TestDeploymentContextPathProperties`

#### TC-1-09: `test_agents_dir_project_scope`
- **What it tests:** `ctx.agents_dir == Path("/my/project/.claude/agents")`
- **Setup:** `ctx = DeploymentContext.from_project(Path("/my/project"))`
- **Phase:** 1

#### TC-1-10: `test_agents_dir_user_scope`
- **What it tests:** `ctx.agents_dir == Path.home() / ".claude" / "agents"`
- **Setup:** `ctx = DeploymentContext.from_user()`; patch `Path.home()`
- **Phase:** 1

#### TC-1-11: `test_skills_dir_project_scope`
- **What it tests:** `ctx.skills_dir == Path("/my/project/.claude/skills")`
- **Phase:** 1

#### TC-1-12: `test_skills_dir_user_scope`
- **What it tests:** `ctx.skills_dir == Path.home() / ".claude" / "skills"`
- **Phase:** 1

#### TC-1-13: `test_archive_dir_project_scope`
- **What it tests:** `ctx.archive_dir == Path("/my/project/.claude/agents/unused")`
- **Phase:** 1

#### TC-1-14: `test_archive_dir_user_scope`
- **What it tests:** `ctx.archive_dir == Path.home() / ".claude" / "agents" / "unused"`
- **Phase:** 1

#### TC-1-15: `test_config_dir_project_scope`
- **What it tests:** `ctx.config_dir == Path("/my/project/.claude-mpm")`
- **Phase:** 1

#### TC-1-16: `test_config_dir_user_scope`
- **What it tests:** `ctx.config_dir == Path.home() / ".claude-mpm"`
- **Phase:** 1

#### TC-1-17: `test_configuration_yaml_project_scope`
- **What it tests:** `ctx.configuration_yaml == Path("/my/project/.claude-mpm/configuration.yaml")`
- **Phase:** 1

#### TC-1-18: `test_configuration_yaml_user_scope`
- **What it tests:** `ctx.configuration_yaml == Path.home() / ".claude-mpm" / "configuration.yaml"`
- **Phase:** 1

---

### `TestDeploymentContextImmutability`

#### TC-1-19: `test_frozen_dataclass_cannot_modify_scope`
- **What it tests:** Attempting `ctx.scope = ConfigScope.USER` raises `FrozenInstanceError`
- **Phase:** 1

#### TC-1-20: `test_frozen_dataclass_cannot_modify_project_path`
- **What it tests:** Attempting `ctx.project_path = Path("/other")` raises `FrozenInstanceError`
- **Phase:** 1

---

### `TestDeploymentContextEdgeCases`

#### TC-1-21: `test_project_and_user_contexts_are_isolated`
- **What it tests:** `project_ctx.agents_dir` and `user_ctx.agents_dir` do not overlap
- **Setup:** Create both contexts; patch `Path.home()`
- **Assertions:** `project_ctx.agents_dir != user_ctx.agents_dir`
- **Phase:** 1

#### TC-1-22: `test_two_project_contexts_same_path_are_equal`
- **What it tests:** Two `DeploymentContext.from_project(same_path)` instances are equal (frozen dataclass equality)
- **Phase:** 1

#### TC-1-23: `test_context_is_hashable`
- **What it tests:** `DeploymentContext` instance can be used as dict key (frozen dataclasses are hashable)
- **Phase:** 1

---

## Phase 2: CLI Scope Tests

> **Purpose:** Verify that after the CLI fix, `--scope user` causes files to land in `~/.claude/agents/` and `~/.claude/skills/`.
>
> **When to write:** Once the CLI scope bug fix is implemented.

---

### Phase 2-A: Configure Command Agent Deploy

**File:** `tests/cli/commands/test_configure_scope_behavior.py`

```
class TestConfigureAgentScopeDeployment:
```

#### TC-2-01: `test_deploy_agent_project_scope_places_file_in_project_dir`
- **What it tests:** `scope="project"` → agent `.md` copied to `{project_dir}/.claude/agents/`
- **Setup:**
  - `project_scope_dirs` fixture
  - Build `ConfigureCommand`; set `current_scope = "project"` and `project_dir = project_scope_dirs["root"]`
  - Prepare `agent` with `source_dict = {"source_file": str(source_file)}`
  - Call `cmd._deploy_single_agent(agent)`
- **Assertions:**
  - `(project_scope_dirs["agents"] / "engineer.md").exists()`
  - `(user_scope_dirs["agents"] / "engineer.md").exists()` is **False**
- **Phase:** 2

#### TC-2-02: `test_deploy_agent_user_scope_places_file_in_home_dir`
- **What it tests:** `scope="user"` → agent `.md` copied to `~/.claude/agents/`
- **Setup:**
  - `user_scope_dirs` fixture; patch `Path.home()` to `fake_home`
  - `current_scope = "user"`
- **Assertions:**
  - `(user_dirs["agents"] / "engineer.md").exists()`
  - NOT in project dir
- **Phase:** 2

#### TC-2-03: `test_deploy_agent_project_scope_unchanged_from_before`
- **What it tests:** After the scope fix, project scope behavior is exactly the same as before (regression test vs. Phase 0-04)
- **Setup:** Same as TC-2-01
- **Assertions:** Identical to TC-0-04 (both should pass)
- **Phase:** 2

#### TC-2-04: `test_deploy_agent_missing_scope_defaults_to_project`
- **What it tests:** When `current_scope` is not set or is `None`, defaults to project behavior
- **Setup:** Do not set `current_scope` on command instance; call `_deploy_single_agent`
- **Assertions:** File goes to project dir, not home
- **Phase:** 2

#### TC-2-05: `test_deploy_agent_invalid_scope_raises_error`
- **What it tests:** If `current_scope` is set to `"workspace"` (invalid), raises `ValueError` or returns error `CommandResult`
- **Phase:** 2

#### TC-2-06: `test_run_scope_user_propagates_to_deploy`
- **What it tests:** Full `ConfigureCommand.run()` with `scope="user"` propagates scope into deploy operation (integration test at CLI layer)
- **Setup:** `args = Namespace(scope="user", project_dir=str(tmp_path), ...)` — drive through `run()` then call deploy
- **Assertions:**
  - `cmd.current_scope == "user"`
  - `cmd._ctx.agents_dir == fake_home / ".claude" / "agents"` (if DeploymentContext used)
- **Phase:** 2

---

### Phase 2-B: Configure Command Skills Deploy

**File:** `tests/cli/commands/test_configure_scope_behavior.py`

```
class TestConfigureSkillScopeDeployment:
```

#### TC-2-07: `test_install_skill_project_scope_places_dir_in_project`
- **What it tests:** `scope="project"` → skill installed under `{project_dir}/.claude/skills/`
- **Setup:** Set `current_scope = "project"` and `project_dir = project_scope_dirs["root"]`; call `_install_skill_from_dict(skill_dict)`
- **Assertions:**
  - `(project_scope_dirs["skills"] / "my-skill" / "skill.md").exists()`
  - Not in home dir
- **Phase:** 2

#### TC-2-08: `test_install_skill_user_scope_places_dir_in_home`
- **What it tests:** `scope="user"` → skill installed under `~/.claude/skills/`
- **Setup:** `user_scope_dirs`, `current_scope = "user"`
- **Assertions:**
  - `(user_dirs["skills"] / "my-skill" / "skill.md").exists()`
- **Phase:** 2

#### TC-2-09: `test_install_skill_missing_scope_defaults_to_project`
- **What it tests:** No scope set → installs to project dir
- **Phase:** 2

#### TC-2-10: `test_get_deployed_skill_ids_project_scope`
- **What it tests:** `_get_deployed_skill_ids()` with `scope="project"` lists skills from project dir
- **Setup:** Create two skill subdirs in `project_scope_dirs["skills"]`; set scope to project
- **Assertions:** Returns names of two skills
- **Phase:** 2

#### TC-2-11: `test_get_deployed_skill_ids_user_scope`
- **What it tests:** `_get_deployed_skill_ids()` with `scope="user"` lists skills from `~/.claude/skills/`
- **Setup:** Create skill subdirs in `user_scope_dirs["skills"]`; scope = "user"
- **Assertions:** Returns user-scope skills, not project-scope ones
- **Phase:** 2

#### TC-2-12: `test_uninstall_skill_project_scope`
- **What it tests:** `_uninstall_skill_by_name()` removes from project dir when scope=project
- **Setup:** Create skill in `project_scope_dirs["skills"]`
- **Assertions:** Skill directory deleted; user-scope skill untouched
- **Phase:** 2

#### TC-2-13: `test_uninstall_skill_user_scope`
- **What it tests:** `_uninstall_skill_by_name()` removes from `~/.claude/skills/` when scope=user
- **Phase:** 2

---

### Phase 2-C: Scope Validation

**File:** `tests/cli/commands/test_configure_scope_behavior.py`

```
class TestConfigureScopeValidation:
```

#### TC-2-14: `test_validate_args_accepts_project_scope`
- **What it tests:** `validate_args` passes with `scope="project"`
- **Phase:** 2

#### TC-2-15: `test_validate_args_accepts_user_scope`
- **What it tests:** `validate_args` passes with `scope="user"`
- **Phase:** 2

#### TC-2-16: `test_validate_args_rejects_invalid_scope`
- **What it tests:** `validate_args` returns error for `scope="workspace"`
- **Phase:** 2

#### TC-2-17: `test_validate_args_accepts_missing_scope_attr`
- **What it tests:** `validate_args` does not error when `scope` attribute missing from namespace
- **Phase:** 2

---

### Phase 2-D: Skills Command Scope

**File:** `tests/cli/commands/test_skills_scope.py`

```
class TestSkillsCommandScope:
```

#### TC-2-18: `test_skills_deploy_project_scope`
- **What it tests:** `SkillsManagementCommand` with `--scope=project` deploys to `{project}/.claude/skills/`
- **Setup:** `Namespace(skills_command="deploy", skill_name="my-skill", scope="project", ...)`; mock `SkillsDeployerService`
- **Assertions:**
  - `SkillsDeployerService.deploy_skills` called with path in project dir
- **Phase:** 2

#### TC-2-19: `test_skills_deploy_user_scope`
- **What it tests:** `--scope=user` deploys to `~/.claude/skills/`
- **Setup:** `Namespace(scope="user", ...)`; patch `Path.home()`; mock `SkillsDeployerService`
- **Assertions:**
  - Deploy path contains `home / ".claude" / "skills"`
- **Phase:** 2

#### TC-2-20: `test_skills_deploy_default_scope_is_project`
- **What it tests:** `SkillsManagementCommand` without explicit scope defaults to project
- **Setup:** `Namespace(scope=None, ...)` or no scope attribute
- **Assertions:**
  - Deploy path is project-level
- **Phase:** 2

#### TC-2-21: `test_skills_list_project_scope`
- **What it tests:** List command reads from project dir when `scope="project"`
- **Phase:** 2

#### TC-2-22: `test_skills_list_user_scope`
- **What it tests:** List command reads from user dir when `scope="user"`
- **Phase:** 2

---

## Phase 3: API Scope Tests

> **Purpose:** Verify that after the API scope work, the `scope` request parameter routes operations to the correct directory.
>
> **When to write:** Once the API scope parameter is implemented.

---

### Phase 3-A: Agent Deploy/Undeploy Scope

**File:** `tests/services/config_api/test_agent_deployment_scope.py`

```
class TestAgentDeploymentScope(AioHTTPTestCase):
```

#### TC-3-01: `test_deploy_agent_without_scope_defaults_to_project`
- **What it tests:** `POST /api/config/agents/deploy` with no `scope` field → uses project path
- **Setup:** `AioHTTPTestCase`; patch `AgentDeploymentService.deploy_agent`; patch `resolve_agents_dir`
- **Request:** `{"agent_name": "engineer"}`
- **Assertions:**
  - `resolve_agents_dir` called with `ConfigScope.PROJECT`
  - Response is `201`
- **Phase:** 3

#### TC-3-02: `test_deploy_agent_explicit_project_scope`
- **What it tests:** `{"agent_name": "engineer", "scope": "project"}` → uses project path
- **Phase:** 3

#### TC-3-03: `test_deploy_agent_user_scope`
- **What it tests:** `{"agent_name": "engineer", "scope": "user"}` → uses user home path
- **Request:** `{"agent_name": "engineer", "scope": "user"}`
- **Assertions:**
  - `resolve_agents_dir` called with `ConfigScope.USER`
  - File written to `~/.claude/agents/engineer.md`
- **Phase:** 3

#### TC-3-04: `test_deploy_agent_invalid_scope_returns_400`
- **What it tests:** `{"agent_name": "engineer", "scope": "workspace"}` → `400 VALIDATION_ERROR`
- **Assertions:**
  - Status `400`
  - `response["code"] == "VALIDATION_ERROR"`
  - `response["error"]` mentions invalid scope
- **Phase:** 3

#### TC-3-05: `test_deploy_agent_null_scope_treated_as_project`
- **What it tests:** `{"agent_name": "engineer", "scope": null}` → treated as project (or returns clear error)
- **Phase:** 3

#### TC-3-06: `test_undeploy_agent_without_scope_defaults_to_project`
- **What it tests:** `DELETE /api/config/agents/engineer` (no scope param) uses project path
- **Phase:** 3

#### TC-3-07: `test_undeploy_agent_user_scope_query_param`
- **What it tests:** `DELETE /api/config/agents/engineer?scope=user` removes from `~/.claude/agents/`
- **Assertions:**
  - `resolve_agents_dir` called with `ConfigScope.USER`
  - HTTP `200`
- **Phase:** 3

#### TC-3-08: `test_undeploy_agent_invalid_scope_returns_400`
- **What it tests:** `DELETE /api/config/agents/engineer?scope=bad` → `400`
- **Phase:** 3

---

### Phase 3-B: Skill Deploy/Undeploy Scope

**File:** `tests/services/config_api/test_skill_deployment_scope.py`

```
class TestSkillDeploymentScope(AioHTTPTestCase):
```

#### TC-3-09: `test_deploy_skill_without_scope_defaults_to_project`
- **What it tests:** `POST /api/config/skills/deploy` with no `scope` → project path
- **Request:** `{"skill_name": "my-skill"}`
- **Phase:** 3

#### TC-3-10: `test_deploy_skill_user_scope`
- **What it tests:** `{"skill_name": "my-skill", "scope": "user"}` → `~/.claude/skills/`
- **Assertions:**
  - `SkillsDeployerService.deploy_skills` called with `skills_dir = home / ".claude" / "skills"`
- **Phase:** 3

#### TC-3-11: `test_deploy_skill_invalid_scope_returns_400`
- **What it tests:** `{"skill_name": "my-skill", "scope": "invalid"}` → `400`
- **Phase:** 3

#### TC-3-12: `test_undeploy_skill_user_scope`
- **What it tests:** `DELETE /api/config/skills/my-skill?scope=user` → removes from user home
- **Phase:** 3

#### TC-3-13: `test_undeploy_skill_without_scope_defaults_to_project`
- **Phase:** 3

---

### Phase 3-C: Read Endpoints Scope

**File:** `tests/services/config_api/test_config_routes_scope.py`

```
class TestConfigReadRoutesScope(AioHTTPTestCase):
```

#### TC-3-14: `test_deployed_agents_without_scope_reads_project`
- **What it tests:** `GET /api/config/agents/deployed` (no scope) reads from project dir
- **Phase:** 3

#### TC-3-15: `test_deployed_agents_user_scope_query_param`
- **What it tests:** `GET /api/config/agents/deployed?scope=user` reads from `~/.claude/agents/`
- **Phase:** 3

#### TC-3-16: `test_deployed_skills_without_scope_reads_project`
- **Phase:** 3

#### TC-3-17: `test_deployed_skills_user_scope_query_param`
- **Phase:** 3

---

### Phase 3-D: Singleton Manager Scope Fix

**File:** `tests/services/config_api/test_config_routes_scope.py`

```
class TestAgentManagerSingletonScope:
```

#### TC-3-18: `test_agent_manager_singleton_reset_on_scope_change`
- **What it tests:** After the singleton fix, requests with different scopes use appropriate manager instances (not the same hardcoded one)
- **Setup:** Call `_get_agent_manager()` for project scope, then for user scope
- **Assertions:**
  - Project manager has project path
  - User manager has home path
  - They are different objects
- **Phase:** 3

#### TC-3-19: `test_agent_manager_project_singleton_cached`
- **What it tests:** Multiple project-scope requests reuse the same `AgentManager` instance
- **Phase:** 3

---

### Phase 3-E: Auto-Configure API Scope

**File:** `tests/services/config_api/test_autoconfig_scope.py`

```
class TestAutoConfigureAPIScope(AioHTTPTestCase):
```

#### TC-3-20: `test_autoconfig_detect_defaults_to_project_scope`
- **What it tests:** `POST /api/config/auto-configure/detect` uses project scope
- **Phase:** 3

#### TC-3-21: `test_autoconfig_apply_project_scope`
- **What it tests:** `POST /api/config/auto-configure/apply` with `scope=project` → agents to project dir
- **Phase:** 3

#### TC-3-22: `test_autoconfig_apply_user_scope`
- **What it tests:** `POST /api/config/auto-configure/apply` with `scope=user` → agents to home dir
- **Phase:** 3

#### TC-3-23: `test_autoconfig_missing_scope_defaults_to_project`
- **What it tests:** No scope field in request → project scope assumed
- **Phase:** 3

---

## Phase 4: Integration Tests

> **Purpose:** End-to-end verification that scope flows correctly from entry point to filesystem — no mocking of path resolution.
>
> **When to write:** Once both Phase 2 (CLI) and Phase 3 (API) are complete.

---

### Phase 4-A: CLI End-to-End

**File:** `tests/e2e/test_scope_deployment_e2e.py`

```
class TestCLIScopeDeploymentE2E:
```

#### TC-4-01: `test_cli_project_scope_agent_deploy_e2e`
- **What it tests:** Running `ConfigureCommand.run()` with `scope="project"` and a real agent source places the `.md` file in `{project}/.claude/agents/`
- **Setup:**
  - `project_scope_dirs` fixture for project dir
  - Create a real source agent `.md` file in a temp location
  - Set up `AgentConfig` with `source_dict` pointing to that file
  - Call `configure_cmd.run(args)` and then trigger deploy through `_deploy_single_agent`
- **Assertions:**
  - `(project_scope_dirs["agents"] / "engineer.md").exists()` → True
  - `(user_dirs["agents"] / "engineer.md").exists()` → False
- **Phase:** 4

#### TC-4-02: `test_cli_user_scope_agent_deploy_e2e`
- **What it tests:** `scope="user"` places file in `~/.claude/agents/` (fake home via fixture)
- **Setup:** `user_scope_dirs`; patch `Path.home()`
- **Assertions:**
  - `(user_dirs["agents"] / "engineer.md").exists()` → True
  - NOT in project dir
- **Phase:** 4

#### TC-4-03: `test_cli_project_scope_skill_deploy_e2e`
- **What it tests:** Skill install with `scope="project"` writes to `{project}/.claude/skills/`
- **Phase:** 4

#### TC-4-04: `test_cli_user_scope_skill_deploy_e2e`
- **What it tests:** Skill install with `scope="user"` writes to `~/.claude/skills/`
- **Phase:** 4

#### TC-4-05: `test_cli_deploy_and_list_project_scope_consistency`
- **What it tests:** After deploying with `scope="project"`, listing deployed agents returns the deployed one (from the same project path)
- **Assertions:** Consistency — deploy + detect agree on which directory
- **Phase:** 4

#### TC-4-06: `test_cli_deploy_and_list_user_scope_consistency`
- Same as TC-4-05 but for user scope
- **Phase:** 4

---

### Phase 4-B: Cross-Scope Isolation

**File:** `tests/e2e/test_scope_deployment_e2e.py`

```
class TestCrossScopeIsolation:
```

#### TC-4-07: `test_project_scope_deploy_does_not_affect_user_scope`
- **What it tests:** Deploying `engineer` to project scope does not create or modify `~/.claude/agents/engineer.md`
- **Setup:** `both_scopes` fixture; deploy to project
- **Assertions:**
  - Project dir has `engineer.md`
  - User dir does NOT have `engineer.md`
- **Phase:** 4

#### TC-4-08: `test_user_scope_deploy_does_not_affect_project_scope`
- Reverse of TC-4-07
- **Phase:** 4

#### TC-4-09: `test_disable_agent_project_scope_does_not_affect_user_scope_state`
- **What it tests:** `configure --disable-agent qa --scope project` updates `{project}/.claude-mpm/agent_states.json` but not `~/.claude-mpm/agent_states.json`
- **Phase:** 4

#### TC-4-10: `test_disable_agent_user_scope_does_not_affect_project_scope_state`
- Reverse of TC-4-09
- **Phase:** 4

---

### Phase 4-C: API End-to-End

**File:** `tests/e2e/test_scope_deployment_e2e.py`

```
class TestAPIDeploymentE2E:
```

#### TC-4-11: `test_api_deploy_agent_project_scope_e2e`
- **What it tests:** `POST /api/config/agents/deploy` with `scope=project` writes file to `{cwd}/.claude/agents/` on real filesystem
- **Setup:**
  - Start `UnifiedMonitorServer` test instance (or use `AioHTTPTestCase`)
  - `project_scope_dirs` fixture for temp project dir
  - Override `Path.cwd()` to project root
- **Assertions:**
  - `(project_dirs["agents"] / "engineer.md").exists()` → True
  - Response `201` with `verification.passed == True`
- **Phase:** 4

#### TC-4-12: `test_api_deploy_agent_user_scope_e2e`
- **What it tests:** `scope=user` in request → file in `~/.claude/agents/`
- **Phase:** 4

#### TC-4-13: `test_api_deploy_skill_project_scope_e2e`
- **Phase:** 4

#### TC-4-14: `test_api_deploy_skill_user_scope_e2e`
- **Phase:** 4

---

### Phase 4-D: Cross-Path Integration

**File:** `tests/e2e/test_scope_deployment_e2e.py`

```
class TestCrossPathIntegration:
```

#### TC-4-15: `test_cli_deploy_user_scope_then_api_reads_user_scope`
- **What it tests:** CLI deploys `engineer` to user scope; API `GET /api/config/agents/deployed?scope=user` then lists it
- **Setup:** `both_scopes`; CLI deploy → verify file; then API GET with `scope=user`
- **Assertions:**
  - API response lists `engineer`
  - API response with `scope=project` does NOT list it
- **Phase:** 4

#### TC-4-16: `test_api_deploy_user_scope_then_cli_detects_it`
- **What it tests:** API deploys to user scope; CLI's `get_deployed_agent_ids()` with user scope then detects it
- **Phase:** 4

---

## Test Execution Order and Dependencies

```
Phase 0 (characterization)
  └── Commit. Never modify these tests during refactoring.
  └── Any failing Phase 0 test after a commit = behavior change detected.

Phase 1 (DeploymentContext unit tests)
  └── Requires: core/deployment_context.py to exist

Phase 2 (CLI scope behavior)
  └── Requires: Phase 1 (DeploymentContext available for use)
  └── Note: TC-0-04 and TC-0-05 will now fail — update to document expected new behavior

Phase 3 (API scope parameter)
  └── Requires: Phase 1 + API scope parameter implemented
  └── TC-0-09, TC-0-10 will now fail — document expected new behavior

Phase 4 (E2E integration)
  └── Requires: Phase 2 + Phase 3 complete
```

---

## Test Naming Conventions

Follow the existing project convention observed in `test_configure_unit.py`:

```python
# Class: TestVerbNoun[Qualifier]
class TestConfigureScopeCurrentBehavior:

# Method: test_action_context_expected_outcome
def test_deploy_agent_user_scope_places_file_in_home_dir(self):
```

---

## File Location Summary

| File | Phase | Count |
|------|-------|-------|
| `tests/cli/commands/test_configure_scope_characterization.py` | 0 | 12 tests |
| `tests/services/config_api/test_scope_characterization.py` | 0 | 4 tests |
| `tests/core/test_deployment_context.py` | 1 | 23 tests |
| `tests/cli/commands/test_configure_scope_behavior.py` | 2 | 17 tests |
| `tests/cli/commands/test_skills_scope.py` | 2 | 5 tests |
| `tests/services/config_api/test_agent_deployment_scope.py` | 3 | 8 tests |
| `tests/services/config_api/test_skill_deployment_scope.py` | 3 | 5 tests |
| `tests/services/config_api/test_config_routes_scope.py` | 3 | 6 tests |
| `tests/services/config_api/test_autoconfig_scope.py` | 3 | 4 tests |
| `tests/e2e/test_scope_deployment_e2e.py` | 4 | 16 tests |
| **Total** | | **~100 tests** |

---

## Pytest Markers

Use existing project markers from `pyproject.toml`:

```python
@pytest.mark.unit          # Phases 0–2 unit tests
@pytest.mark.integration   # Phase 3 API tests (AioHTTPTestCase)
@pytest.mark.e2e           # Phase 4 end-to-end tests
@pytest.mark.regression    # Phase 0 characterization tests specifically
```

---

## Notes on AioHTTPTestCase Pattern

API tests use the existing `aiohttp.test_utils.AioHTTPTestCase` pattern. See `tests/test_config_routes.py` for the established boilerplate:

```python
from aiohttp.test_utils import AioHTTPTestCase

class TestAgentDeploymentScope(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        # register only the routes under test
        register_agent_deployment_routes(app, server_instance=mock_server)
        return app

    async def test_deploy_agent_user_scope(self):
        resp = await self.client.post("/api/config/agents/deploy",
                                      json={"agent_name": "engineer", "scope": "user"})
        self.assertEqual(resp.status, 201)
```

---

## Devil's Advocate Consideration

Per `devils-advocate.md`: Phase 0 tests are the highest priority. They must be written and committed before any code changes. The devil's advocate is correct that "zero test coverage means introducing a new abstraction is also risky" — Phase 0 prevents this.

For Phase 3 (API scope), the devil's advocate notes the singleton `_agent_manager` bug must be fixed first. TC-3-18 and TC-3-19 specifically target this. Do NOT skip these tests.

The devil's advocate also suggests that `DeploymentContext` may be premature if the dashboard has no scope UI. Phase 1 tests are written regardless — they test the value object itself, which is useful independent of the dashboard. The API scope tests (Phase 3) should be gated on a confirmed dashboard requirement.
