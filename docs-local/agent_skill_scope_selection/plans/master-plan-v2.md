# Master Implementation Plan v2: Scope-Aware Agent & Skill Deployment

**Author:** master-integrator (Research Agent)
**Date:** 2026-02-28
**Branch:** agent_skill_scope_selection
**Supersedes:** `docs-local/agent_skill_scope_selection/plans/master-plan.md` (v1, preserved for history)
**Decisions incorporated:** See `docs-local/agent_skill_scope_selection/plans/decisions-log.md`
**Synthesized from:**
- `docs-local/agent_skill_scope_selection/plans/cli-path-plan.md` (7 phases)
- `docs-local/agent_skill_scope_selection/plans/api-path-plan.md` (6 phases, labeled 0–5)
- `docs-local/agent_skill_scope_selection/plans/test-plan.md` (~100 tests, 5 phases)
- `docs-local/agent_skill_scope_selection/research/implementation-strategies.md`
- `docs-local/agent_skill_scope_selection/research/abstraction-opportunities.md`
- `docs-local/agent_skill_scope_selection/research/devils-advocate.md`

---

## Change Summary from v1

Three binding decisions from the project owner revise v1:

| Decision | Change from v1 |
|----------|---------------|
| MUST-1: API scope scoped down to project-only | Phases 5–8 trimmed: scope parameter added but user-scope wiring deferred. No user-scope directory resolution, no user-scope manager, no user-scope Socket.IO routing in this iteration. |
| MUST-2: TC-0-04/TC-0-05 contradiction resolved | Phase 4A now explicitly deletes TC-0-04 and TC-0-05 rather than removing xfail markers. |
| MUST-3: BackupManager extends to accept scope | A BackupManager scope task is added to Phase 4B. The TODO-comment approach from v1 is rejected. |

See `decisions-log.md` for full rationale and impact analysis.

---

## 1. Executive Summary

### Problem Statement

When a user runs `claude-mpm configure --scope user`, agent files still deploy to
`{cwd}/.claude/agents/` and skills still deploy to `{cwd}/.claude/skills/`. The `--scope user`
flag silently affects only metadata (`agent_states.json` location) — not file deployment. On the
API side, all 14+ call sites hardcode `ConfigScope.PROJECT`; a singleton `_agent_manager` in
`config_routes.py` is initialized once with the project path and never re-keyed by scope, creating
a silent data-corruption trap if scope-aware reads are added before fixing it.

### Solution Approach

**Strategy 1: DeploymentContext** — a ~65-line frozen dataclass at `core/deployment_context.py`
that captures (scope, project_path) and exposes `agents_dir`, `skills_dir`, and `config_dir`
properties by delegating to the existing `core/config_scope.py` resolvers. Both CLI and API create
one context at the entry point and carry it through. No path logic lives in the dataclass — it
wraps what already works.

**API scope constraint (MUST-1):** This iteration adds a `scope` parameter to all API endpoints
for explicit project-scope signaling and extensible design. The parameter accepts `"project"` and
validates it; anything else returns HTTP 400. User-scope wiring (user-scope directory paths, a
user-scope manager instance, user-scope Socket.IO event routing) is deferred to a future task once
the dashboard has a scope selector UI.

The plan is organized in **8 unified phases** (v1 had 9; Phase 8 Socket.IO / dashboard notes is
cut from this iteration). Phases 1–3 carry zero behavioral change. Phase 4 fixes the actual bugs
(CLI deploy paths + API singleton) and extends BackupManager. Phases 5–6 add the extensible scope
parameter to API endpoints (project-only validation). Phase 7 closes with code cleanup and E2E
integration tests.

### Total Estimated Scope (vs. v1)

| Category | v1 | v2 |
|----------|----|----|
| New production files | 1 | 1 (`core/deployment_context.py`, ~65 lines) |
| Production files modified | 8 | 8 (same files; API handler scope wiring trimmed) |
| Files deleted | 2 | 2 (`configure_paths.py`, `path_resolver.py`) |
| New test files | 10 | 9 (test_autoconfig_scope.py deferred; user-scope API E2E deferred) |
| Total new tests | ~100 | ~75 (E2E API user-scope tests deferred, TC-0-04/05 deleted) |
| Total net lines (prod) | ~+150 / ~-160 / ~+200 | ~+150 / ~-160 / ~+160 modified |

### Success Criteria

1. `claude-mpm configure --scope user` deploys agent `.md` files to `~/.claude/agents/`
2. `claude-mpm configure --scope user` deploys skill directories to `~/.claude/skills/`
3. `POST /api/config/agents/deploy {"scope": "project", "agent_name": "X"}` places `X.md` in
   `{cwd}/.claude/agents/X.md` (scope explicit, not hardcoded)
4. `POST /api/config/agents/deploy {"scope": "invalid"}` returns HTTP 400 `VALIDATION_ERROR`
5. `POST /api/config/agents/deploy {"agent_name": "X"}` (no scope) works identically to current
   (backward compatible; server defaults to project scope)
6. No singleton trap: `_get_agent_manager("project")` returns a project-scoped `AgentManager`;
   the dict structure is in place for future `_get_agent_manager("user")`
7. `BackupManager` is wired to receive the scope-resolved directory path, not a hardcoded one
8. `configure_paths.py` and `core/shared/path_resolver.py` are deleted (resolver count: 3 → 1)
9. Test coverage increases at every phase (never decreases)
10. Every phase is independently mergeable (CI green after each)

**Not a success criterion in this iteration:**
- `POST /api/config/agents/deploy {"scope": "user", "agent_name": "X"}` — user-scope API
  wiring is deferred; this request will return HTTP 400 by design.

---

## 2. Unified Phase Sequence

```
Phase 1: Test Foundation           ← characterization tests + fixtures (no prod code)
    │
    └── Phase 2: DeploymentContext ← additive only (~65 lines, pure value object)
                │
                ├── Phase 3: CLI Config Wire   ← pure refactor, zero behavior change
                │       │
                │       └── Phase 4A: CLI Bug Fix ─────────────┐ (parallel)
                │                                               │
                └── Phase 4B: API Singleton Fix ───────────────┘ (parallel with 4A)
                             + BackupManager scope extension
                                │
                                ├── Phase 5: API Scope Parameter (project-only validation)
                                │
                                └── Phase 6: API Read-Only Scope (project-only validation)
                                                │
                                                └── Phase 7: Code Cleanup + E2E Tests
```

**Phases 4A and 4B are the only parallel phases.** All other phases must proceed in the order
shown.

**What is explicitly not in this diagram (deferred):**
- Full user-scope wiring in API handlers
- Socket.IO scope metadata on events
- Dashboard integration notes document
- User-scope cross-path E2E tests (CLI deploy → API reads user-scope dir)

---

## 3. Detailed Phase Descriptions

---

### Phase 1: Test Foundation

