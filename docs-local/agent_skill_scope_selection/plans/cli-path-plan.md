# CLI Path Implementation Plan: Scope-Aware Agent & Skill Deployment

**Author:** cli-planner (Research Agent)
**Date:** 2026-02-28
**Branch:** agent_skill_scope_selection
**Based on research:** cli-path.md, implementation-strategies.md, abstraction-opportunities.md, test-coverage.md, devils-advocate.md

---

## Executive Summary

This plan fixes the CLI scope bug (user scope not affecting file deployment) and introduces a `DeploymentContext` abstraction as the team's chosen Strategy 1. The work is organized into 7 sequential phases. Phases 1–3 carry zero behavioral change; Phases 4–5 fix the actual bug; Phase 6 retires dead code; Phase 7 adds new `--scope` capability to the `skills` command.

**Core issue:** When a user runs `claude-mpm configure --scope user`, agent files still deploy to `{cwd}/.claude/agents/` and skills still deploy to `{cwd}/.claude/skills/`. The scope flag silently affects only metadata (`agent_states.json` location), not file deployment.

**Strategy (as specified):** Strategy 1 — `DeploymentContext` frozen dataclass (~50 lines) in `core/deployment_context.py`.

**Out of scope:** API path changes, archive feature removal, dashboard changes.

---

## The Bug in Numbers

| Code Site | File:Line | Hardcoded Path | Should Use |
|-----------|-----------|----------------|------------|
| `_deploy_single_agent()` | `configure.py:3073` | `self.project_dir / ".claude" / "agents"` | `self._ctx.agents_dir` |
| `_get_deployed_skill_ids()` | `configure.py:1279` | `Path.cwd() / ".claude" / "skills"` | `self._ctx.skills_dir` |
| `_install_skill()` | `configure.py:1301` | `Path.cwd() / ".claude" / "skills" / skill.skill_id` | `self._ctx.skills_dir / skill.skill_id` |
| `_install_skill_from_dict()` | `configure.py:1344` | `Path.cwd() / ".claude" / "skills" / deploy_name` | `self._ctx.skills_dir / deploy_name` |
| `_uninstall_skill()` | `configure.py:1321` | `Path.cwd() / ".claude" / "skills" / skill.skill_id` | `self._ctx.skills_dir / skill.skill_id` |
| `_uninstall_skill_by_name()` | `configure.py:1360` | `Path.cwd() / ".claude" / "skills" / skill_name` | `self._ctx.skills_dir / skill_name` |

---

## Phase 1: Pre-Refactor Characterization Tests

### Objective
Write tests that characterize the **current** behavior before touching any production code. These tests become the safety net for all subsequent refactoring. They document the bug (and will initially FAIL for user-scope deployment tests, which is expected — they define the target behavior).

