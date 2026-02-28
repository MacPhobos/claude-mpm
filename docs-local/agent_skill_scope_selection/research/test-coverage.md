# Test Coverage Analysis: CLI and API Configuration Paths

**Research Date:** 2026-02-28
**Author:** test-researcher (Research Agent)
**Task:** Analyze existing test coverage for both CLI and API configuration paths in claude-mpm

---

## Executive Summary

The project has **substantial test coverage** for CLI and API configuration paths, with a well-structured suite spanning unit, integration, and e2e tests. However, there are **critical gaps around scope selection** — particularly the interactive scope selection flow, scope propagation through the CLI→API boundary, and scope parameter handling in API routes. Any abstraction of scope selection into a unified `ScopeSelector` must fill these gaps.

---

## 1. Test File Inventory

### 1.1 CLI Configuration Tests

| File | Type | Coverage Focus |
|------|------|---------------|
| `tests/cli/commands/test_configure_unit.py` | Unit | 47+ tests for ConfigureCommand and SimpleAgentManager (85%+ coverage target) |
| `tests/cli/commands/test_configure_golden.py` | Golden/Regression | 20 golden tests capturing exact pre-refactoring behavior |
| `tests/cli/commands/test_config_command.py` | Unit | ConfigCommand (validate, view, status, auto, gitignore subcommands) |
| `tests/cli/commands/test_auto_configure.py` | Unit | AutoConfigureCommand basics |
| `tests/cli/commands/test_skills_cli.py` | Unit | SkillsManagementCommand (list, deploy, validate, update, info) |
| `tests/cli/test_agent_startup_config_respect.py` | Integration | Agent startup config loading |
| `tests/core/test_config_scope.py` | Unit + Integration | ConfigScope enum, all path resolver functions |

**Key CLI coverage:**
- **ConfigureCommand:** 47+ unit tests covering initialization, scope setting (project/user), agent enable/disable, export/import config, deferred changes, template discovery, path resolution
- **SimpleAgentManager:** Tests for state file CRUD, deferred change queue, enabled/disabled defaults
- **ConfigScope:** 30+ tests covering `resolve_agents_dir`, `resolve_skills_dir`, `resolve_archive_dir`, `resolve_config_dir` for both PROJECT and USER scopes

### 1.2 API Configuration Tests

| File | Type | Coverage Focus |
|------|------|---------------|
| `tests/test_config_routes.py` | Integration | All GET config API endpoints (aiohttp AioHTTPTestCase) |
| `tests/unit/services/monitor/routes/test_config_sources.py` | Integration | Source management CRUD routes (add/remove/update/sync) |
| `tests/services/config_api/test_autoconfig_integration.py` | Integration | Handler-to-service boundary, singleton lifecycle |
| `tests/services/config_api/test_autoconfig_defaults.py` | Integration | min_confidence defaults and async/sync boundary |
| `tests/services/config_api/test_autoconfig_skill_deployment.py` | Integration | Skill deployment across scopes |
| `tests/services/config_api/test_autoconfig_events.py` | Unit | Socket.IO event payload structure validation |
| `tests/e2e/test_autoconfig_full_flow.py` | E2E/Integration | Full auto-configure flow with filesystem integration |

**Key API coverage:**
- **`/api/config/project/summary`**: Success, service error, empty state
- **`/api/config/agents/deployed`**: List with core/non-core classification, service error, empty
- **`/api/config/sources/agent`**: POST (add/duplicate/invalid), DELETE (remove/not-found/protected), PATCH (update/disable-protected)
- **`/api/config/sources/skill`**: POST success/invalid-id/token-not-in-response
- **`/api/config/sources/{type}/sync`**: 202 response, validation error
- **`/api/config/sources/sync-all`**: 202 with source count
- **`/api/config/sources/sync-status`**: Idle state

### 1.3 Cross-Cutting Tests