**Objective:** Capture current behavior in tests before any production code changes. These tests
are the safety net — any Phase 1 test that breaks after a refactor means behavior changed.
Also establish shared fixtures and document the user-scope contract in docstrings.

**Must complete before:** Any production code change.

**CLI tasks** (from cli-path-plan.md Phase 1):

| Task | File | Description |
|------|------|-------------|
| 1.1 | `tests/cli/commands/test_configure_unit.py` | Add 6 scope characterization tests; user-scope deploy tests marked `@pytest.mark.xfail(strict=True)` |
| 1.2 | `tests/cli/commands/test_configure_unit.py` | Add `_get_deployed_skill_ids()` scope tests (project PASS, user XFAIL) |
| 1.3 | `tests/core/test_scope_selector.py` (new) | TDD placeholder tests for `DeploymentContext` interface (all xfail until Phase 2) |
| 1.4 | `tests/cli/commands/test_skills_cli.py` | Add `TestSkillsScope` documenting the gap in skills command scope handling |

**API tasks** (from api-path-plan.md Phase 0):

| Task | File | Description |
|------|------|-------------|
| 0.1 | `src/claude_mpm/core/config_scope.py` docstring | Document semantics: PROJECT=`{cwd}/.claude/`, USER=`~/.claude/`; note that USER scope is not yet supported by the API |
| 0.2 | `tests/unit/services/config_api/test_scope_current_behavior.py` (new) | API characterization: hardcoded PROJECT scope, `_get_config_path()`, singleton behavior |
| 0.3 | `tests/integration/api/conftest.py` (new) | Shared aiohttp test client fixtures, `tmp_path` project dirs, fake home dirs |

**Test tasks** (from test-plan.md Phase 0):

- **TC-0-01 through TC-0-06** (file: `tests/cli/commands/test_configure_scope_characterization.py`)
  — CLI scope characterization: project config dir, user config dir, missing scope default,
  deploy target (project), deploy target (user, XFAIL), scope toggle.
  Note: TC-0-04 and TC-0-05 are written as `xfail(strict=True)` here and will be **deleted**
  in Phase 4A (not updated — see MUST-2).
- **TC-0-07, TC-0-08** (same file) — skills scope current behavior: `_get_deployed_skill_ids()`
  reads from cwd, `_uninstall_skill_by_name()` removes from cwd
- **TC-0-09 through TC-0-12** (file: `tests/services/config_api/test_scope_characterization.py`)
  — API current assumptions: handlers hardcode PROJECT, singleton initializes once

Add shared fixtures to `tests/conftest.py`:
- `project_scope_dirs` — standard `.claude/agents/`, `.claude/skills/`, `.claude-mpm/` under tmp_path
- `user_scope_dirs` — same but under a patched `Path.home()` (fake home)
- `both_scopes` — composite fixture for cross-scope isolation tests

**Milestone:** All 16 characterization tests + new fixtures committed. `pytest --tb=short` shows:
- 12 CLI tests: some PASS (project scope), some XFAIL (user scope deploy — TC-0-04, TC-0-05)
- 4 API tests: all PASS on unmodified code
- All existing tests still pass (zero regressions)

**Dependencies:** None. This phase stands alone.

**Responsibility:** test-engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| XFAIL markers missing from user-scope tests | Low | CI enforces `strict=True` — will error if xfail passes unexpectedly |
| conftest.py fixture name collision | Low | Use project-namespaced names (`project_scope_dirs`, not `dirs`) |
| API characterization test tightly couples to internals | Medium | Use `monkeypatch` for `_get_agent_manager`; avoid patching private vars directly |

---

### Phase 2: DeploymentContext Core

**Objective:** Create `src/claude_mpm/core/deployment_context.py` — a pure, immutable value
object that wraps `config_scope.py`. Zero existing files modified (except `core/__init__.py` for
export). The devil's advocate raised "fourth resolver" concern; the counter: this is a convenience
wrapper, not a resolver. All path logic remains in `config_scope.py`. The dataclass is designed
to be scope-extensible (it can represent USER scope and resolve correct paths for it) but API
handlers in this iteration will only create project-scope instances.

**Must complete before:** Phases 3, 4A, 4B.

**Tasks:**

| Task | File | Description |
|------|------|-------------|
| 2.1 | `src/claude_mpm/core/deployment_context.py` (new) | Frozen dataclass: `from_project()`, `from_user()`, `from_request_scope()`; properties: `agents_dir`, `skills_dir`, `config_dir`, `configuration_yaml` |
| 2.2 | `src/claude_mpm/core/__init__.py` | Add `from .deployment_context import DeploymentContext` (check for circular imports first) |
| 2.3 | `tests/core/test_scope_selector.py` | Remove xfail markers; add immutability + equality + hashability tests |

**Factory method alignment:** `from_request_scope()` is the primary API factory; `from_string`
is an alias for CLI compatibility:
```python
from_string = from_request_scope
```

**`from_request_scope()` validation (project-only, MUST-1):** In this iteration the validation
allows only `"project"`. The implementation accepts the full enum by design (so adding `"user"`
later is one line), but raises `ValueError` for non-`"project"` strings:
```python
@classmethod
def from_request_scope(cls, scope_str: str, project_path: Path = None) -> "DeploymentContext":
    """Create from an HTTP request scope string.

    Currently only "project" is supported by the API. "user" and other
    values raise ValueError. This design is intentionally scope-extensible:
    adding user scope requires only wiring the handlers, not changing
    this class.
    """
    if scope_str not in ("project",):   # extend to ("project", "user") when user-scope API lands
        raise ValueError(
            f"Invalid scope '{scope_str}'. Currently only 'project' is supported."
        )
    return cls(scope=ConfigScope(scope_str), project_path=project_path or Path.cwd())
```

Note: `from_project()` and `from_user()` remain fully usable (e.g., by CLI); only
`from_request_scope` enforces the project-only API constraint.

**Final `DeploymentContext` properties:**
- `agents_dir` → `resolve_agents_dir(scope, project_path)`
- `skills_dir` → `resolve_skills_dir(scope, project_path)`
- `config_dir` → `resolve_config_dir(scope, project_path)`
- `configuration_yaml` → `config_dir / "configuration.yaml"`

**Test tasks** (from test-plan.md Phase 1, TC-1-01 through TC-1-23):

Full coverage of `TestDeploymentContextFactories`, `TestDeploymentContextPathProperties`,
`TestDeploymentContextImmutability`, `TestDeploymentContextEdgeCases` — 23 tests total.
TC-1-05 (`from_string("user")`) and TC-1-12/TC-1-14/TC-1-16/TC-1-18 (user-scope property
tests) still pass — these test the dataclass directly, which correctly resolves user paths.
The API-level restriction is in `from_request_scope()` only.

**Milestone:**
- `src/claude_mpm/core/deployment_context.py` exists and imports cleanly
- All 23 tests in `test_deployment_context.py` pass
- `from_request_scope("project")` succeeds; `from_request_scope("user")` raises `ValueError`
- `from_user()` still works (CLI uses it directly)
- No existing test regressions