### Why First
The devil's advocate research correctly identified that refactoring untested code without first capturing behavior is risky. We write characterization tests before any refactoring so we know when we've preserved behavior (and when we've fixed the bug).

### Dependencies
None — this phase stands alone.

### Tasks

#### Task 1.1: Add scope missing/invalid tests to `test_configure_unit.py`

**File:** `tests/cli/commands/test_configure_unit.py`

**Functions to add:**
```python
def test_run_scope_missing_defaults_to_project(self, tmp_path):
    """GAP-5: When scope attribute is absent from Namespace, defaults to 'project'."""
    # Create args Namespace without 'scope' attribute at all
    args = argparse.Namespace(project_dir=str(tmp_path))
    cmd = ConfigureCommand()
    # Should not raise AttributeError; current_scope must be "project"
    cmd.current_scope  # verify default
    # Acceptance: no exception; cmd.current_scope == "project"

def test_run_scope_defaults_to_project_when_none(self, tmp_path):
    """GAP-5: scope=None in Namespace defaults to 'project'."""

def test_deploy_single_agent_project_scope_deploys_to_project_dir(self, tmp_path):
    """Current behavior: agent deploys to project_dir/.claude/agents/ (project scope)."""
    # Setup agent with source_dict pointing to tmp source file
    # Run _deploy_single_agent with scope="project"
    # Assert file appears in tmp_path/.claude/agents/
    # Acceptance: file exists at project_dir/.claude/agents/{name}.md

def test_deploy_single_agent_user_scope_should_deploy_to_home(self, tmp_path, monkeypatch):
    """TARGET behavior (currently broken): agent should deploy to ~/.claude/agents/ with user scope.

    This test defines the fix target. Initially FAILS (documents the bug).
    After Phase 4 implementation, this test PASSES.
    """
    # monkeypatch Path.home() → tmp_path / "fake_home"
    # Setup command with scope="user"
    # Run _deploy_single_agent
    # Assert file appears in fake_home/.claude/agents/
    # NOTE: Mark with @pytest.mark.xfail(reason="bug fix pending Phase 4") initially

def test_install_skill_project_scope_deploys_to_project_dir(self, tmp_path):
    """Current behavior: skill deploys to cwd/.claude/skills/ (project scope)."""

def test_install_skill_user_scope_should_deploy_to_home(self, tmp_path, monkeypatch):
    """TARGET behavior (currently broken). Initially XFAIL."""
```

**Acceptance criteria:**
- All new tests exist and run without errors
- Project-scope tests PASS (document current working behavior)
- User-scope deployment tests are marked `@pytest.mark.xfail(strict=True, reason="scope bug — fix in Phase 4/5")` and DO fail (confirm the bug exists)
- No existing tests broken

#### Task 1.2: Add scope tests for `_get_deployed_skill_ids()`

**File:** `tests/cli/commands/test_configure_unit.py`

**Functions to add:**
```python
def test_get_deployed_skill_ids_reads_project_dir(self, tmp_path, monkeypatch):
    """_get_deployed_skill_ids() reads from cwd/.claude/skills/ (current behavior)."""
    # monkeypatch Path.cwd() → tmp_path
    # Create tmp_path/.claude/skills/my-skill/ directory
    # Call _get_deployed_skill_ids()
    # Assert "my-skill" in result

def test_get_deployed_skill_ids_user_scope_reads_home(self, tmp_path, monkeypatch):
    """TARGET: with user scope, reads from ~/.claude/skills/ (currently broken, XFAIL)."""
```

**Acceptance criteria:** Same as 1.1 — project scope PASSes, user scope marked XFAIL.

#### Task 1.3: Add `TestScopeSelector` in `tests/core/test_scope_selector.py`

**File (new):** `tests/core/test_scope_selector.py`

This is a placeholder test file that documents the expected `DeploymentContext` interface before the class is written (TDD-style).

```python
class TestDeploymentContextInterface:
    """Documents the expected DeploymentContext interface (TDD pre-Phase 2 tests)."""

    def test_from_string_project_resolves_agents_dir(self, tmp_path):
        """from_string('project', path).agents_dir == path/.claude/agents"""
        # Import will fail until Phase 2 — mark as xfail with importorskip

    def test_from_string_user_resolves_home_agents_dir(self, tmp_path, monkeypatch):
        """from_string('user').agents_dir == ~home/.claude/agents"""

    def test_from_string_project_resolves_skills_dir(self, tmp_path):
        """from_string('project', path).skills_dir == path/.claude/skills"""

    def test_from_string_user_resolves_home_skills_dir(self, tmp_path, monkeypatch):
        """from_string('user').skills_dir == ~home/.claude/skills"""

    def test_from_string_invalid_scope_raises(self):
        """from_string('invalid') raises ValueError."""

    def test_config_dir_project(self, tmp_path):
        """config_dir for project == path/.claude-mpm"""

    def test_config_dir_user(self, tmp_path, monkeypatch):
        """config_dir for user == ~home/.claude-mpm"""
```

**Acceptance criteria:** All tests in this file are marked `xfail` until Phase 2 completes them.

#### Task 1.4: Add `TestSkillsScopeGap` in `tests/cli/commands/test_skills_cli.py`

**File:** `tests/cli/commands/test_skills_cli.py`

```python
class TestSkillsScope:
    """GAP-2: Skills CLI has no --scope tests. These document current gap and target."""

    def test_skills_command_has_no_scope_arg_currently(self):
        """Document current state: SkillsManagementCommand.run() ignores scope."""
        # Verify args.scope is not read in skills.py run()
        # This is the gap that Phase 7 will close.
```

**Acceptance criteria:** Test file updated, gap documented.

### Phase 1 Milestone

**Done looks like:**
- All new test files/classes exist and run (`pytest tests/cli/commands/test_configure_unit.py -k "scope" -v`)
- Project-scope deploy tests PASS
- User-scope deploy tests FAIL with `xfail` marker (no noise in CI)
- No regressions in existing test suite

### Phase 1 Risk Assessment

**Low risk.** Tests only — no production code changes.

---

## Phase 2: Create `DeploymentContext`

### Objective

Add `src/claude_mpm/core/deployment_context.py` as a new pure-value frozen dataclass (~50 lines). No existing files are modified. This is additive only.

### Dependencies
- Phase 1 complete (characterization tests written)

### Tasks

#### Task 2.1: Create `core/deployment_context.py`

**File (new):** `src/claude_mpm/core/deployment_context.py`

**Exact content:**

```python
"""Immutable deployment context capturing scope and project path.

WHY: Provides a single object that encapsulates scope + project_path,
allowing both CLI and (in future) API to derive consistent deployment
paths without scattered if/else scope checks.

DESIGN: Frozen dataclass (immutable) so it's safe to pass through
multiple layers without mutation risk. Pure properties delegate to
config_scope.py's canonical resolve_* functions — no duplication of
path logic.

NOTE: This wraps core/config_scope.py. Do not add path resolution
logic here; add it in config_scope.py and expose via a property.
"""

from dataclasses import dataclass
from pathlib import Path

from .config_scope import ConfigScope, resolve_agents_dir, resolve_skills_dir
from .config_scope import resolve_config_dir


@dataclass(frozen=True)
class DeploymentContext:
    """Immutable context capturing scope and project path.

    Created once at the CLI entry point (ConfigureCommand.run()) and
    carried as self._ctx through all subsequent operations. Recreated
    when scope changes interactively (switch_scope).

    Thread-safe (frozen dataclass) for future API use.
    """

    scope: ConfigScope
    project_path: Path

    @classmethod
    def from_project(cls, project_path: Path = None) -> "DeploymentContext":
        """Factory for explicit project scope."""
        return cls(scope=ConfigScope.PROJECT, project_path=project_path or Path.cwd())

    @classmethod
    def from_user(cls, project_path: Path = None) -> "DeploymentContext":
        """Factory for user scope. project_path stored but unused for path resolution."""
        return cls(scope=ConfigScope.USER, project_path=project_path or Path.cwd())

    @classmethod
    def from_string(cls, scope_str: str, project_path: Path = None) -> "DeploymentContext":
        """Backward-compatible factory for CLI (which passes raw 'project'/'user' strings).

        Args:
            scope_str: 'project' or 'user'
            project_path: Project root; defaults to Path.cwd()

        Raises:
            ValueError: If scope_str is not 'project' or 'user'
        """
        scope = ConfigScope(scope_str)  # raises ValueError for invalid strings
        return cls(scope=scope, project_path=project_path or Path.cwd())

    @property
    def agents_dir(self) -> Path:
        """Claude Code agents deployment directory."""
        return resolve_agents_dir(self.scope, self.project_path)

    @property
    def skills_dir(self) -> Path:
        """Claude Code skills deployment directory."""
        return resolve_skills_dir(self.scope, self.project_path)

    @property
    def config_dir(self) -> Path:
        """MPM configuration directory (.claude-mpm/)."""
        return resolve_config_dir(self.scope, self.project_path)
```

**What it adds:**
- 1 new file, ~65 lines
- 3 class methods: `from_project`, `from_user`, `from_string`
- 3 properties: `agents_dir`, `skills_dir`, `config_dir`
- Zero changes to any existing file

**What is NOT in this class:**
- `archive_dir` — archive feature is out of scope
- `configuration_yaml` — API concern, not CLI
- No path resolution logic — delegates to `config_scope.py`

#### Task 2.2: Export DeploymentContext from core package

**File:** `src/claude_mpm/core/__init__.py`

**Change:** Add to imports:
```python
from .deployment_context import DeploymentContext
```

**Risk:** If `core/__init__.py` has a complex import chain, check for circular imports first. Mitigation: use lazy import in `__init__.py` if needed.

#### Task 2.3: Update TDD tests from Phase 1 to remove xfail markers

**File:** `tests/core/test_scope_selector.py`

Now that `DeploymentContext` exists, remove `xfail` markers from Task 1.3 tests and run them green.

Add more thorough tests:
```python
def test_frozen_dataclass_immutable():
    """DeploymentContext fields cannot be mutated after creation."""
    ctx = DeploymentContext.from_project(Path("/my/project"))
    with pytest.raises(FrozenInstanceError):
        ctx.scope = ConfigScope.USER

def test_from_string_project_is_same_as_from_project(tmp_path):
    """from_string('project') and from_project() produce identical results."""
    ctx1 = DeploymentContext.from_string("project", tmp_path)
    ctx2 = DeploymentContext.from_project(tmp_path)
    assert ctx1 == ctx2

def test_scope_comparison_with_string():
    """ConfigScope.PROJECT == 'project' (str enum backward compat)."""
    ctx = DeploymentContext.from_project(Path("/my/proj"))
    assert ctx.scope == "project"  # backward compat check
```

**Acceptance criteria:**
- All tests in `tests/core/test_scope_selector.py` PASS (no xfail)
- `from_string("invalid")` raises `ValueError`
- Frozen dataclass raises `FrozenInstanceError` on mutation attempt
- `agents_dir` for project scope == `path/.claude/agents`
- `agents_dir` for user scope == `Path.home() / ".claude" / "agents"`

### Phase 2 Milestone

**Done looks like:**
- `src/claude_mpm/core/deployment_context.py` exists and is importable
- All tests in `tests/core/test_scope_selector.py` pass
- No existing test suite regressions (run full test suite)
- **No behavioral change** — existing code does not yet use `DeploymentContext`

### Phase 2 Risk Assessment

**Minimal risk.** Additive only. The only risk is circular import if `core/__init__.py` has import-order issues — check first, use lazy import if needed.

---

## Phase 3: Wire DeploymentContext into `ConfigureCommand.run()` — Config Path Only

### Objective

Replace the ad-hoc `if self.current_scope == "project"` block in `ConfigureCommand.run()` with `DeploymentContext.from_string()`. At this phase, **only `config_dir` is changed** — agent and skill deployment paths remain unchanged. This is a pure refactor (zero behavioral change).

### Dependencies
- Phase 2 complete (DeploymentContext exists and tested)

### Tasks

#### Task 3.1: Update `ConfigureCommand.run()` to create `self._ctx`

**File:** `src/claude_mpm/cli/commands/configure.py`

**Current code (lines 182–194):**
```python
def run(self, args) -> CommandResult:
    # Set configuration scope
    self.current_scope = getattr(args, "scope", "project")
    if getattr(args, "project_dir", None):
        self.project_dir = Path(args.project_dir)

    # Initialize agent manager and behavior manager with appropriate config directory
    if self.current_scope == "project":
        config_dir = self.project_dir / ".claude-mpm"
    else:
        config_dir = Path.home() / ".claude-mpm"
    self.agent_manager = SimpleAgentManager(config_dir)
    self.behavior_manager = BehaviorManager(
        config_dir, self.current_scope, self.console
    )
```

**New code:**
```python
def run(self, args) -> CommandResult:
    # Set configuration scope — keep current_scope string for backward compat
    scope_str = getattr(args, "scope", "project")
    self.current_scope = scope_str
    if getattr(args, "project_dir", None):
        self.project_dir = Path(args.project_dir)

    # Create immutable deployment context (single source of truth for paths)
    self._ctx = DeploymentContext.from_string(scope_str, self.project_dir)

    # config_dir for agent state and behavior files
    config_dir = self._ctx.config_dir
    self.agent_manager = SimpleAgentManager(config_dir)
    self.behavior_manager = BehaviorManager(
        config_dir, self.current_scope, self.console
    )
```

**Import to add at top of configure.py:**
```python
from ...core.deployment_context import DeploymentContext
```

**What changes:** The `if/else` block for `config_dir` is replaced by `self._ctx.config_dir`. Behavior is identical — `DeploymentContext` calls the same `resolve_config_dir()` function that the API already uses.

#### Task 3.2: Initialize `self._ctx` in `__init__()` with a default

**File:** `src/claude_mpm/cli/commands/configure.py`, `__init__()` method (line 68)

**Add to `__init__`:**
```python
self._ctx = DeploymentContext.from_project(Path.cwd())  # Default; overwritten in run()
```

This ensures `self._ctx` is never `None` and has a safe default before `run()` is called.

#### Task 3.3: Update `_switch_scope()` to recreate `self._ctx`

**File:** `src/claude_mpm/cli/commands/configure.py`, lines 1436–1440

**Current code:**
```python
def _switch_scope(self) -> None:
    """Switch between project and user scope."""
    self.navigation.switch_scope()
    # Sync scope back from navigation
    self.current_scope = self.navigation.current_scope
```

**New code:**
```python
def _switch_scope(self) -> None:
    """Switch between project and user scope."""
    self.navigation.switch_scope()
    # Sync scope back from navigation and recreate deployment context
    self.current_scope = self.navigation.current_scope
    self._ctx = DeploymentContext.from_string(self.current_scope, self.project_dir)
    # Reinitialize managers that depend on config_dir
    config_dir = self._ctx.config_dir
    self.agent_manager = SimpleAgentManager(config_dir)
    # Note: behavior_manager also needs reinit if behavior dir changes
    self.behavior_manager = BehaviorManager(config_dir, self.current_scope, self.console)
    # Reset lazy-initialized managers that cache scope-dependent data
    self._agent_display = None
    self._persistence = None
    self._navigation = None   # Will reinit with synced scope
    self._template_editor = None
    self._startup_manager = None
```

**Why:** `DeploymentContext` is frozen (immutable). When scope switches, we must create a new context. Lazy-initialized sub-managers that hold references to `current_scope` or `project_dir` also need reset.

**Risk note:** Resetting `self._navigation = None` means the navigation object (which holds `current_scope`) is destroyed and recreated. We must ensure the navigation property reinitializes correctly. Check: `ConfigNavigation.__init__` takes `console` and `project_dir` (line 125 of configure.py). The new navigation will have `current_scope = "project"` by default — we must set it after:

```python
    # After reset, sync scope into new navigation instance
    self._navigation = None   # Force lazy reinit
    # The navigation property getter syncs current_scope on first access:
    # self._navigation.current_scope = self.current_scope
```

Looking at the navigation property (lines 122–128):
```python
@property
def navigation(self) -> ConfigNavigation:
    if self._navigation is None:
        self._navigation = ConfigNavigation(self.console, self.project_dir)
        # Sync scope from main command
        self._navigation.current_scope = self.current_scope
    return self._navigation
```

The lazy property already syncs `current_scope` on first access. So resetting `self._navigation = None` is safe — the next `.navigation` access will reinit and sync.

#### Task 3.4: Add import

**File:** `src/claude_mpm/cli/commands/configure.py`

**At top, after other core imports:**
```python
from ...core.deployment_context import DeploymentContext
```

#### Task 3.5: Update golden tests

**File:** `tests/cli/commands/test_configure_golden.py`

If any golden test captures the exact `config_dir` string (`.claude-mpm/`), verify they still pass since the path produced is identical.

Run golden tests: `pytest tests/cli/commands/test_configure_golden.py -v`

Expected: all pass without modification (since `config_dir` resolves to the same value).

### Phase 3 Milestone

**Done looks like:**
- `ConfigureCommand.run()` creates `self._ctx = DeploymentContext.from_string(scope_str, project_dir)`
- `self._ctx` initialized in `__init__()` with safe default
- `_switch_scope()` recreates `self._ctx` and resets scope-dependent lazy managers
- All existing tests pass (no regressions)
- `test_run_scope_project` and `test_run_scope_user` golden tests pass
- `self._ctx.agents_dir` and `self._ctx.skills_dir` are computed correctly but **not yet used** in deployment methods

### Phase 3 Risk Assessment

**Low risk.** The behavioral change to `config_dir` is identical to the previous if/else — same paths. The only risk is `_switch_scope()` teardown: resetting lazy-initialized objects could leave the command in a bad state. Mitigation: run the full test suite after this phase, and add an integration test that switches scope and then deploys an agent to verify no state corruption.

---

## Phase 4: Fix Agent Scope Bug — Wire `self._ctx.agents_dir`

### Objective

Fix the actual bug: agent files now deploy to the scope-appropriate directory. This is the first phase with a user-visible behavioral change.

### Dependencies
- Phase 3 complete (`self._ctx` available on `ConfigureCommand`)

### Tasks

#### Task 4.1: Fix `_deploy_single_agent()` — remote agents

**File:** `src/claude_mpm/cli/commands/configure.py`, line 3073

**Current code:**
```python
# Deploy to project-level agents directory
target_dir = self.project_dir / ".claude" / "agents"
target_dir.mkdir(parents=True, exist_ok=True)
target_file = target_dir / target_name
```

**New code:**
```python
# Deploy to scope-appropriate agents directory
target_dir = self._ctx.agents_dir
target_dir.mkdir(parents=True, exist_ok=True)
target_file = target_dir / target_name
```

**Lines changed:** 1 line modified (comment + path assignment).

**What this does:**
- `scope=project`: `target_dir = project_dir / ".claude" / "agents"` (identical to before)
- `scope=user`: `target_dir = Path.home() / ".claude" / "agents"` (the fix)

#### Task 4.2: Fix `_remove_agents()` — use scope-appropriate directories

**File:** `src/claude_mpm/cli/commands/configure.py`, lines 3141–3158

**Current code:**
```python
# Remove from both project and user directories
removed = False
project_agent_dir = Path.cwd() / ".claude-mpm" / "agents"  # BUG: wrong namespace
user_agent_dir = Path.home() / ".claude" / "agents"
```

Note: `Path.cwd() / ".claude-mpm" / "agents"` is the MPM config namespace, NOT the Claude Code deployment namespace. The correct project path is `self.project_dir / ".claude" / "agents"`.

**New code:**
```python
# Remove from scope-appropriate directory primarily, check other for legacy cleanup
removed = False
primary_agent_dir = self._ctx.agents_dir  # scope-resolved deployment dir
# Legacy fallback: also check the other scope during removal for backward compat
fallback_agent_dir = (
    Path.home() / ".claude" / "agents"
    if self._ctx.scope == "project"
    else self.project_dir / ".claude" / "agents"
)
```

Then update the loop to check `primary_agent_dir` first, then `fallback_agent_dir`:
```python
for file_name in file_names:
    primary_file = primary_agent_dir / file_name
    fallback_file = fallback_agent_dir / file_name

    if primary_file.exists():
        primary_file.unlink()
        removed = True
        self.console.print(f"[green]✓ Removed {primary_file}[/green]")

    # Legacy cleanup: also remove from other scope if present
    if fallback_file.exists():
        fallback_file.unlink()
        removed = True
        self.console.print(f"[green]✓ Removed {fallback_file}[/green]")
```

**Why keep fallback:** Users may have agents physically present in both scope directories from before this fix. The fallback removal cleans up legacy deployments.

#### Task 4.3: Fix `get_deployed_agent_ids()` call in `_deploy_agents_unified()`

**File:** `src/claude_mpm/cli/commands/configure.py`, line 1906

**Current code:**
```python
deployed_ids = get_deployed_agent_ids()  # defaults to Path.cwd()
```

**New code:**
```python
# Pass scope-appropriate project path so deployed agent detection matches scope
deployed_ids = get_deployed_agent_ids(project_dir=self._ctx.project_path)
```

**Note on user scope:** `get_deployed_agent_ids(project_dir=self._ctx.project_path)` still only checks `project_dir/.claude/agents/.mpm_deployment_state`. For user scope, deployed agents live in `~/.claude/agents/`, not the project dir. We need to pass the actual deployment directory root, not the project path.

**Revised approach:** For user scope, we need `get_deployed_agent_ids` to check `~/.claude/agents/`. Looking at the function signature: `get_deployed_agent_ids(project_dir: Optional[Path] = None)`. It uses `project_dir / ".claude" / "agents"`.

For user scope, we want it to check `Path.home()`. So the correct call is:

```python
# For user scope: agent detection base is Path.home() (not project_dir)
# For project scope: agent detection base is self._ctx.project_path
detection_root = (
    Path.home() if self._ctx.scope == ConfigScope.USER else self._ctx.project_path
)
deployed_ids = get_deployed_agent_ids(project_dir=detection_root)
```

Or, to avoid scattering scope logic, add a method to `DeploymentContext`:

**Optional: Add `agents_detection_root` property to DeploymentContext:**
```python
@property
def agents_detection_root(self) -> Path:
    """Root directory for agent deployment state detection.

    get_deployed_agent_ids() appends '.claude/agents/' to this path.
    For project scope: project_path (→ project_path/.claude/agents/)
    For user scope: Path.home() (→ ~/.claude/agents/)
    """
    if self.scope == ConfigScope.USER:
        return Path.home()
    return self.project_path
```

Then in `_deploy_agents_unified()`:
```python
deployed_ids = get_deployed_agent_ids(project_dir=self._ctx.agents_detection_root)
```

**Decision:** Use the simpler `detection_root` local variable approach (avoid adding more methods to `DeploymentContext`).

#### Task 4.4: Add acceptance tests for agent scope fix

**File:** `tests/cli/commands/test_configure_unit.py`

Remove `@pytest.mark.xfail` from the user-scope agent deploy tests added in Phase 1 (Task 1.1). They should now PASS.

Also add integration tests:

```python
def test_deploy_single_agent_project_scope_writes_correct_dir(self, tmp_path, monkeypatch):
    """Agents deploy to project_dir/.claude/agents/ with project scope."""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# Agent")

    cmd = ConfigureCommand()
    cmd.current_scope = "project"
    cmd.project_dir = tmp_path
    cmd._ctx = DeploymentContext.from_project(tmp_path)

    agent = _make_agent_with_source(source)
    cmd._deploy_single_agent(agent, show_feedback=False)

    expected = tmp_path / ".claude" / "agents" / "agent.md"
    assert expected.exists()

def test_deploy_single_agent_user_scope_writes_to_home(self, tmp_path, monkeypatch):
    """Agents deploy to ~/.claude/agents/ with user scope."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    source = tmp_path / "source.md"
    source.write_text("# Agent")

    cmd = ConfigureCommand()
    cmd.current_scope = "user"
    cmd.project_dir = tmp_path
    cmd._ctx = DeploymentContext.from_user(tmp_path)

    agent = _make_agent_with_source(source)
    cmd._deploy_single_agent(agent, show_feedback=False)

    expected = fake_home / ".claude" / "agents" / "agent.md"
    assert expected.exists()
```

### Phase 4 Milestone

**Done looks like:**
- `claude-mpm configure --scope user` deploys agent `.md` files to `~/.claude/agents/`
- `claude-mpm configure` (default) still deploys to `{cwd}/.claude/agents/`
- Removal operations are scope-aware (primary) with legacy fallback
- Agent detection in checkbox UI correctly shows agents in the scope-appropriate directory
- User-scope xfail tests from Phase 1 now PASS
- Full test suite passes

### Phase 4 Risk Assessment

**Medium risk.** This changes user-visible behavior. Specific risks:

1. **`_remove_agents()` namespace bug:** The original code used `.claude-mpm/agents` (MPM config namespace) for the project path — this was already incorrect. Our fix uses `self._ctx.agents_dir` (`.claude/agents/`) which is the right namespace. Could affect users who have agents in the old `.claude-mpm/agents/` path (unlikely but possible). Mitigation: keep the fallback removal for backward compat; add a note in release notes.

2. **`get_deployed_agent_ids()` change:** Passing user home as detection root means the virtual deployment state file at `~/.claude/agents/.mpm_deployment_state` will be checked. This file may not exist for user-scope deployments until after the first deploy. Mitigation: the function already handles missing files gracefully (returns empty set).

3. **Scope toggle mid-session:** If user switches scope mid-session, `self._ctx` is recreated (Phase 3). The agent list in the checkbox UI will now show agents from the new scope's directory. This is correct but potentially surprising. No mitigation needed — this is the intended behavior.

---

## Phase 5: Fix Skills Scope Bug — Wire `self._ctx.skills_dir`

### Objective

Fix all six skill operation methods in `configure.py` to use scope-appropriate paths.

### Dependencies
- Phase 4 complete (agent scope fix applied and tested)

### Tasks

#### Task 5.1: Fix `_get_deployed_skill_ids()`

**File:** `src/claude_mpm/cli/commands/configure.py`, lines 1271–1293

**Current code:**
```python
def _get_deployed_skill_ids(self) -> set:
    from pathlib import Path
    skills_dir = Path.cwd() / ".claude" / "skills"
```

**New code:**
```python
def _get_deployed_skill_ids(self) -> set:
    skills_dir = self._ctx.skills_dir
```

Remove the `from pathlib import Path` local import (already imported at top of file).

**Lines changed:** Remove 2 lines, modify 1 line.

#### Task 5.2: Fix `_install_skill()`

**File:** `src/claude_mpm/cli/commands/configure.py`, lines 1295–1314

**Current code (line 1301):**
```python
target_dir = Path.cwd() / ".claude" / "skills" / skill.skill_id
```

**New code:**
```python
target_dir = self._ctx.skills_dir / skill.skill_id
```

Remove the local `from pathlib import Path` import.

#### Task 5.3: Fix `_uninstall_skill()`

**File:** `src/claude_mpm/cli/commands/configure.py`, lines 1316–1323

**Current code (line 1321):**
```python
target_dir = Path.cwd() / ".claude" / "skills" / skill.skill_id
```

**New code:**
```python
target_dir = self._ctx.skills_dir / skill.skill_id
```

#### Task 5.4: Fix `_install_skill_from_dict()`

**File:** `src/claude_mpm/cli/commands/configure.py`, lines 1325–1349

**Current code (line 1344):**
```python
target_dir = Path.cwd() / ".claude" / "skills" / deploy_name
```

**New code:**
```python
target_dir = self._ctx.skills_dir / deploy_name
```

Remove the local `from pathlib import Path` import.

#### Task 5.5: Fix `_uninstall_skill_by_name()`

**File:** `src/claude_mpm/cli/commands/configure.py`, lines 1351–1362

**Current code (line 1360):**
```python
target_dir = Path.cwd() / ".claude" / "skills" / skill_name
```

**New code:**
```python
target_dir = self._ctx.skills_dir / skill_name
```

Remove the local imports.

#### Task 5.6: Add acceptance tests for skills scope fix

**File:** `tests/cli/commands/test_configure_unit.py`

Remove `@pytest.mark.xfail` from skills user-scope tests from Phase 1 (Task 1.2). They should now PASS.

Add:
```python
def test_install_skill_from_dict_project_scope(self, tmp_path, monkeypatch):
    """Skills from dict install to project_dir/.claude/skills/"""
    monkeypatch.chdir(tmp_path)
    skill_dict = {"name": "my-skill", "content": "# My Skill", "deployment_name": "my-skill"}
    cmd = ConfigureCommand()
    cmd._ctx = DeploymentContext.from_project(tmp_path)
    cmd._install_skill_from_dict(skill_dict)
    assert (tmp_path / ".claude" / "skills" / "my-skill" / "skill.md").exists()

def test_install_skill_from_dict_user_scope(self, tmp_path, monkeypatch):
    """Skills from dict install to ~/.claude/skills/ with user scope."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    skill_dict = {"name": "my-skill", "content": "# My Skill", "deployment_name": "my-skill"}
    cmd = ConfigureCommand()
    cmd._ctx = DeploymentContext.from_user(tmp_path)
    cmd._install_skill_from_dict(skill_dict)
    assert (fake_home / ".claude" / "skills" / "my-skill" / "skill.md").exists()

def test_uninstall_skill_by_name_project_scope(self, tmp_path, monkeypatch):
    """Skill uninstall removes from project scope directory."""
    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    cmd = ConfigureCommand()
    cmd._ctx = DeploymentContext.from_project(tmp_path)
    cmd._uninstall_skill_by_name("my-skill")
    assert not skill_dir.exists()

def test_get_deployed_skill_ids_reflects_scope(self, tmp_path, monkeypatch):
    """_get_deployed_skill_ids() reads from scope-appropriate directory."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Create skill in user scope dir
    user_skill = fake_home / ".claude" / "skills" / "user-skill"
    user_skill.mkdir(parents=True)

    cmd = ConfigureCommand()
    cmd._ctx = DeploymentContext.from_user(tmp_path)
    ids = cmd._get_deployed_skill_ids()
    assert "user-skill" in ids
```

### Phase 5 Milestone

**Done looks like:**
- `claude-mpm configure --scope user` deploys skills to `~/.claude/skills/`
- `claude-mpm configure` (default) still deploys to `{cwd}/.claude/skills/`
- Skill detection shows correctly installed skills per scope
- Uninstallation removes from the correct scope directory
- All user-scope xfail tests from Phase 1 (skills) now PASS
- Full test suite passes

### Phase 5 Risk Assessment

**Low-medium risk.** Same category as Phase 4 but lower because skill operations are simpler (no virtual deployment state, no fallback mechanism). Main risk: users who have skills in `{cwd}/.claude/skills/` and switch to user scope will see those skills as "not installed" in the new scope view. This is correct behavior but may be surprising. No code mitigation needed — document in release notes.

---

## Phase 6: Retire `configure_paths.py`

### Objective

Delete `src/claude_mpm/cli/commands/configure_paths.py` (CLI-specific path resolver) in favor of `core/config_scope.py` (canonical resolver). This reduces three path resolvers to one.

### Background

`configure_paths.py` exports:
- `get_agent_template_path()` — resolves to `.claude-mpm/agents/{agent_name}.json` (MPM config namespace)
- `get_config_directory()` — resolves to `.claude-mpm/`
- `get_agents_directory()` — resolves to `.claude-mpm/agents/` (MPM namespace, NOT `.claude/agents/`)
- `get_behaviors_directory()` — resolves to `.claude-mpm/behaviors/`

Only `get_agent_template_path()` is imported externally (by `configure_template_editor.py`). The other functions appear unused externally — verify with grep.

**Important distinction:** `configure_paths.py`'s `get_agents_directory()` resolves to `.claude-mpm/agents/` (MPM config namespace), while `config_scope.py`'s `resolve_agents_dir()` resolves to `.claude/agents/` (Claude Code deployment namespace). These are different namespaces. The migration must map each function to the correct `config_scope.py` equivalent.

### Dependencies
- Phase 3 complete (configure.py uses DeploymentContext for config_dir)
- Phases 4 and 5 complete (deployment paths use `self._ctx.agents_dir` / `self._ctx.skills_dir`)

### Tasks

#### Task 6.1: Audit all usages of `configure_paths.py`

**Search commands:**
```bash
grep -r "from .configure_paths import" src/
grep -r "from claude_mpm.cli.commands.configure_paths import" src/
grep -r "configure_paths" src/
```

**Expected results:**
- `configure_template_editor.py:28`: `from .configure_paths import get_agent_template_path` — the only external usage

**Verify no other usages exist before proceeding.**

#### Task 6.2: Migrate `configure_template_editor.py` away from `configure_paths`

**File:** `src/claude_mpm/cli/commands/configure_template_editor.py`

**Current import (line 28):**
```python
from .configure_paths import get_agent_template_path
```

**`get_agent_template_path` behavior:** Given `(agent_name, scope, project_dir, templates_dir)`, it:
1. Resolves `.claude-mpm/agents/{agent_name}.json` (scope-appropriate)
2. If that exists, returns it (custom template)
3. Otherwise, checks `templates_dir/{agent_name}.json` (system template)
4. Returns the custom path for new templates

The mapping to `config_scope.py`:
- `.claude-mpm/agents/` = `resolve_config_dir(scope, project_dir) / "agents"` from config_scope.py

**Migration:** Replace the import and add an inline function or use `resolve_config_dir`:

**Option A: Inline the function in `configure_template_editor.py`**

Remove the import, add to `configure_template_editor.py`:
```python
from ...core.config_scope import resolve_config_dir, ConfigScope

def _get_agent_template_path(
    agent_name: str,
    scope: str,
    project_dir: Path,
    templates_dir: Path,
) -> Path:
    """Get the path to an agent's template file (MPM config namespace).

    Checks scope-appropriate .claude-mpm/agents/ for custom templates,
    falls back to system templates_dir.
    """
    config_agents_dir = resolve_config_dir(ConfigScope(scope), project_dir) / "agents"
    config_agents_dir.mkdir(parents=True, exist_ok=True)
    custom_template = config_agents_dir / f"{agent_name}.json"

    if custom_template.exists():
        return custom_template

    # Check system templates with various naming conventions
    for name in [
        f"{agent_name}.json",
        f"{agent_name.replace('-', '_')}.json",
        f"{agent_name}-agent.json",
        f"{agent_name.replace('-', '_')}_agent.json",
    ]:
        system_template = templates_dir / name
        if system_template.exists():
            return system_template

    return custom_template
```

This is identical logic using `resolve_config_dir` from `config_scope.py` instead of `get_config_directory` from `configure_paths.py`.

**Option B: Promote `get_agent_template_path` into `config_scope.py`**

This is cleaner if the function belongs at the core level. Add to `config_scope.py`:
```python
def resolve_agent_template_path(
    agent_name: str,
    scope: ConfigScope,
    project_path: Path,
    templates_dir: Path,
) -> Path:
    """Resolve an agent's template file path in the MPM config namespace."""
    ...
```

**Recommendation:** Option A — keep the function scoped to CLI template editing. It doesn't belong in the shared `config_scope.py` module which focuses on Claude Code deployment paths.

#### Task 6.3: Delete `configure_paths.py`

After verifying no remaining imports:
```bash
rm src/claude_mpm/cli/commands/configure_paths.py
```

#### Task 6.4: Add tests for migrated template path resolution

**File:** `tests/cli/commands/test_configure_unit.py` or `tests/cli/commands/test_template_editor.py`

```python
def test_get_agent_template_path_project_scope(self, tmp_path):
    """Template path resolves to project .claude-mpm/agents/ for project scope."""
    templates_dir = tmp_path / "system_templates"
    templates_dir.mkdir()

    path = _get_agent_template_path("python-engineer", "project", tmp_path, templates_dir)
    assert ".claude-mpm" in str(path)
    assert "python-engineer.json" in str(path)

def test_get_agent_template_path_user_scope(self, tmp_path, monkeypatch):
    """Template path resolves to ~/.claude-mpm/agents/ for user scope."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    templates_dir = tmp_path / "system_templates"
    templates_dir.mkdir()

    path = _get_agent_template_path("python-engineer", "user", tmp_path, templates_dir)
    assert str(fake_home) in str(path)
    assert ".claude-mpm" in str(path)
```

### Phase 6 Milestone

**Done looks like:**
- `configure_paths.py` is deleted
- `configure_template_editor.py` imports from `core.config_scope` instead
- `grep -r "configure_paths" src/` returns no results
- All template editing tests pass
- Full test suite passes

### Phase 6 Risk Assessment

**Low risk.** The logic being migrated is identical — only the import source changes. Main risk: missed usages of `configure_paths`. Mitigation: comprehensive grep before deletion + full test suite run after.

---

## Phase 7: Add `--scope` to `SkillsManagementCommand`

### Objective

Wire `DeploymentContext` through the `skills` CLI command (`skills.py`) so that `claude-mpm skills deploy --scope user` installs to `~/.claude/skills/`.

### Background

`SkillsManagementCommand` (in `cli/commands/skills.py`) currently uses `SkillsDeployerService` which has its own scope handling via `ConfigScope`. The `run()` method does not read a `--scope` arg. The `skills` subcommand parser (`cli/parsers/skills_parser.py`) must be checked for an existing `--scope` arg.

### Dependencies
- Phase 5 complete (skill scope fix in configure.py done)
- Phase 2 complete (DeploymentContext exists)

### Tasks

#### Task 7.1: Audit `SkillsDeployerService` scope support

**File:** `src/claude_mpm/services/skills_deployer.py`

Look for: `deploy_skills(self, ..., skills_dir: Optional[Path] = None)` signature. If `skills_dir` is already accepted, the service is already scope-agnostic — we only need to pass the right `skills_dir` from the CLI layer.

**Expected finding:** Based on implementation-strategies.md research: `SkillsDeployerService.deploy_skills(skills_dir=...)` already accepts target directory.

#### Task 7.2: Check skills parser for existing `--scope` arg

**File:** `src/claude_mpm/cli/parsers/skills_parser.py` (or similar)

**Grep:**
```bash
grep -n "scope" src/claude_mpm/cli/parsers/skills_parser.py
```

If `--scope` already exists in the parser, skip Task 7.3. If not, add it.

#### Task 7.3: Add `--scope` arg to skills parser

**File:** `src/claude_mpm/cli/parsers/skills_parser.py` (or `add_skills_subparser()`)

**Change:** Add to the skills subparser:
```python
scope_group = skills_parser.add_argument_group("deployment scope")
scope_group.add_argument(
    "--scope",
    choices=["project", "user"],
    default="project",
    help="Deployment scope for skills (default: project → ./.claude/skills/, user → ~/.claude/skills/)",
)
```

#### Task 7.4: Read scope in `SkillsManagementCommand.run()`

**File:** `src/claude_mpm/cli/commands/skills.py`

**In `run()` method:**
```python
def run(self, args) -> CommandResult:
    # Read scope (defaults to project for backward compat)
    scope_str = getattr(args, "scope", "project")
    self._ctx = DeploymentContext.from_string(scope_str)
    ...
```

**Add import:**
```python
from ...core.deployment_context import DeploymentContext
```

#### Task 7.5: Pass scope-appropriate `skills_dir` to `SkillsDeployerService`

In the deploy subcommand handler (`_deploy_skills()` or similar):

**Before:**
```python
result = self.skills_deployer.deploy_skills(...)
```

**After:**
```python
result = self.skills_deployer.deploy_skills(..., skills_dir=self._ctx.skills_dir)
```

Repeat for `check_deployed_skills()`, `remove_skills()`, and any other method that accepts `skills_dir`.

#### Task 7.6: Add tests for skills command scope

**File:** `tests/cli/commands/test_skills_cli.py`

Remove the gap-documentation test from Phase 1 Task 1.4 and replace with real tests:

```python
class TestSkillsScope:
    def test_deploy_skills_default_scope_is_project(self, tmp_path, monkeypatch):
        """claude-mpm skills deploy uses project scope by default."""
        monkeypatch.chdir(tmp_path)
        args = argparse.Namespace(
            skills_command="deploy",
            scope="project",
            # ... other required args
        )
        cmd = SkillsManagementCommand()
        assert cmd._ctx is None or True  # Before run()
        # Verify deployer is called with project skills_dir
        # (mock SkillsDeployerService, assert skills_dir == tmp_path/.claude/skills/)

    def test_deploy_skills_user_scope_uses_home(self, tmp_path, monkeypatch):
        """claude-mpm skills deploy --scope user deploys to ~/.claude/skills/."""
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        args = argparse.Namespace(scope="user", skills_command="deploy")
        cmd = SkillsManagementCommand()
        # Verify deployer is called with user skills_dir
```

### Phase 7 Milestone

**Done looks like:**
- `claude-mpm skills deploy --scope user` deploys to `~/.claude/skills/`
- `claude-mpm skills remove --scope user` removes from `~/.claude/skills/`
- Default (no `--scope`) behavior unchanged (project scope)
- Gap tests from Phase 1 Task 1.4 removed and replaced with passing tests
- Full test suite passes

### Phase 7 Risk Assessment

**Low-medium risk.** The skills service already accepts `skills_dir` as a parameter — wiring is straightforward. Risk: if some skills subcommands (e.g., `list`, `info`) don't accept `skills_dir` and always read from project scope. Mitigation: audit each skills subcommand during Task 7.5.

---

## Summary: All Phases at a Glance

| Phase | Description | Files Modified | Behavioral Change | Risk |
|-------|-------------|----------------|-------------------|------|
| 1 | Pre-refactor characterization tests | 2 test files (new/modified) | None | Very low |
| 2 | Create `DeploymentContext` | 1 new file + `core/__init__.py` | None | Minimal |
| 3 | Wire `self._ctx` in `ConfigureCommand.run()` (config_dir only) | `configure.py` | None (same paths) | Low |
| 4 | Fix agent scope bug | `configure.py` | **Yes** — user scope deploys to `~/.claude/agents/` | Medium |
| 5 | Fix skills scope bug | `configure.py` | **Yes** — user scope deploys to `~/.claude/skills/` | Low-Medium |
| 6 | Retire `configure_paths.py` | `configure_template_editor.py`, delete `configure_paths.py` | None | Low |
| 7 | Add `--scope` to `SkillsManagementCommand` | `skills.py`, `skills_parser.py` | **Yes** — new capability | Low-Medium |

### Key constraints honored

- **Archive feature**: Not touched in any phase.
- **Default behavior**: Project scope behavior identical throughout. Users who don't use `--scope user` see zero change.
- **`DeploymentContext`**: Implemented as specified (~50-line frozen dataclass) per implementation-strategies.md Strategy 1.
- **Backward compatibility**: `ConfigScope(str, Enum)` means `scope == "project"` string comparisons in existing code still work.

---

## Implementation Order Dependencies

```
Phase 1 (tests)
    │
    ▼
Phase 2 (DeploymentContext)
    │
    ▼
Phase 3 (wire in run() — config_dir only)
    │
    ▼
Phase 4 (fix agent bug) ──┐
    │                      │
    ▼                      │
Phase 5 (fix skills bug) ──┤
    │                      │
    ▼                      ▼
Phase 6 (retire configure_paths.py)
    │
Phase 7 (--scope in skills cmd) ← can start after Phase 2
```

Note: Phase 7 can begin in parallel with Phase 3–5 since it operates on `skills.py`, not `configure.py`.

---

## Test Files Summary

| Test File | New/Modified | Tests Added | Phase |
|-----------|-------------|-------------|-------|
| `tests/core/test_scope_selector.py` | New | ~10 DeploymentContext tests | 1, 2 |
| `tests/cli/commands/test_configure_unit.py` | Modified | ~10 scope characterization + fix tests | 1, 4, 5 |
| `tests/cli/commands/test_skills_cli.py` | Modified | ~4 scope tests | 1, 7 |
| `tests/cli/commands/test_configure_golden.py` | Modified (check only) | Verify no regression | 3 |
| `tests/cli/commands/test_template_editor.py` | New or modified | ~4 template path tests | 6 |

---

## Files Modified Summary

| File | Phase(s) | Nature of Change |
|------|----------|-----------------|
| `src/claude_mpm/core/deployment_context.py` | 2 | **New file** (~65 lines) |
| `src/claude_mpm/core/__init__.py` | 2 | Add export |
| `src/claude_mpm/cli/commands/configure.py` | 3, 4, 5 | Add import + wire `self._ctx` + fix 6 path hardcodings |
| `src/claude_mpm/cli/commands/configure_template_editor.py` | 6 | Replace import from `configure_paths` with `config_scope` |
| `src/claude_mpm/cli/commands/configure_paths.py` | 6 | **Deleted** |
| `src/claude_mpm/cli/commands/skills.py` | 7 | Add scope reading + DeploymentContext |
| `src/claude_mpm/cli/parsers/skills_parser.py` | 7 | Add `--scope` arg |

**Total production code changes:** ~1 new file (65 lines), 1 deleted file (105 lines), ~40 lines of modifications across 3 existing files, 1 parser addition (~8 lines).

---

## Acceptance Criteria (End State)

1. `claude-mpm configure --scope user --agents` → agents deploy to `~/.claude/agents/`
2. `claude-mpm configure` (no scope) → agents deploy to `{cwd}/.claude/agents/` (unchanged)
3. Interactive scope toggle ("Switch Scope" option in TUI) → subsequent operations use new scope
4. `claude-mpm configure --scope user` → skills deploy to `~/.claude/skills/`
5. `claude-mpm skills deploy --scope user` → skills deploy to `~/.claude/skills/`
6. `grep -r "configure_paths" src/` returns no results
7. `DeploymentContext.from_string("invalid")` raises `ValueError`
8. Full test suite passes with no regressions
9. New tests (Phases 1–7) all pass (no xfail remaining after Phase 5)