| File | Type | Coverage Focus |
|------|------|---------------|
| `tests/conftest.py` | Infrastructure | Global fixtures (mock_config, temp_agent_dir, project_root, etc.) |
| `tests/agents/conftest.py` | Infrastructure | Agent-specific fixtures |
| `tests/services/config_api/test_autoconfig_skill_deployment.py` | Integration | Cross-scope skill isolation and path resolution |
| `tests/e2e/test_autoconfig_full_flow.py` | E2E | Filesystem integration, scope isolation, lazy singleton handling |

---

## 2. Coverage Analysis Per Code Path

### 2.1 CLI Path: `claude-mpm configure`

**Well-tested:**
- `ConfigureCommand.run()` — scope initialization from args, no-colors, all subcommand dispatch
- `ConfigureCommand.validate_args()` — conflicting navigation options, enable+disable conflict
- `ConfigureCommand._enable_agent_non_interactive()` / `_disable_agent_non_interactive()`
- `ConfigureCommand._list_agents_non_interactive()`
- `ConfigureCommand._export_config()` / `_import_config()`
- `ConfigureCommand._show_version_info()`
- `ConfigureCommand._parse_id_selection()` — single, range, comma-separated, mixed, invalid
- `ConfigureCommand._get_agent_template_path()` — project, user, system fallback
- `SimpleAgentManager` lifecycle — init, load/save states, enable/disable, deferred changes

**Scope-specific test coverage (CLI):**
- `test_run_scope_project` — Passes `scope="project"`, verifies `agent_manager.config_dir == tmp_path / ".claude-mpm"`
- `test_run_scope_user` — Passes `scope="user"`, verifies `agent_manager.config_dir == Path.home() / ".claude-mpm"`
- `test_scope_initialization_golden` — Default scope is `"project"`, `project_dir == Path.cwd()`, `agent_manager is None`
- `test_run_scope_setting_golden` — Golden-captures scope initialization with project dir

**Not tested in CLI path:**
- Interactive TUI scope selection (the prompt that asks "project" or "user?")
- Scope propagation when scope arg is missing/None
- Mixed scope operations (project agents + user skills, or vice versa)
- Skills scope handling in `SkillsManagementCommand` — **no `--scope` tests at all**

### 2.2 API Path: `/config` Endpoints

**Well-tested:**
- GET `/api/config/project/summary` — success, error, empty
- GET `/api/config/agents/deployed` — full agent list with core classification
- POST/DELETE/PATCH `/api/config/sources/agent` and `/skill` — full CRUD
- Sync routes — 202 response, validation, status polling
- Handler singleton lifecycle — creation, caching, reset-on-failure

**Scope-specific test coverage (API):**
- URL path `/api/config/project/summary` hard-codes "project" — **no USER scope equivalent route tested**
- No test sends scope as a query parameter or request body field
- `test_autoconfig_skill_deployment.py` verifies `ConfigScope.PROJECT` path resolution works but does not drive it through the API endpoint

**Not tested in API path:**
- Scope parameter in autoconfig API routes (if supported)
- Scope switching mid-flow via API
- User-scope deployments initiated via API
- API routes for user-scope agent/skill listing

### 2.3 ConfigScope Module

**Highly tested** (`tests/core/test_config_scope.py`):
- `ConfigScope.PROJECT == "project"` and `.USER == "user"` (backward compatibility with strings)
- `resolve_agents_dir` — PROJECT, USER, nested paths
- `resolve_skills_dir` — default (no args = PROJECT+cwd), PROJECT+explicit, USER, cross-scope isolation
- `resolve_archive_dir` — PROJECT, USER, is-subdirectory-of-agents
- `resolve_config_dir` — PROJECT, USER, user-ignores-project-path
- Cross-scope deployment isolation (no path overlap)
- Real filesystem operations with tmp_path (create directories, write files, read back)
- Auto-configure phase transitions (PROJECT scope consistent across phases)

This module is the most thoroughly tested part of the scope system.

---

## 3. Testing Patterns and Infrastructure

### 3.1 Test Patterns Used