**Dependencies:** Phase 1 complete.

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Circular import in `core/__init__.py` | Medium | Import `DeploymentContext` lazily or check import graph first |
| CLI `from_string()` raises for `None` scope | Low | Guard: `if not scope_str: raise ValueError(...)` |
| `from_request_scope` validation blocks TC-1-05 in test suite | Low | TC-1-05 tests `from_user()` directly, not `from_request_scope("user")` — different method |

---

### Phase 3: CLI Config Path Wire (Zero Behavior Change)

**Objective:** Replace the ad-hoc `if self.current_scope == "project": config_dir = ...` block in
`ConfigureCommand.run()` with `self._ctx = DeploymentContext.from_string(...)`. Only `config_dir`
is threaded through `_ctx` at this phase — deploy paths remain unchanged. Pure refactor.

**Must complete before:** Phase 4A.

**CLI tasks** (from cli-path-plan.md Phase 3):

| Task | File | Lines | Description |
|------|------|-------|-------------|
| 3.1 | `src/claude_mpm/cli/commands/configure.py` | ~185–197 | Replace if/else `config_dir` block with `self._ctx = DeploymentContext.from_string(scope_str, self.project_dir); config_dir = self._ctx.config_dir` |
| 3.2 | `src/claude_mpm/cli/commands/configure.py` | `__init__()` | Add `self._ctx = DeploymentContext.from_project(Path.cwd())` as default |
| 3.3 | `src/claude_mpm/cli/commands/configure.py` | `_switch_scope()` | Recreate `self._ctx` and reinit scope-dependent managers after scope switch |
| 3.4 | `src/claude_mpm/cli/commands/configure.py` | imports | Add `from ...core.deployment_context import DeploymentContext` |
| 3.5 | `tests/cli/commands/test_configure_golden.py` | — | Run golden tests; verify no path string changes (paths are identical) |

Note: CLI uses `from_string()` (which aliases `from_request_scope()`). CLI will call
`from_string("user")` when scope is user — this must succeed. The user-scope restriction in
`from_request_scope` is enforced at the API handler level only, not in the dataclass factory
called by the CLI. Consider keeping `from_string()` as a separate, less-restricted method for
CLI use if needed, or have CLI call `from_user()` / `from_project()` directly based on the
string value.

**API tasks:** None. Phase 3 is CLI-only.

**Test tasks:** No new tests. Validate by running:
```bash
pytest tests/cli/commands/ -v  # all must pass
pytest tests/cli/commands/test_configure_golden.py -v  # specific regression check
```

**Milestone:**
- `ConfigureCommand.run()` uses `self._ctx.config_dir` for manager initialization
- `_switch_scope()` recreates context correctly
- Full test suite passes (all existing tests green, no regressions)
- XFAIL user-scope deploy tests still XFAIL (behavior not yet fixed)

**Dependencies:** Phase 2 complete.

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `from_request_scope("user")` raises in CLI after MUST-1 restriction | Medium | CLI calls `from_project()` / `from_user()` directly, or `from_string()` is a separate unrestricted alias |
| `_switch_scope()` resets `_navigation = None` | Medium | Navigation property getter already syncs `current_scope` on first access |
| Golden tests capture `.claude-mpm/` path as a string and break | Low | `DeploymentContext.config_dir` returns the identical path value |

---

### Phase 4A: CLI Bug Fix (Parallel with 4B)

**Objective:** Fix the actual CLI scope bug. Wire `self._ctx.agents_dir` and `self._ctx.skills_dir`
into the 6 hardcoded deploy-path sites in `configure.py`. The XFAIL tests from Phase 1 (TC-0-04,
TC-0-05) are deleted in this phase — not updated with new assertions.

**Must complete before:** Phase 7 (E2E).
**Can run in parallel with:** Phase 4B (API Singleton Fix + BackupManager).

**CLI tasks** (from cli-path-plan.md Phases 4 and 5):

**Agent deploy fix (Phase 4 in CLI plan):**

| Task | File | Line(s) | Change |
|------|------|---------|--------|
| 4A.1 | `configure.py` | `_deploy_single_agent()` ~3073 | Replace `self.project_dir / ".claude" / "agents"` with `self._ctx.agents_dir` |

**Skill deploy fixes (Phase 5 in CLI plan):**

| Task | File | Line(s) | Change |
|------|------|---------|--------|
| 4A.2 | `configure.py` | `_get_deployed_skill_ids()` ~1279 | Replace `Path.cwd() / ".claude" / "skills"` with `self._ctx.skills_dir` |
| 4A.3 | `configure.py` | `_install_skill()` ~1301 | Replace `Path.cwd() / ".claude" / "skills" / skill.skill_id` with `self._ctx.skills_dir / skill.skill_id` |
| 4A.4 | `configure.py` | `_install_skill_from_dict()` ~1344 | Replace `Path.cwd() / ".claude" / "skills" / deploy_name` with `self._ctx.skills_dir / deploy_name` |
| 4A.5 | `configure.py` | `_uninstall_skill()` ~1321 | Replace `Path.cwd() / ".claude" / "skills" / skill.skill_id` with `self._ctx.skills_dir / skill.skill_id` |
| 4A.6 | `configure.py` | `_uninstall_skill_by_name()` ~1360 | Replace `Path.cwd() / ".claude" / "skills" / skill_name` with `self._ctx.skills_dir / skill_name` |

**Test tasks (MUST-2 applied):**

TC-0-04 and TC-0-05 are **deleted** in this phase. They documented the broken behavior; their
purpose is served. The new-behavior tests (TC-2-01 and TC-2-02) are the regression anchors
going forward.

New test file: `tests/cli/commands/test_configure_scope_behavior.py` (17 tests)
- `TestConfigureAgentScopeDeployment`: TC-2-01 through TC-2-06
- `TestConfigureSkillScopeDeployment`: TC-2-07 through TC-2-13
- `TestConfigureScopeValidation`: TC-2-14 through TC-2-17

**Milestone:**
- All 6 hardcoded path sites in `configure.py` use `self._ctx.agents_dir` or `self._ctx.skills_dir`
- `claude-mpm configure --scope user` places files in `~/.claude/agents/` and `~/.claude/skills/`
- 17 new CLI scope tests pass (TC-2-01 through TC-2-17)
- TC-0-04 and TC-0-05 are absent from the test suite (deleted)
- All other existing tests still pass

**Dependencies:** Phase 3 complete.

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `_deploy_single_agent()` also calls `AgentDeploymentService.deploy_agent()` — behavior change masked | Medium | Read the exact current code before changing; CLI uses `shutil.copy2` directly (confirmed in abstraction research). Path change only. |
| `~/.claude/agents/` does not exist — mkdir fails silently | Low | Add `self._ctx.agents_dir.mkdir(parents=True, exist_ok=True)` before copy |
| Deleting TC-0-04/TC-0-05 leaves a gap if behavior regresses later | Low | TC-2-01 (project scope) + TC-2-02 (user scope) cover both paths with correct new-behavior assertions |

---

### Phase 4B: API Singleton Fix + BackupManager (Parallel with 4A)

**Objective:** Eliminate the `_agent_manager` singleton trap in `config_routes.py` BEFORE any
scope parameter is added to API endpoints. Also extend BackupManager to receive the scope-resolved
directory path rather than hardcoding the project path (MUST-3).

**Must complete before:** Phases 5, 6.
**Can run in parallel with:** Phase 4A.

**API singleton fix tasks** (from api-path-plan.md Phase 2):

| Task | File | Description |
|------|------|-------------|
| 4B.1 | `services/monitor/config_routes.py` | Replace `_agent_manager = None` singleton with `_agent_managers: Dict[str, Any] = {}` per-scope dict; update `_get_agent_manager(scope: str = "project")` |
| 4B.2 | `services/monitor/config_routes.py` | Update all callers of `_get_agent_manager()` to pass `"project"` explicitly (no behavior change at this phase) |
| 4B.3 | `services/config_api/agent_deployment_handler.py` | Make `verifier.verify_agent_deployed(name)` calls explicitly pass `agents_dir=agents_dir` |
| 4B.4 | `services/config_api/skill_deployment_handler.py` | Make `verifier.verify_skill_*()` calls explicitly pass `skills_dir=skills_dir` |

**Pre-coding check for Task 4B.1:**
```bash
grep -n "_agent_manager" src/claude_mpm/services/monitor/config_routes.py
```
Ensure no direct `_agent_manager` access bypasses `_get_agent_manager()`.

**BackupManager scope extension task (MUST-3):**

| Task | File | Description |
|------|------|-------------|
| 4B.5 | `services/config_api/backup_manager.py` | Add `agents_dir` parameter to `BackupManager.__init__()` or to the primary backup call; remove the hardcoded `resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` |
| 4B.6 | `services/config_api/agent_deployment_handler.py` | Pass `agents_dir=ctx.agents_dir` (project-scope-resolved) to BackupManager at the call site in the deploy handler |
| 4B.7 | `services/config_api/skill_deployment_handler.py` | Same for skills handler — pass `skills_dir=ctx.skills_dir` to BackupManager if it is used there |

**Implementation note for BackupManager (MUST-3):** The behavioral change for project-scope
operations is zero — the project-scope-resolved directory is the same value that was previously
hardcoded. The architectural change is that the path is now supplied explicitly from the handler's
`DeploymentContext` rather than internally computed. When user-scope API wiring arrives in a future
iteration, `BackupManager` will automatically back up the correct directory because the handler
will pass `ctx.agents_dir` which will then be `~/.claude/agents/`.

**Test tasks:**

File: `tests/unit/services/monitor/test_agent_manager_scoping.py` (new, 2 tests)
- `test_project_and_user_managers_are_independent`: clears dict, calls both scopes, asserts `is not`
- `test_same_scope_returns_cached_manager`: calls project scope twice, asserts `is`

New test for BackupManager wiring (add to existing or new file in
`tests/unit/services/config_api/`):
- `test_backup_manager_receives_scope_resolved_agents_dir`: mock BackupManager; verify it is
  called with the `agents_dir` derived from `DeploymentContext.from_project()`, not a hardcoded
  `Path.cwd() / ".claude" / "agents"` expression

**Milestone:**
- `_get_agent_manager("project")` and `_get_agent_manager("user")` return different `AgentManager`
  instances (dict is in place even though user-scope wiring is deferred in handlers)
- All existing API tests pass (project scope behavior unchanged)
- `verifier.verify_agent_deployed()` and `verify_skill_*()` always called with explicit `*_dir`
  param
- `BackupManager` receives `agents_dir` from the handler, not from an internal hardcoded resolver
- Test confirms BackupManager is called with scope-resolved path

**Dependencies:** Phase 2 complete (DeploymentContext used inside `_get_agent_manager()`).

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Direct `_agent_manager` variable access in config_routes.py bypasses singleton fix | Medium | Run grep before coding; fix any direct accesses |
| `BackupManager.__init__` signature change breaks callers outside handlers | Medium | `grep -rn "BackupManager(" src/` to enumerate all call sites before changing |
| `_get_agent_manager("user")` called at test time before user-scope wiring is ready | Low | Dict returns user-scoped AgentManager correctly; only issue is if `~/.claude/agents/` doesn't exist. Add guard or let AgentManager return empty. |

---

### Phase 5: API Scope Parameter — Mutation Endpoints (Project-Only Validation)

**Objective:** Add optional `scope` parameter (defaulting to `"project"`) to all write endpoints.
In this iteration, `"project"` is the only accepted value; all other values return HTTP 400. The
design is explicitly extensible — adding user-scope means changing the validation in
`DeploymentContext.from_request_scope()` from `("project",)` to `("project", "user")`.
Existing API clients see no change.

**Must complete before:** Phase 6 (consistency — both mutation and read accept scope).

**API tasks** (from api-path-plan.md Phase 3, project-only variant):

| Task | Endpoint | File | Description |
|------|---------|------|-------------|
| 5.1 | `POST /api/config/agents/deploy` | `agent_deployment_handler.py` | Parse `scope` from body; validate via `DeploymentContext.from_request_scope(scope_str)`; agents_dir still resolves to project path; add scope to response |
| 5.2 | `DELETE /api/config/agents/{name}` | `agent_deployment_handler.py` | Parse `scope` from query param; validate; add scope to response |
| 5.3 | `POST /api/config/agents/deploy-collection` | `agent_deployment_handler.py` | Parse `scope` from body; validate once; add scope to batch response summary |
| 5.4 | `POST /api/config/skills/deploy` | `skill_deployment_handler.py` | Parse `scope`; validate; `configuration_yaml` still resolves to project path; add scope to response |
| 5.5 | `DELETE /api/config/skills/{name}` | `skill_deployment_handler.py` | Parse scope from query; validate; add scope to response |
| 5.6 | `GET/PUT /api/config/skills/deployment-mode` | `skill_deployment_handler.py` | Parse scope from query/body; validate; config path resolves to project path |
| 5.7 | `services/config_api/autoconfig_handler.py` | autoconfig | Reject `scope=user` with HTTP 400 `SCOPE_NOT_SUPPORTED`; project-only operation (this is correct for any scope value other than "project" given the current constraint) |

**Null-safety (R-3):** Parse scope as:
```python
scope_str = (body.get("scope", "project") or "project")
```
This coerces JSON `null` to the default. Only non-empty non-`"project"` strings trigger 400.

**Dashboard contract:** The dashboard should send `scope: "project"` explicitly in all POST
request bodies. This makes the scope contract visible at the call site and prepares for future
scope selector UI without a server-side change.