**Unit Tests:**
- Mock-heavy: `unittest.mock.patch`, `MagicMock`, `Mock` for all external dependencies
- Fixture-per-method: `@pytest.fixture` for `tmp_path`, config directories, command instances
- Namespace-based args: `argparse.Namespace` constructed with all required fields

**Integration Tests:**
- `aiohttp.test_utils.AioHTTPTestCase` for API endpoint tests
- Real filesystem via `tmp_path` for path resolution tests
- Service singleton reset via `setup_method` (clears `_auto_config_manager = None`)
- Async/sync boundary testing with `AsyncMock` and `patch("asyncio.run")`

**E2E Tests:**
- Real project structure creation (pyproject.toml, requirements.txt, package.json)
- Full command flow from `AutoConfigureCommand.run()` to filesystem assertions
- Lazy singleton verification (`command._auto_config_manager is None` pre-access)
- Cross-scope filesystem isolation (PROJECT vs USER directories)

**Golden Tests:**
- Capture pre-refactoring behavior for safe refactoring
- Test exact file format (JSON indent=2, specific keys)
- Test exact state transitions and file contents

### 3.2 File System Mocking Patterns

```python
# Pattern 1: tmp_path for isolated real filesystem (most common)
def test_something(self, tmp_path):
    config_dir = tmp_path / ".claude-mpm"
    config_dir.mkdir(parents=True)
    manager = SimpleAgentManager(config_dir)

# Pattern 2: Patching Path.home() for user-scope tests
with patch("claude_mpm.core.config_scope.Path.home") as mock_home:
    mock_home.return_value = tmp_path / "fake_home"
    result = resolve_agents_dir(ConfigScope.USER, project_path)

# Pattern 3: Patching internal path attributes
agent_manager.templates_dir = mock_templates_dir

# Pattern 4: mock_open for file I/O without filesystem
with patch("builtins.open", mock_open(read_data=json.dumps(data))):
    ...
```

### 3.3 Test Infrastructure (conftest.py)

**Global `tests/conftest.py` provides:**
- `mock_config` — Mock with sensible config defaults (paths, services, features)
- `config_file` — Real tmp YAML file with version+socketio config
- `temp_agent_dir` — Real `.claude/agents/` with sample researcher.yml
- `temp_memory_dir` — Real `.claude/memory/` with index.json
- `project_root` — Standard project structure with src, tests, scripts, .claude/agents
- `mock_agent` / `mock_memory_manager` / `mock_session` — Pre-configured Mocks
- `mock_async_client` / `async_service` — AsyncMock for async services
- `mock_argparse_namespace` — Base args namespace
- `cli_runner` — Click `CliRunner`
- `sample_yaml_content` / `sample_json_content` — Content fixtures
- `mock_socketio_server` / `mock_socketio_client` — Socket.IO fixtures
- `clean_env` / `test_env` — Env variable management
- `mock_process` / `mock_subprocess` — Process/subprocess mocks
- `mock_logger` — Logging mock
- `event_loop` — Async event loop per function

**Helper functions:**
- `create_mock_file(path, content)` — Create file with content
- `create_mock_agent_file(agent_dir, name, **kwargs)` — Create agent YAML

**Pytest markers:**
- `unit`, `integration`, `e2e`, `regression`, `socketio`, `hook`, `serial`
- `behavioral`, `delegation`, `tools`, `circuit_breaker`, `workflow`
- `evidence`, `file_tracking`, `memory`, `performance`
- `critical`, `high`, `medium`, `low`

**Test command configuration:**
```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--tb=short", "--strict-markers", "--disable-warnings"]
asyncio_mode = "auto"
norecursedirs = ["archive", "benchmarks", "manual", "stress", ".*", "_*"]
```

---

## 4. Identified Gaps in Test Coverage

### 4.1 Critical Gaps (Block Abstraction Work)

**GAP-1: Interactive scope selection flow — NO TESTS**
- The interactive TUI prompt asking user to choose "project" vs "user" scope is not tested
- No tests verify that prompt input maps correctly to `ConfigScope.PROJECT` or `ConfigScope.USER`
- No tests for the decision logic: "default to project when in a git repo, user otherwise"
- No tests for invalid input handling at the prompt