**Pre-coding prerequisites:** Before coding Tasks 5.4 and 5.5, verify method signatures:
```bash
grep -n "def deploy_skills" src/claude_mpm/services/skills_deployer.py
grep -n "def remove_skills" src/claude_mpm/services/skills_deployer.py
grep -n "def verify_skill" src/claude_mpm/services/config_api/deployment_verifier.py
```

**Test tasks** (from test-plan.md Phase 3, partial — only project-scope tests):

New files:
- `tests/services/config_api/test_agent_deployment_scope.py` — TC-3-01 through TC-3-08 (8 tests):
  deploy without scope (defaults to project), deploy explicit project scope, deploy invalid scope
  returns 400, deploy null scope defaults to project, undeploy without scope, undeploy invalid scope
- `tests/services/config_api/test_skill_deployment_scope.py` — TC-3-09 through TC-3-13 (5 tests):
  deploy without scope, deploy explicit project scope, deploy invalid scope, undeploy scope,
  undeploy without scope

Note: TC-3-03 (`test_deploy_agent_user_scope`) and TC-3-10 (`test_deploy_skill_user_scope`)
are deferred — these test user-scope wiring that is not implemented in this iteration.

**Milestone:**
- All 6 mutation endpoints accept optional `scope` defaulting to `"project"`
- `POST {"agent_name": "x"}` (no scope) → `{cwd}/.claude/agents/x.md` (identical to current)
- `POST {"agent_name": "x", "scope": "project"}` → `{cwd}/.claude/agents/x.md`
- `POST {"agent_name": "x", "scope": "workspace"}` → HTTP 400 `VALIDATION_ERROR`
- `POST {"agent_name": "x", "scope": "user"}` → HTTP 400 (user scope not yet supported)
- Response bodies include `"scope": "project"` field
- Autoconfig endpoints reject user scope with HTTP 400

**Dependencies:** Phase 4B complete (singleton trap fixed, verifier calls explicit, BackupManager wired).

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `SkillsDeployerService.deploy_skills()` missing `skills_dir` param | Medium | Check signature first; add param if absent |
| `scope: null` in JSON body triggers 400 | Medium | Use `or "project"` coercion pattern above |
| Response field `"scope"` conflicts with existing schema in Svelte types | Low | Additive field; JS ignores unknown fields; update types if linting catches it |

---

### Phase 6: API Scope Parameter — Read-Only Endpoints (Project-Only Validation)

**Objective:** Add `?scope=project` query param validation to all GET endpoints. Only `"project"`
is accepted; anything else returns HTTP 400. The per-scope `_agent_managers` dict (from Phase 4B)
is used, but only the project-scope manager is reachable via the API in this iteration.

**Must complete before:** Phase 7 (E2E tests need both mutation and read scope in place).

**API tasks** (from api-path-plan.md Phase 4, project-only variant):

| Task | Endpoint | File | Description |
|------|---------|------|-------------|
| 6.1 | `GET /api/config/agents/deployed` | `config_routes.py` | Parse `?scope=` from query; validate via `from_request_scope(scope_str)` (validates project-only); call `_get_agent_manager("project")`; include scope in response |
| 6.2 | `GET /api/config/project/summary` | `config_routes.py` | Parse scope; validate; use `ctx.skills_dir` and `ctx.configuration_yaml` for path resolution (both resolve to project paths) |
| 6.3 | `GET /api/config/skills/deployed` | `config_routes.py` | Parse scope; validate; replace `Path.cwd() / ".claude" / "skills"` with `ctx.skills_dir` |
| 6.4 | `GET /api/config/agents/agent-detail` (line 441) | `config_routes.py` | Parse scope; validate; use scoped manager |
| 6.5 | `GET /api/config/skills/skill-links` (line 523) | `config_routes.py` | Parse scope; validate; use `ctx.skills_dir` |
| 6.6 | `GET /api/config/validate` (line 834) | `config_routes.py` | Parse scope; validate; validate against project-scope dirs |

**Note on `handle_agents_available`:** Reads from the git template cache — scope-independent.
Do NOT add scope to this endpoint.

**Test tasks:**

New tests in `tests/services/config_api/test_config_routes_scope.py`:
- `test_deployed_agents_without_scope_reads_project` (TC-3-14)
- `test_deployed_agents_valid_project_scope_query_param` (TC-3-15, adapted — tests that
  `?scope=project` works, not `?scope=user`)
- `test_deployed_agents_invalid_scope_returns_400`
- `test_deployed_skills_without_scope_reads_project` (TC-3-16)
- `test_deployed_skills_valid_project_scope_query_param` (TC-3-17, adapted)
- `test_deployed_skills_invalid_scope_returns_400`

Note: TC-3-15 and TC-3-17 in v1 tested `?scope=user`. These are adapted to test `?scope=project`
as the valid case; a new test for `?scope=user` returning 400 is added.

**Milestone:**
- All GET endpoints accept optional `?scope=` query param defaulting to `"project"`
- `GET /api/config/agents/deployed?scope=project` returns same result as without scope param
- `GET /api/config/agents/deployed?scope=user` returns HTTP 400 `VALIDATION_ERROR`
- `GET /api/config/agents/deployed` (no scope) returns from `{cwd}/.claude/agents/` (unchanged)

**Dependencies:** Phase 4B complete (singleton fixed).

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Scope validation added to read endpoints breaks curl clients with no scope param | Low | Default is `"project"` — no scope param is identical to current behavior |
| Validation endpoint returns 500 for scope validation error | Low | Wrap validation error in try/except; return 400 not 500 |

---

### Phase 7: Code Cleanup + E2E Integration Tests

**Objective:** Retire the two dead/redundant path resolvers. Add `--scope` to the `skills`
command. Run end-to-end integration tests to confirm the complete CLI scope flow with real
filesystem. API E2E tests cover project scope only (user-scope API E2E is deferred).

**Must complete after:** Phases 4A and 6.

**Retire dead resolvers (from cli-path-plan.md Phase 6):**

| Task | File | Action |
|------|------|--------|
| 7.1 | `src/claude_mpm/cli/commands/configure_paths.py` | Migrate all call sites to use `core/config_scope.py` or `DeploymentContext`; then delete file |
| 7.2 | `src/claude_mpm/core/shared/path_resolver.py` | Confirm no external callers (grep); delete file |
| 7.3 | Any `import` statements referencing either file | Update to use `config_scope.py` or `DeploymentContext` directly |

Pre-delete check:
```bash
grep -r "configure_paths" src/ --include="*.py"
grep -r "path_resolver" src/ --include="*.py"
```

**Add `--scope` to `skills` command (from cli-path-plan.md Phase 7):**

| Task | File | Description |
|------|------|-------------|
| 7.4 | `src/claude_mpm/cli/commands/skills.py` | Parse `scope` from `args`; create `ctx = DeploymentContext.from_string(scope_str, project_dir)`; pass `ctx.skills_dir` to `SkillsDeployerService` |
| 7.5 | `src/claude_mpm/cli/main.py` (or argparse setup) | Add `--scope {project,user}` argument to `skills` subcommand |

**CLI E2E tests (from test-plan.md Phase 4, TC-4-01 through TC-4-10):**

File: `tests/e2e/test_scope_deployment_e2e.py` (new)

- `TestCLIScopeDeploymentE2E` (TC-4-01 through TC-4-06): CLI project + user scope for agents and
  skills, deploy-then-list consistency
- `TestCrossScopeIsolation` (TC-4-07 through TC-4-10): project deploy doesn't affect user dirs,
  disable-agent scope isolation

**API E2E tests (from test-plan.md Phase 4, project-scope only):**

- `TestAPIDeploymentE2E` (TC-4-11 and TC-4-13 only): API project scope for agents; API project
  scope for skills. TC-4-12 and TC-4-14 (user-scope API E2E) are deferred.
- `TestCrossPathIntegration` is deferred (requires user-scope API wiring).

**Skills scope tests (from test-plan.md Phase 2-D, TC-2-18 through TC-2-22):**

File: `tests/cli/commands/test_skills_scope.py` (new, 5 tests)

**Milestone:**
- `configure_paths.py` deleted; no references in codebase
- `core/shared/path_resolver.py` deleted; no references in codebase
- Path resolver count: 3 → 1 (`config_scope.py` is canonical)
- `claude-mpm skills deploy my-skill --scope user` deploys to `~/.claude/skills/my-skill/`
- CLI E2E tests pass (TC-4-01 through TC-4-10): 10 tests with real filesystem
- API project-scope E2E tests pass (TC-4-11 and TC-4-13): 2 tests
- All 5 skills scope tests pass

**Dependencies:** Phases 4A and 6 complete; Phase 4B implicitly required via Phase 6.

**Responsibility:** engineer + refactoring-engineer (for safe deletion)

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `configure_paths.py` used by code not found in grep (dynamic import) | Low | Check `importlib.import_module` usage; check `__all__` exports |
| `path_resolver.py` imported by tests | Medium | `grep -r "path_resolver" tests/` before deletion |
| Skills command `argparse` conflict with existing `--scope` on parent parser | Medium | Check parent parser argument group; use `dest` disambiguation if needed |

---

## 4. Dependency Graph

```
Phase 1: Test Foundation
  ─────────────────────────────────────────────────────
  CLI: characterization tests (xfail user-scope deploy)
  API: characterization tests + conftest fixtures
  Tests: TC-0-01 → TC-0-12, shared fixtures
  NOTE: TC-0-04 + TC-0-05 written as xfail here; deleted in Phase 4A
  ─────────────────────────────────────────────────────
         |
         v
Phase 2: DeploymentContext Core
  ─────────────────────────────────────────────────────
  NEW: core/deployment_context.py (~65 lines)
  from_request_scope() validates project-only (extensible)
  Tests: TC-1-01 → TC-1-23 (23 tests, all green)
  ─────────────────────────────────────────────────────
         |
         v
Phase 3: CLI Config Wire (pure refactor)
  ─────────────────────────────────────────────────────
  configure.py: run() + __init__() + _switch_scope()
  No new tests; existing tests stay green
  ─────────────────────────────────────────────────────
         |
    ─────┼──────────────────────────────────────────────┐
    ↓ (after Phase 3)                                    ↓ (after Phase 2, parallel)
Phase 4A: CLI Bug Fix                          Phase 4B: API Singleton Fix
  ─────────────────────────────                  + BackupManager scope extension
  configure.py: 6 hardcoded path sites          ─────────────────────────────────
  Tests: TC-2-01 → TC-2-17 (17 tests)           config_routes.py: singleton → dict
  DELETE TC-0-04, TC-0-05                        backup_manager.py: accept agents_dir
  ─────────────────────────────                  Tests: singleton scoping (2 tests)
                                                  Test: BackupManager path wiring (1 test)
                                                  ─────────────────────────────────
                                                         |
                              ───────────────────────────┤
                             |                           |
                             ↓                           ↓
                  Phase 5: API Mutation Scope  Phase 6: API Read-Only Scope
                  (project-only validation)    (project-only validation)
                  ─────────────────────────   ─────────────────────────
                  6 mutation endpoints         6 read endpoints
                  scope param: project only    scope param: project only
                  user→400, invalid→400        user→400, invalid→400
                  Tests: ~13 tests             Tests: ~6 tests
                  ─────────────────────────   ─────────────────────────
                             |                           |
                    ─────────┴───────────────────────────┘
                    ↓ (after Phase 4A and Phase 6 both complete)
                Phase 7: Code Cleanup + E2E Tests
                  ─────────────────────────────────────────────────────
                  Delete configure_paths.py, path_resolver.py
                  Add skills --scope
                  CLI E2E: TC-4-01 → TC-4-10 (10 tests, real FS)
                  API E2E: TC-4-11, TC-4-13 (project scope only)
                  Skills: TC-2-18 → TC-2-22 (5 tests)
                  ─────────────────────────────────────────────────────
```

**Phases 4A and 4B are the ONLY phases that can run simultaneously.**

**Deferred work (not in this graph):**
- `from_request_scope` validation expanded to include `"user"`
- User-scope wiring in Phase 5/6 handlers
- Socket.IO scope metadata
- Dashboard integration notes document
- TC-4-12, TC-4-14 (API user-scope E2E)
- TC-4-15, TC-4-16 (CLI→API cross-path integration)

---

## 5. Responsibility Matrix (RACI-Style)

| Deliverable | Implements | Reviews | Tests | Approves |
|-------------|-----------|---------|-------|---------|
| Characterization tests (Phase 1) | test-engineer | engineer | test-engineer | team-lead |
| `core/deployment_context.py` (Phase 2) | engineer | test-engineer | test-engineer | team-lead |
| CLI config path wire (Phase 3) | engineer | test-engineer | test-engineer | team-lead |
| CLI bug fix: agent + skill paths (Phase 4A) | engineer | test-engineer | test-engineer | team-lead |
| Delete TC-0-04/TC-0-05 (Phase 4A) | engineer | test-engineer | — | team-lead |
| API singleton fix (Phase 4B) | engineer | test-engineer | test-engineer | team-lead |
| BackupManager scope extension (Phase 4B) | engineer | test-engineer | test-engineer | team-lead |
| API mutation scope param (Phase 5) | engineer | test-engineer | test-engineer | team-lead |
| API read-only scope param (Phase 6) | engineer | test-engineer | test-engineer | team-lead |
| Code cleanup: retire resolvers (Phase 7) | refactoring-engineer | engineer | test-engineer | team-lead |
| Skills command `--scope` (Phase 7) | engineer | test-engineer | test-engineer | team-lead |
| E2E integration tests (Phase 7) | test-engineer | engineer | test-engineer | team-lead |

---

## 6. Risk Register

### R-1: CLI `shutil.copy2` vs `AgentDeploymentService.deploy_agent()` (Behavior Masquerade)