**GAP-2: Skills CLI — no scope parameter tests**
- `test_skills_cli.py` has zero `--scope` tests
- The `SkillsManagementCommand` may accept `--scope` but it's not tested
- No test verifies skills deploy to project vs user directory based on scope arg

**GAP-3: API scope parameter — no tests**
- API endpoints like `/api/config/project/summary` have project hard-coded in the URL
- No test verifies a scope query parameter or request body scope field
- No API test deploys to or reads from user scope via HTTP

**GAP-4: Unified scope propagation — no tests**
- No test verifies that a scope choice in the CLI propagates correctly through:
  `CLI args → scope variable → file path resolution → agent manager config dir`
  ...for BOTH agents AND skills in the same operation
- Current tests verify CLI scope → agent path OR scope → skills path independently, not together

### 4.2 High-Priority Gaps (Should Add for Abstraction)

**GAP-5: Scope fallback/default behavior**
- No test verifies scope default when `--scope` arg is missing from args namespace
- `test_configure_unit.py` always passes explicit `scope="project"` or `scope="user"`
- Edge case: `scope=None` in Namespace, missing attribute

**GAP-6: Scope validation**
- No test verifies what happens with `--scope=invalid-scope`
- No test verifies `validate_args` rejects invalid scope values
- The `ConfigCommand._validate_config` tests don't test scope validation

**GAP-7: User scope in auto-configure CLI**
- All `test_autoconfig_*.py` tests use `project_path` with PROJECT scope implicitly
- No test calls auto-configure with `scope="user"` to verify user home deployment
- `test_autoconfig_full_flow.py::test_full_flow_cross_scope_deployment` partially covers this but verifies service call args, not actual filesystem paths

**GAP-8: Scope-qualified configure command golden tests**
- `test_configure_golden.py` only has one scope test (GOLDEN TEST 9) for project scope
- No golden test for user scope scope-setting behavior
- Missing: golden test for scope switching between operations

### 4.3 Lower-Priority Gaps

**GAP-9: ConfigScope integration with configure command**
- `configure.py` uses raw string `"project"/"user"` comparisons internally
- `core/config_scope.py::ConfigScope` is tested separately
- No test verifies configure.py uses ConfigScope functions instead of raw paths

**GAP-10: Cross-scope agent/skill state consistency**
- No test verifies that disabling an agent in project scope doesn't affect user scope state
- No test for "agent enabled in user scope but disabled in project scope"

**GAP-11: Config export/import scope preservation**
- `test_export_config_golden` verifies `"scope"` key in exported JSON
- No test verifies that importing a config with `"scope": "user"` applies to user paths

---

## 5. Recommendations for Testing the Unified Abstraction

### 5.1 New Test File: `tests/core/test_scope_selector.py`

For a unified `ScopeSelector` abstraction, add:

```python
class TestScopeSelector:
    """Tests for unified scope selection abstraction."""

    def test_project_scope_selection_from_args(self):
        """Scope selector returns PROJECT when args.scope == 'project'."""

    def test_user_scope_selection_from_args(self):
        """Scope selector returns USER when args.scope == 'user'."""

    def test_missing_scope_arg_defaults_to_project(self):
        """When scope attribute missing from Namespace, defaults to PROJECT."""

    def test_invalid_scope_raises_value_error(self):
        """Invalid scope string raises ValueError with helpful message."""

    def test_scope_selector_returns_config_scope_enum(self):
        """Selector returns ConfigScope enum, not raw string."""

    def test_interactive_scope_prompt_project_input(self, monkeypatch):
        """Interactive prompt maps 'p'/'project'/'1' to PROJECT."""

    def test_interactive_scope_prompt_user_input(self, monkeypatch):
        """Interactive prompt maps 'u'/'user'/'2' to USER."""

    def test_interactive_scope_prompt_invalid_retries(self, monkeypatch):
        """Invalid input triggers retry prompt."""

    def test_scope_selector_from_environment_variable(self, monkeypatch):
        """CLAUDE_MPM_SCOPE env var overrides default."""
```