**Source:** devils-advocate.md, Section 8, Risk 1
**Description:** The CLI's `_deploy_single_agent()` uses `shutil.copy2` (a direct file copy). Phase 4A
must only change the **target directory**, not the copy mechanism.
**Severity:** High
**Phase:** 4A
**Mitigation:** Read the exact code at `configure.py:~3047` before changing. Do not alter the copy
call itself. Characterization tests confirm the copy mechanism.
**Status:** Mitigated by plan design.

### R-2: Singleton Trap Causes Silent Wrong-Scope Reads

**Source:** api-path-plan.md Phase 2; devils-advocate.md, Section 6
**Description:** If scope is added to API endpoints before the singleton is fixed, user-scope GET
requests silently read from the project-scope `AgentManager`.
**Severity:** Critical
**Phase:** 4B (fix must precede Phase 5)
**Mitigation:** Phase ordering enforces 4B before 5. Per-scope dict tests confirm the singleton
is gone.
**Status:** Mitigated by phase ordering.

### R-3: Backward Compatibility — `scope: null` or `scope: ""`

**Source:** devils-advocate.md, Section 8, Risk 2 (Missing Risk 5)
**Description:** Adding scope validation means `scope: null` could trigger a new HTTP 400. Existing
clients send no scope field; only malformed clients sending explicit `null` could break.
**Severity:** Medium
**Phase:** 5
**Mitigation:** Parse scope as `body.get("scope", "project") or "project"` — coerces null to default.
Only non-empty, non-`"project"` strings get 400 in this iteration.
**Status:** Mitigated in implementation detail.

### R-4: `DeploymentVerifier` Hardcoded Path

**Source:** devils-advocate.md, Section 8, Risk 4
**Description:** `deployment_verifier.py` captures `default_agents_dir` at lazy-init time.
Without explicit `agents_dir` param, verifier checks wrong directory.
**Severity:** High
**Phase:** 4B
**Mitigation:** Tasks 4B.3 and 4B.4 make all `verifier.verify_*()` calls explicitly pass
`agents_dir` or `skills_dir`. The default is never used.
**Status:** Mitigated by Phase 4B design.

### R-5: BackupManager Backs Up Wrong Directory for User-Scope Operations

**Source:** devils-advocate.md, Section 7, MUST-3; Gap 2
**Description:** `BackupManager` previously hardcoded project-scope path. For user-scope operations
(when wired in a future iteration), an unhardcoded BackupManager would back up the wrong directory.
**Severity:** High (safety protocol)
**Phase:** 4B
**Mitigation:** Task 4B.5–4B.7 extend BackupManager to receive the scope-resolved path explicitly.
For this iteration (project scope only), behavioral change is zero; architectural correctness is
established.
**Status:** Resolved in Phase 4B (MUST-3).

### R-6: Cross-Scope Isolation — Deploy Bleeds into Wrong Scope

**Source:** test-plan.md, Phase 4-B
**Description:** A path resolution bug could cause a user-scope CLI deploy to write into the
project directory (or vice versa).
**Severity:** High (data integrity)
**Phase:** 7 (E2E verification)
**Mitigation:** TC-4-07 and TC-4-08 test that deploying to one scope does not affect the other.
These are E2E tests with real filesystem (no path mocking).
**Status:** Detected by Phase 7 tests.

### R-7: Circular Import in `core/__init__.py`

**Source:** cli-path-plan.md Phase 2 risk
**Description:** Adding `DeploymentContext` to `core/__init__.py` could create a circular import.
**Severity:** Medium
**Phase:** 2
**Mitigation:** Use lazy import pattern in `__init__.py` if circular import detected.
**Status:** Contingency plan ready.

### R-8: YAGNI Risk on API Scope (MUST-1)

**Source:** devils-advocate.md, Section 4
**Description:** In v1 this risk was dismissed with a feature-flag mitigation. In v2 it is resolved:
the full user-scope API wiring is deferred. The scope parameter is added only as project-scope
validation with an extensible design. The risk is now "extensible design is never used" rather
than "YAGNI on 14 endpoints."
**Severity:** Low (residual — extensible design is cheap)
**Resolution:** Scoped down per MUST-1. The parameter structure prepares for future user-scope
without the implementation cost.
**Status:** Resolved by MUST-1 decision.

### R-9: TC-0-04/TC-0-05 xfail Contradiction

**Source:** devils-advocate.md, Section 7, MUST-2; Gap 1
**Description:** v1 said to "remove xfail markers" from TC-0-04/05 after Phase 4A. The assertions
document broken behavior and would fail with new behavior, not pass.
**Severity:** Critical (would fail CI)
**Resolution:** TC-0-04 and TC-0-05 are deleted in Phase 4A. TC-2-01 and TC-2-02 replace them.
**Status:** Resolved by MUST-2 decision.

### R-10: Test Coverage Decrease at Any Phase

**Source:** Plan constraint
**Description:** Any phase that modifies production code without adding corresponding tests could
leave gaps.
**Severity:** Medium
**Mitigation:** Each phase's "Milestone" section specifies the exact tests that must pass.
Pre-condition checks: `pytest --cov=claude_mpm --cov-fail-under=<current_threshold>`.
**Status:** Enforced by phase milestone criteria.

---

## 7. Definition of Done

The scope abstraction effort for this iteration is **complete** when ALL of the following are true:

### CLI

- [ ] `claude-mpm configure --scope user` deploys agent `.md` files to `~/.claude/agents/`
- [ ] `claude-mpm configure --scope user` deploys skill directories to `~/.claude/skills/`
- [ ] `claude-mpm configure --scope project` (or no scope) behavior is identical to pre-change
- [ ] `claude-mpm skills deploy <name> --scope user` deploys to `~/.claude/skills/<name>/`
- [ ] `claude-mpm skills deploy <name>` behavior is identical to pre-change
- [ ] `configure_paths.py` is deleted from the codebase
- [ ] `core/shared/path_resolver.py` is deleted from the codebase
- [ ] `core/config_scope.py` is the sole canonical path resolver
- [ ] `self._ctx` (`DeploymentContext`) is initialized in `ConfigureCommand.__init__()` and
      recreated in `_switch_scope()`

### API

- [ ] All 6 mutation endpoints accept optional `scope` defaulting to `"project"`
- [ ] All 6 read endpoints accept optional `?scope=` query param defaulting to `"project"`
- [ ] `scope: "project"` (explicit) routes to `{cwd}/.claude/agents/` or `{cwd}/.claude/skills/`
- [ ] `scope: "user"` returns HTTP 400 (not yet supported — by design in this iteration)
- [ ] `scope: "invalid"` returns HTTP 400 `VALIDATION_ERROR`
- [ ] No singleton trap: `_agent_managers` dict is in place; project-scope manager is wired
- [ ] `BackupManager` receives scope-resolved `agents_dir` from the handler (not hardcoded)
- [ ] Autoconfig endpoints explicitly reject user scope with HTTP 400 `SCOPE_NOT_SUPPORTED`
- [ ] Response bodies include `"scope": "project"` field on all mutation and read responses