### 5.2 Extended Tests: `tests/cli/commands/test_configure_unit.py`

Add to existing configure unit tests:

```python
def test_run_scope_missing_defaults_to_project(self):
    """scope attribute not present in Namespace defaults to project."""

def test_run_scope_invalid_returns_error(self):
    """Invalid scope value returns error CommandResult."""

def test_configure_uses_config_scope_for_path_resolution(self):
    """Verify configure.py uses ConfigScope functions, not raw Path concatenation."""
```

### 5.3 Extended Tests: `tests/cli/commands/test_skills_cli.py`

Add scope tests:

```python
class TestSkillsScope:
    def test_deploy_project_scope(self, tmp_path):
        """Skills deploy to project/.claude/skills with --scope=project."""

    def test_deploy_user_scope(self, tmp_path):
        """Skills deploy to ~/.claude/skills with --scope=user."""

    def test_deploy_default_scope_is_project(self, tmp_path):
        """Default scope for skills deploy is project."""
```

### 5.4 API Tests: Scope Parameter Support

If the abstraction exposes scope via API:

```python
class TestAutoConfigureScope(AioHTTPTestCase):
    async def test_autoconfig_post_project_scope(self):
        """POST /api/config/autoconfig with scope=project uses project paths."""

    async def test_autoconfig_post_user_scope(self):
        """POST /api/config/autoconfig with scope=user uses user home paths."""

    async def test_autoconfig_missing_scope_defaults_to_project(self):
        """Missing scope param defaults to project scope."""
```

### 5.5 Test Infrastructure Updates

**New fixtures to add to `tests/conftest.py`:**

```python
@pytest.fixture
def project_scope_dirs(tmp_path):
    """Standard PROJECT scope directory structure."""
    dirs = {
        "agents": tmp_path / "project" / ".claude" / "agents",
        "skills": tmp_path / "project" / ".claude" / "skills",
        "config": tmp_path / "project" / ".claude-mpm",
    }
    for d in dirs.values():
        d.mkdir(parents=True)
    return dirs

@pytest.fixture
def user_scope_dirs(tmp_path):
    """Standard USER scope directory structure (mocked home)."""
    dirs = {
        "agents": tmp_path / "home" / ".claude" / "agents",
        "skills": tmp_path / "home" / ".claude" / "skills",
        "config": tmp_path / "home" / ".claude-mpm",
    }
    for d in dirs.values():
        d.mkdir(parents=True)
    return dirs, tmp_path / "home"
```

**New conftest.py fixtures for scope testing:**
- `@pytest.fixture def both_scopes(project_scope_dirs, user_scope_dirs)` — provides both scope directories for cross-scope isolation tests

---

## 6. Summary Assessment

| Area | Coverage Level | Priority for Abstraction |
|------|---------------|--------------------------|
| ConfigScope module (path resolution) | **Excellent** (30+ tests) | Foundational — reuse as-is |
| CLI configure scope setting (project/user args) | **Good** (4 direct tests) | Extend for missing attr/invalid |
| CLI configure agent state management | **Excellent** (40+ tests) | Reuse patterns |
| API GET config routes | **Good** (15+ tests) | Add scope param tests |
| API source mutation routes | **Good** (16 tests) | Minimal scope impact |
| Interactive scope selection TUI | **None** | Must add |
| Skills CLI scope | **None** | Must add |
| Auto-configure scope propagation | **Partial** (path resolution tested, not CLI-driven) | Extend |
| Cross-scope state isolation | **Partial** (filesystem isolation tested in e2e) | Add unit-level |
| Scope validation/error handling | **None** | Must add |

**Verdict:** The existing test suite provides a solid foundation of patterns and infrastructure to build upon. The critical gap is **interactive scope selection** — this is the core of the proposed abstraction and has zero test coverage. Any unified `ScopeSelector` must be driven by new tests that cover: interactive prompts, arg parsing, env variables, defaults, and validation, all wired through both CLI commands (configure and skills) and the API layer.