### Shared

- [ ] `src/claude_mpm/core/deployment_context.py` exists (~65 lines)
- [ ] `DeploymentContext.from_project()`, `.from_user()`, `.from_request_scope("project")` all work
- [ ] `DeploymentContext.from_request_scope("user")` raises `ValueError` (project-only API constraint)
- [ ] `DeploymentContext` is frozen (immutable) — `ctx.scope = X` raises `FrozenInstanceError`
- [ ] `DeploymentContext` is hashable (usable as dict key)

### Tests

- [ ] All 16 characterization tests pass on the pre-change codebase (Phase 1)
- [ ] TC-0-04 and TC-0-05 are absent from the test suite after Phase 4A (deleted)
- [ ] All 23 `test_deployment_context.py` unit tests pass (Phase 2)
- [ ] All 17 CLI scope behavior tests pass (Phase 4A)
- [ ] Singleton scoping tests pass (Phase 4B): 2 tests
- [ ] BackupManager scope wiring test passes (Phase 4B): 1 test
- [ ] API scope parameter tests pass (Phases 5 + 6): ~19 tests
- [ ] All 5 skills scope tests pass (Phase 7)
- [ ] CLI E2E tests pass (Phase 7): TC-4-01 through TC-4-10 (10 tests, real filesystem)
- [ ] API project-scope E2E tests pass (Phase 7): TC-4-11 and TC-4-13 (2 tests)
- [ ] Total new tests: ~75
- [ ] Test coverage % is equal to or higher than before Phase 1

### Out of Scope — This Iteration (Deferred to Future Task)

- User-scope wiring in API handlers (Phase 5 Tasks 5.1–5.6 user-scope code path)
- `from_request_scope("user")` validation expansion
- Per-scope Socket.IO event routing
- Dashboard scope selector UI
- Dashboard integration notes document
- `dashboard-integration-notes.md` creation (was Phase 8 in v1)
- TC-4-12, TC-4-14 (API user-scope E2E tests)
- TC-4-15, TC-4-16 (CLI deploy → API read cross-path tests)
- Archive feature removal (`unused/` directory handling)
- CLI safety protocol (backup/journal/verify) — remains API-only
- `ConfigurationService` facade (Strategy 2) — deferred if/when needed
- `is_enabled` / `is_deployed` unified `AgentInfo` dataclass — state model complexity deferred

---

## Appendix: File Change Summary

### Production Files

| File | Action | Phase | Approx Lines Changed |
|------|--------|-------|---------------------|
| `src/claude_mpm/core/deployment_context.py` | **NEW** | 2 | +65 |
| `src/claude_mpm/core/__init__.py` | Modified | 2 | +1 |
| `src/claude_mpm/core/config_scope.py` | Modified (docstring only) | 1 | +15 |
| `src/claude_mpm/cli/commands/configure.py` | Modified | 3, 4A | +30, -20 |
| `src/claude_mpm/cli/commands/skills.py` | Modified | 7 | +25 |
| `src/claude_mpm/cli/commands/configure_paths.py` | **DELETED** | 7 | -80 |
| `src/claude_mpm/core/shared/path_resolver.py` | **DELETED** | 7 | -80 |
| `src/claude_mpm/services/monitor/config_routes.py` | Modified | 4B, 6 | +40 |
| `src/claude_mpm/services/config_api/agent_deployment_handler.py` | Modified | 4B, 5 | +40 |
| `src/claude_mpm/services/config_api/skill_deployment_handler.py` | Modified | 4B, 5 | +40 |
| `src/claude_mpm/services/config_api/autoconfig_handler.py` | Modified | 5 | +10 |
| `src/claude_mpm/services/config_api/backup_manager.py` | Modified | 4B | +15 |

### Test Files

| File | Action | Phase | Test Count |
|------|--------|-------|-----------|
| `tests/conftest.py` | Modified (fixtures added) | 1 | — |
| `tests/cli/commands/test_configure_unit.py` | Modified (tests added) | 1 | +6 |
| `tests/cli/commands/test_skills_cli.py` | Modified | 1 | +1 |
| `tests/cli/commands/test_configure_scope_characterization.py` | **NEW** | 1 | 12 (TC-0-04, TC-0-05 deleted in Phase 4A) |
| `tests/services/config_api/test_scope_characterization.py` | **NEW** | 1 | 4 |
| `tests/integration/api/conftest.py` | **NEW** | 1 | — |
| `tests/core/test_scope_selector.py` | **NEW** | 1→2 | 7→12 |
| `tests/unit/core/test_deployment_context.py` | **NEW** | 2 | 23 |
| `tests/cli/commands/test_configure_scope_behavior.py` | **NEW** | 4A | 17 |
| `tests/unit/services/monitor/test_agent_manager_scoping.py` | **NEW** | 4B | 2 |
| `tests/unit/services/config_api/test_backup_manager_scope.py` | **NEW** | 4B | 1 |
| `tests/services/config_api/test_agent_deployment_scope.py` | **NEW** | 5 | ~8 (user-scope tests deferred) |
| `tests/services/config_api/test_skill_deployment_scope.py` | **NEW** | 5 | ~5 (user-scope tests deferred) |
| `tests/services/config_api/test_config_routes_scope.py` | **NEW** | 5+6 | ~6 |
| `tests/cli/commands/test_skills_scope.py` | **NEW** | 7 | 5 |
| `tests/e2e/test_scope_deployment_e2e.py` | **NEW** | 7 | 12 (CLI: 10, API project: 2; user-scope E2E deferred) |

### Documentation Files

| File | Action | Note |
|------|--------|------|
| `docs-local/agent_skill_scope_selection/plans/decisions-log.md` | **NEW** | Records MUST-1/2/3 decisions |
| `docs-local/agent_skill_scope_selection/plans/master-plan-v2.md` | **NEW** (this file) | Supersedes v1 |
| `docs-local/agent_skill_scope_selection/plans/master-plan.md` | Preserved unchanged | History; not to be modified |

---

*Total estimated implementation time: 7 phases, independently mergeable, each ~1–3 hours of
focused engineering. Critical path: Phase 1 → 2 → 3 → 4A+4B → 5 → 6 → 7.*

*When user-scope API wiring is ready to implement, the extension points are:*
*1. Change `from_request_scope` validation from `("project",)` to `("project", "user")`*
*2. Wire `ctx.agents_dir` / `ctx.skills_dir` in Phase 5 handlers (already `ctx`-based)*
*3. Wire `_get_agent_manager(scope_str)` in Phase 6 read handlers (dict already keyed by scope)*
*4. Add TC-4-12, TC-4-14 (API user-scope E2E tests)*
*5. Add TC-4-15, TC-4-16 (cross-path integration tests)*
*No structural changes required — the extensible design does its job.*
