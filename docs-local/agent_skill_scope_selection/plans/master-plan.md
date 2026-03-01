# Master Implementation Plan: Scope-Aware Agent & Skill Deployment

**Author:** master-integrator (Research Agent)
**Date:** 2026-02-28
**Branch:** agent_skill_scope_selection
**Synthesized from:**
- `docs-local/agent_skill_scope_selection/plans/cli-path-plan.md` (7 phases)
- `docs-local/agent_skill_scope_selection/plans/api-path-plan.md` (6 phases, labeled 0–5)
- `docs-local/agent_skill_scope_selection/plans/test-plan.md` (~100 tests, 5 phases)
- `docs-local/agent_skill_scope_selection/research/implementation-strategies.md`
- `docs-local/agent_skill_scope_selection/research/abstraction-opportunities.md`
- `docs-local/agent_skill_scope_selection/research/devils-advocate.md`

---

## 1. Executive Summary

### Problem Statement

When a user runs `claude-mpm configure --scope user`, agent files still deploy to
`{cwd}/.claude/agents/` and skills still deploy to `{cwd}/.claude/skills/`. The `--scope user`
flag silently affects only metadata (`agent_states.json` location) — not file deployment. On the
API side, all 14+ call sites hardcode `ConfigScope.PROJECT`; a singleton `_agent_manager` in
`config_routes.py` is initialized once with the project path and never re-keyed by scope, creating
a silent data-corruption trap if user-scope reads are added before fixing it.

### Solution Approach

**Strategy 1: DeploymentContext** — a ~65-line frozen dataclass at `core/deployment_context.py`
that captures (scope, project_path) and exposes `agents_dir`, `skills_dir`, and `config_dir`
properties by delegating to the existing `core/config_scope.py` resolvers. Both CLI and API create
one context at the entry point and carry it through. No path logic lives in the dataclass — it
wraps what already works.

The plan is organized in **9 unified phases**. Phases 1–3 carry zero behavioral change.
Phase 4 fixes the actual bugs (CLI deploy paths + API singleton). Phases 5–8 extend scope to the
full API surface. Phase 9 closes with end-to-end integration tests.

### Total Estimated Scope

| Category | Count |
|----------|-------|
| New production files | 1 (`core/deployment_context.py`, ~65 lines) |
| Production files modified | 8 |
| Files deleted | 2 (`configure_paths.py`, `path_resolver.py`) |
| New test files | 10 |
| Total new tests | ~100 |
| Total net lines (prod) | ~+150 new / ~-160 deleted / ~+200 modified |

### Success Criteria

1. `claude-mpm configure --scope user` deploys agent `.md` files to `~/.claude/agents/`
2. `claude-mpm configure --scope user` deploys skill directories to `~/.claude/skills/`
3. `POST /api/config/agents/deploy {"scope": "user", "agent_name": "X"}` places `X.md` in
   `~/.claude/agents/X.md` (not in the project directory)
4. All existing CLI and API tests pass unchanged (backward compatibility preserved)
5. No singleton trap: `_get_agent_manager("project")` and `_get_agent_manager("user")` return
   independent `AgentManager` instances
6. `configure_paths.py` and `core/shared/path_resolver.py` are deleted (resolver count: 3 → 1)
7. Test coverage increases at every phase (never decreases)
8. Every phase is independently mergeable (CI green after each)

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
                                │
                                ├── Phase 5: API Mutation Scope
                                │       │
                                │       └── Phase 8: Socket.IO + Dashboard Notes
                                │
                                ├── Phase 6: API Read-Only Scope
                                │
                                └── Phase 7: Code Cleanup ← retire dead resolvers + skills --scope
                                                │
                                                └── Phase 9: E2E Integration Tests
```

**Phases 4A and 4B are the only parallel phases.** All other phases must proceed in the order
shown. Phase 9 (E2E) requires both 4A and 6 to be complete.

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
| 0.1 | `src/claude_mpm/core/config_scope.py` docstring | Document semantics: PROJECT=`{cwd}/.claude/`, USER=`~/.claude/` |
| 0.2 | `tests/unit/services/config_api/test_scope_current_behavior.py` (new) | API characterization: hardcoded PROJECT scope, `_get_config_path()`, singleton behavior |
| 0.3 | `tests/integration/api/conftest.py` (new) | Shared aiohttp test client fixtures, `tmp_path` project dirs, fake home dirs |

**Test tasks** (from test-plan.md Phase 0):

- **TC-0-01 through TC-0-06** (file: `tests/cli/commands/test_configure_scope_characterization.py`)
  — CLI scope characterization: project config dir, user config dir, missing scope default,
  deploy target (project), deploy target (user, XFAIL), scope toggle
- **TC-0-07, TC-0-08** (same file) — skills scope current behavior: `_get_deployed_skill_ids()`
  reads from cwd, `_uninstall_skill_by_name()` removes from cwd
- **TC-0-09 through TC-0-12** (file: `tests/services/config_api/test_scope_characterization.py`)
  — API current assumptions: handlers hardcode PROJECT, singleton initializes once

Add shared fixtures to `tests/conftest.py`:
- `project_scope_dirs` — standard `.claude/agents/`, `.claude/skills/`, `.claude-mpm/` under tmp_path
- `user_scope_dirs` — same but under a patched `Path.home()` (fake home)
- `both_scopes` — composite fixture for cross-scope isolation tests

**Milestone:** All 16 characterization tests + new fixtures committed. `pytest --tb=short` shows:
- 12 CLI tests: some PASS (project scope), some XFAIL (user scope deploy)
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
wrapper, not a resolver. All path logic remains in `config_scope.py`.

**Must complete before:** Phases 3, 4A, 4B.

**CLI tasks** (from cli-path-plan.md Phase 2):

| Task | File | Description |
|------|------|-------------|
| 2.1 | `src/claude_mpm/core/deployment_context.py` (new) | Frozen dataclass: `from_project()`, `from_user()`, `from_string()`; properties: `agents_dir`, `skills_dir`, `config_dir` |
| 2.2 | `src/claude_mpm/core/__init__.py` | Add `from .deployment_context import DeploymentContext` (check for circular imports first) |
| 2.3 | `tests/core/test_scope_selector.py` | Remove xfail markers; add immutability + equality + hashability tests |

**API tasks** (from api-path-plan.md Phase 1):

| Task | File | Description |
|------|------|-------------|
| 1.1 | `src/claude_mpm/core/deployment_context.py` | Same file as CLI Task 2.1 — **one shared implementation** |
| 1.2 | `tests/unit/core/test_deployment_context.py` (new) | 6 unit tests for all factory methods and properties |

**Note on API vs CLI `DeploymentContext` spec:** The API plan adds `configuration_yaml` and
`archive_dir` properties; the CLI plan omits them as "API concern." **Resolution:** Include
`configuration_yaml` in the dataclass (used by Phase 5 API work). Omit `archive_dir` (archive
feature is out of scope per constraints). The single file satisfies both plans.

**Final `DeploymentContext` properties:**
- `agents_dir` → `resolve_agents_dir(scope, project_path)`
- `skills_dir` → `resolve_skills_dir(scope, project_path)`
- `config_dir` → `resolve_config_dir(scope, project_path)`
- `configuration_yaml` → `config_dir / "configuration.yaml"`

**Factory method name alignment:** API plan uses `from_request_scope()`; CLI plan uses
`from_string()`. **Resolution:** Provide both as aliases:
```python
from_string = from_request_scope  # CLI backward compat
```

**Test tasks** (from test-plan.md Phase 1, TC-1-01 through TC-1-23):

Full coverage of `TestDeploymentContextFactories`, `TestDeploymentContextPathProperties`,
`TestDeploymentContextImmutability`, `TestDeploymentContextEdgeCases` — 23 tests total.

**Milestone:**
- `src/claude_mpm/core/deployment_context.py` exists and imports cleanly
- All 23 tests in `test_deployment_context.py` pass
- All TDD tests in `test_scope_selector.py` now pass (xfail removed)
- `python -c "from claude_mpm.core import DeploymentContext; print('OK')"` succeeds
- No existing test regressions

**Dependencies:** Phase 1 complete.

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Circular import in `core/__init__.py` | Medium | Import `DeploymentContext` lazily or check import graph first |
| CLI `from_string()` raises for `None` scope | Low | Guard: `if not scope_str: raise ValueError(...)` |
| `configuration_yaml` property added raises `AttributeError` in tests expecting old interface | Low | Tests are new — no existing code reads `configuration_yaml` yet |

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
| `_switch_scope()` resets `_navigation = None`, causing missing `current_scope` on reinit | Medium | Navigation property getter already syncs `current_scope` on first access (line 468 of configure.py) — no change needed |
| Golden tests capture `.claude-mpm/` path as a string and break | Low | `DeploymentContext.config_dir` returns the identical path value |

---

### Phase 4A: CLI Bug Fix (Parallel with 4B)

**Objective:** Fix the actual CLI scope bug. Wire `self._ctx.agents_dir` and `self._ctx.skills_dir`
into the 6 hardcoded deploy-path sites in `configure.py`. The XFAIL tests from Phase 1 now turn green.

**Must complete before:** Phase 9.
**Can run in parallel with:** Phase 4B (API Singleton Fix).

**CLI tasks** (from cli-path-plan.md Phases 4 and 5):

**Agent deploy fix** (Phase 4 in CLI plan):

| Task | File | Line(s) | Change |
|------|------|---------|--------|
| 4A.1 | `configure.py` | `_deploy_single_agent()` ~3073 | Replace `self.project_dir / ".claude" / "agents"` with `self._ctx.agents_dir` |

**Skill deploy fixes** (Phase 5 in CLI plan):

| Task | File | Line(s) | Change |
|------|------|---------|--------|
| 4A.2 | `configure.py` | `_get_deployed_skill_ids()` ~1279 | Replace `Path.cwd() / ".claude" / "skills"` with `self._ctx.skills_dir` |
| 4A.3 | `configure.py` | `_install_skill()` ~1301 | Replace `Path.cwd() / ".claude" / "skills" / skill.skill_id` with `self._ctx.skills_dir / skill.skill_id` |
| 4A.4 | `configure.py` | `_install_skill_from_dict()` ~1344 | Replace `Path.cwd() / ".claude" / "skills" / deploy_name` with `self._ctx.skills_dir / deploy_name` |
| 4A.5 | `configure.py` | `_uninstall_skill()` ~1321 | Replace `Path.cwd() / ".claude" / "skills" / skill.skill_id` with `self._ctx.skills_dir / skill.skill_id` |
| 4A.6 | `configure.py` | `_uninstall_skill_by_name()` ~1360 | Replace `Path.cwd() / ".claude" / "skills" / skill_name` with `self._ctx.skills_dir / skill_name` |

**Test tasks** (from test-plan.md Phase 2, TC-2-01 through TC-2-17):

Files:
- `tests/cli/commands/test_configure_scope_behavior.py` (new, 17 tests)
  - `TestConfigureAgentScopeDeployment`: TC-2-01 through TC-2-06
  - `TestConfigureSkillScopeDeployment`: TC-2-07 through TC-2-13
  - `TestConfigureScopeValidation`: TC-2-14 through TC-2-17

Previously-XFAIL tests in `test_configure_unit.py` (TC-0-04, TC-0-05) now pass and should have
their `xfail` marker removed.

**Milestone:**
- All 6 hardcoded path sites in `configure.py` use `self._ctx.agents_dir` or `self._ctx.skills_dir`
- `claude-mpm configure --scope user` places files in `~/.claude/agents/` and `~/.claude/skills/`
- 17 new CLI scope tests pass
- Formerly-XFAIL tests TC-0-04, TC-0-05 now PASS (xfail markers removed)
- All other existing tests still pass

**Dependencies:** Phase 3 complete.

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `_deploy_single_agent()` also calls `AgentDeploymentService.deploy_agent()` (not just shutil.copy2) — behavior change masked as refactor | Medium | Read the exact current code at `configure.py:3047` before changing; the CLI does use `shutil.copy2` directly (confirmed in abstraction research), NOT `AgentDeploymentService`. Path change only. |
| `~/.claude/agents/` does not exist — mkdir fails silently | Low | Add `self._ctx.agents_dir.mkdir(parents=True, exist_ok=True)` before copy |
| Closure captures stale path in skill install loops | Low | Compute `self._ctx.skills_dir` once per call, not inside a lambda |

---

### Phase 4B: API Singleton Fix (Parallel with 4A)

**Objective:** Eliminate the `_agent_manager` singleton trap in `config_routes.py` BEFORE any
scope parameter is added to API endpoints. This is the highest-risk safety gate: adding scope to
the API without this fix would silently route user-scope reads to project-scope directories.

**Must complete before:** Phases 5, 6.
**Can run in parallel with:** Phase 4A.

**API tasks** (from api-path-plan.md Phase 2):

| Task | File | Description |
|------|------|-------------|
| 4B.1 | `services/monitor/config_routes.py` | Replace `_agent_manager = None` singleton with `_agent_managers: Dict[str, Any] = {}` per-scope dict; update `_get_agent_manager(scope: str = "project")` |
| 4B.2 | `services/monitor/config_routes.py` | Update all callers of `_get_agent_manager()` to pass `"project"` explicitly (no behavior change at this phase) |
| 4B.3 | `services/config_api/agent_deployment_handler.py` | Make `verifier.verify_agent_deployed(name)` calls explicitly pass `agents_dir=agents_dir` (no scope change yet — still PROJECT) |
| 4B.4 | `services/config_api/skill_deployment_handler.py` | Make `verifier.verify_skill_*()` calls explicitly pass `skills_dir=skills_dir` |

**Pre-coding check for Task 4B.1:**
```bash
grep -n "_agent_manager" src/claude_mpm/services/monitor/config_routes.py
```
Ensure no direct `_agent_manager` access bypasses `_get_agent_manager()`.

**Test tasks** (from test-plan.md Phase 3-D, TC-3-18 and TC-3-19):

File: `tests/unit/services/monitor/test_agent_manager_scoping.py` (new)
- `test_project_and_user_managers_are_independent`: clears dict, calls both scopes, asserts `is not`
- `test_same_scope_returns_cached_manager`: calls project scope twice, asserts `is`

Also from api-path-plan.md Task 2.4 (regression tests).

**Milestone:**
- `_get_agent_manager("project")` and `_get_agent_manager("user")` return different `AgentManager`
  instances with different `project_dir` values
- All existing API tests pass (project scope behavior unchanged — all callers pass `"project"`)
- `verifier.verify_agent_deployed()` and `verify_skill_*()` always called with explicit `*_dir`
  param in all handlers

**Dependencies:** Phase 2 complete (DeploymentContext used inside `_get_agent_manager()`).

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Direct `_agent_manager` variable access in config_routes.py bypasses singleton fix | Medium | Run grep before coding; fix any direct accesses to use `_get_agent_manager()` |
| `_get_agent_manager("user")` fails because `~/.claude/agents/` doesn't exist | Medium | `AgentManager` should return empty list for missing dir; write test to confirm |
| `DeploymentContext` import in `config_routes.py` causes circular import | Low | Use lazy import inside `_get_agent_manager()` if needed |

---

### Phase 5: API Scope — Mutation Endpoints

**Objective:** Add optional `scope` parameter (defaulting to `"project"`) to all write endpoints:
deploy/undeploy for agents and skills, plus deployment-mode read/write. Existing API clients see
no change. New behavior gated behind explicit `scope: "user"` in request.

**Must complete before:** Phase 8.

**API tasks** (from api-path-plan.md Phase 3):

| Task | Endpoint | File | Description |
|------|---------|------|-------------|
| 5.1 | `POST /api/config/agents/deploy` | `agent_deployment_handler.py` | Parse `scope` from body; create `ctx = DeploymentContext.from_request_scope(scope_str)`; replace hardcoded `agents_dir`; add scope to response + event |
| 5.2 | `DELETE /api/config/agents/{name}` | `agent_deployment_handler.py` | Parse `scope` from query param; use `ctx.agents_dir`; add scope to response + event |
| 5.3 | `POST /api/config/agents/deploy-collection` | `agent_deployment_handler.py` | Parse `scope` from body once; use `ctx.agents_dir` in closure (compute before loop) |
| 5.4 | `POST /api/config/skills/deploy` | `skill_deployment_handler.py` | Parse `scope`; replace `_get_config_path()` with `ctx.configuration_yaml`; pass `skills_dir=ctx.skills_dir`; `mark_user_requested` writes to correct config path |
| 5.5 | `DELETE /api/config/skills/{name}` | `skill_deployment_handler.py` | Parse scope from query; pass `skills_dir=ctx.skills_dir` to remove_skills; explicit verifier call |
| 5.6 | `GET/PUT /api/config/skills/deployment-mode` | `skill_deployment_handler.py` | Parse scope from query/body; use `DeploymentContext.from_request_scope(scope_str).configuration_yaml` |
| 5.7 | `services/config_api/autoconfig_handler.py` | autoconfig | Reject `scope=user` with HTTP 400 `SCOPE_NOT_SUPPORTED`; project-only operation |
| 5.8 | `services/config_api/backup_manager.py` | backup | Add TODO comment: BackupManager always backs up project-scope dirs; user-scope improvement deferred |

**Pre-coding prerequisites:** Before coding Tasks 5.4 and 5.5, verify method signatures:
```bash
grep -n "def deploy_skills" src/claude_mpm/services/skills_deployer.py
grep -n "def remove_skills" src/claude_mpm/services/skills_deployer.py
grep -n "def verify_skill" src/claude_mpm/services/config_api/deployment_verifier.py
```
If `skills_dir` param is missing, add it as part of the task.

**Test tasks** (from test-plan.md Phase 3, TC-3-01 through TC-3-17):

New files:
- `tests/services/config_api/test_agent_deployment_scope.py` — TC-3-01 through TC-3-08 (8 tests)
- `tests/services/config_api/test_skill_deployment_scope.py` — TC-3-09 through TC-3-13 (5 tests)
- `tests/services/config_api/test_config_routes_scope.py` — TC-3-14 through TC-3-19 (6 tests)
- `tests/services/config_api/test_autoconfig_scope.py` — TC-3-20 through TC-3-23 (4 tests)

**Milestone:**
- All 6 mutation endpoints accept optional `scope` defaulting to `"project"`
- `POST {"agent_name": "x", "scope": "user"}` → `~/.claude/agents/x.md` created
- `POST {"agent_name": "x", "scope": "workspace"}` → HTTP 400 `VALIDATION_ERROR`
- `POST {"agent_name": "x"}` (no scope) → `{cwd}/.claude/agents/x.md` (identical to current)
- Autoconfig endpoints reject user scope with HTTP 400
- Response bodies include `"scope": "project"` or `"scope": "user"` field
- All 23 API scope tests pass

**Dependencies:** Phase 4B complete (singleton trap fixed, verifier calls explicit).

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `SkillsDeployerService.deploy_skills()` missing `skills_dir` param | Medium | Check signature first; add param if absent (small, well-contained change) |
| `~/.claude-mpm/configuration.yaml` doesn't exist for user-scope mode switch | High | `_load_config()` already returns `{}` for missing files; add `mkdir(parents=True)` before write |
| Closure captures wrong `agents_dir` in batch deploy loop | Low | Compute `agents_dir = ctx.agents_dir` once before loop, capture by value |
| `scope: null` in JSON body triggers 400 instead of defaulting to project | Medium | Use `body.get("scope", "project") or "project"` to handle null |

---

### Phase 6: API Scope — Read-Only Endpoints

**Objective:** Add `?scope=project|user` query param to all GET endpoints. Use the per-scope
`_agent_managers` dict (from Phase 4B) to read from the correct directory.

**Must complete before:** Phase 9.

**API tasks** (from api-path-plan.md Phase 4):

| Task | Endpoint | File | Description |
|------|---------|------|-------------|
| 6.1 | `GET /api/config/agents/deployed` | `config_routes.py` | Parse scope from query; call `_get_agent_manager(scope_str)`; include scope in response |
| 6.2 | `GET /api/config/project/summary` | `config_routes.py` | Parse scope; use `ctx.skills_dir` for skills count; use `ctx.configuration_yaml` for config path |
| 6.3 | `GET /api/config/skills/deployed` | `config_routes.py` | Replace `Path.cwd() / ".claude" / "skills"` with `ctx.skills_dir` |
| 6.4 | `GET /api/config/agents/agent-detail` (line 441) | `config_routes.py` | Add scope; use scoped manager |
| 6.5 | `GET /api/config/skills/skill-links` (line 523) | `config_routes.py` | Add scope; use `ctx.skills_dir` |
| 6.6 | `GET /api/config/validate` (line 834) | `config_routes.py` | Add scope; validate against scoped dirs; return valid-but-empty for non-existent user-scope dirs |

**Note on `handle_agents_available`:** This reads from the git template cache — scope-independent.
Do NOT add scope to this endpoint.

**Test tasks:** TC-3-14 through TC-3-17 (in `test_config_routes_scope.py`, 4 tests — already
listed in Phase 5 file but covering read endpoints).

**Milestone:**
- All GET endpoints accept optional `?scope=` query param defaulting to `"project"`
- `GET /api/config/agents/deployed?scope=user` returns agents from `~/.claude/agents/`
- `GET /api/config/agents/deployed` (no scope) returns from `{cwd}/.claude/agents/` (unchanged)
- Missing user-scope directory returns empty list, not error
- Dashboard can already test scope switching via curl without UI changes

**Dependencies:** Phase 4B complete (singleton fixed).

**Responsibility:** engineer

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `AgentManager.list_agents()` raises for non-existent `~/.claude/agents/` | Medium | Test with missing dir; add guard if needed |
| Validation endpoint returns 500 for missing user-scope config | Medium | Wrap missing-file cases in try/except; return valid-but-empty |

---

### Phase 7: Code Cleanup

**Objective:** Retire the two dead/redundant path resolvers. Add `--scope` to the `skills`
command. Reduces the path-resolution ecosystem from 3 implementations to 1.

**Must complete before:** Phase 9 (cleanup must land before E2E tests capture final file state).

**CLI tasks** (from cli-path-plan.md Phases 6 and 7):

**Retire dead resolvers (Phase 6 in CLI plan):**

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

**Add `--scope` to `skills` command (Phase 7 in CLI plan):**

| Task | File | Description |
|------|------|-------------|
| 7.4 | `src/claude_mpm/cli/commands/skills.py` | Parse `scope` from `args`; create `ctx = DeploymentContext.from_string(scope_str, project_dir)`; pass `ctx.skills_dir` to `SkillsDeployerService` |
| 7.5 | `src/claude_mpm/cli/main.py` (or argparse setup) | Add `--scope {project,user}` argument to `skills` subcommand |

**Test tasks** (from test-plan.md Phase 2-D, TC-2-18 through TC-2-22):

File: `tests/cli/commands/test_skills_scope.py` (new, 5 tests)
- `TestSkillsCommandScope`: deploy project, deploy user, default is project, list project, list user

**Milestone:**
- `configure_paths.py` deleted; no references in codebase
- `core/shared/path_resolver.py` deleted; no references in codebase
- Path resolver count: 3 → 1 (`config_scope.py` is canonical)
- `claude-mpm skills deploy my-skill --scope user` deploys to `~/.claude/skills/my-skill/`
- `claude-mpm skills deploy my-skill` (no scope) deploys to `{cwd}/.claude/skills/my-skill/`
- All 5 skills scope tests pass

**Dependencies:** Phase 4A complete (CLI scope already working); Phase 3 complete (DeploymentContext
in CLI). Tasks 7.1–7.3 can technically start after Phase 2 (once the call sites are identified).

**Responsibility:** engineer + refactoring-engineer (for safe deletion)

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `configure_paths.py` used by code not found in grep (dynamic import) | Low | Check `importlib.import_module` usage; also check `__all__` exports |
| `path_resolver.py` imported by tests (not just prod code) | Medium | `grep -r "path_resolver" tests/` before deletion |
| Skills command `argparse` conflict with existing `--scope` on parent parser | Medium | Check parent parser argument group; use `dest` disambiguation if needed |

---

### Phase 8: Socket.IO Events + Dashboard Integration Notes

**Objective:** Add `scope` metadata to all `config_event` Socket.IO emissions. Create a
documentation file for the frontend team describing dashboard changes needed for scope UI.

**Must complete before:** Phase 9.

**API tasks** (from api-path-plan.md Phase 5):

| Task | File | Description |
|------|------|-------------|
| 8.1 | `agent_deployment_handler.py` | Add `"scope": scope_str` to all `emit_config_event()` `data={}` calls |
| 8.2 | `skill_deployment_handler.py` | Same — all `emit_config_event()` calls include scope |
| 8.3 | `docs-local/agent_skill_scope_selection/plans/dashboard-integration-notes.md` (new) | Svelte component requirements: `ScopeSelector.svelte`, `configScope` store, fetch/mutation changes, feature flag `SCOPE_SELECTOR: false` |

**Test tasks:** No new tests. Verify via:
```bash
grep -rn "emit_config_event" src/claude_mpm/services/config_api/ | grep -v "scope"
```
This should return zero results after Task 8.1 and 8.2 are complete.

**Milestone:**
- Every `config_event` emission includes `data.scope`
- No emission is missing scope (grep check above shows zero results)
- Dashboard integration document exists at the specified path

**Dependencies:** Phase 5 complete (mutation endpoints emit events with scope context).

**Responsibility:** engineer (8.1, 8.2) + documentation-agent (8.3)

**Risk assessment:**

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Extra `scope` field in event data breaks existing Svelte event handlers | Low | JavaScript ignores unknown fields; `data.agent_name` still accessible |

---

### Phase 9: End-to-End Integration Tests

**Objective:** Validate the full scope flow end-to-end — from CLI or API entry point to filesystem
state — with no path mocking. Also validate cross-path consistency (CLI deploy → API read, and
vice versa).

**Must complete after:** Phases 4A and 6 (both paths functional).

**API tasks:** None. Phase 9 is tests-only.

**CLI tasks:** None.

**Test tasks** (from test-plan.md Phase 4, TC-4-01 through TC-4-16):

File: `tests/e2e/test_scope_deployment_e2e.py` (new, 16 tests)

- `TestCLIScopeDeploymentE2E` (TC-4-01 through TC-4-06): CLI project + user scope for agents and
  skills, deploy-then-list consistency
- `TestCrossScopeIsolation` (TC-4-07 through TC-4-10): project deploy doesn't affect user dirs,
  disable-agent scope isolation
- `TestAPIDeploymentE2E` (TC-4-11 through TC-4-14): API project + user scope for agents and skills
- `TestCrossPathIntegration` (TC-4-15 through TC-4-16): CLI deploy → API list, API deploy → CLI detect

**Milestone:**
- 16 E2E tests pass with real filesystem (no path mocking)
- Cross-scope isolation confirmed: deploying to project scope never modifies user-scope directories
- Cross-path integration confirmed: CLI and API agree on scope-resolved directories

**Dependencies:** Phases 4A and 6 complete. (Phase 4B is implicitly required via Phase 6.)

**Responsibility:** test-engineer

---

## 4. Dependency Graph

```
Phase 1: Test Foundation
  ─────────────────────────────────────────────────────
  CLI: characterization tests (xfail user-scope)
  API: characterization tests + conftest fixtures
  Tests: TC-0-01 → TC-0-12, shared fixtures
  ─────────────────────────────────────────────────────
         |
         v
Phase 2: DeploymentContext Core
  ─────────────────────────────────────────────────────
  NEW: core/deployment_context.py (~65 lines)
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
    ─────┼────────────────────────────────────────────────┐
    ↓ (after Phase 3)                                      ↓ (after Phase 2, parallel)
Phase 4A: CLI Bug Fix                            Phase 4B: API Singleton Fix
  ─────────────────────────────────                ─────────────────────────────────
  configure.py: 6 hardcoded path sites              config_routes.py: singleton → dict
  Tests: TC-2-01 → TC-2-17 (17 tests)               Tests: TC-3-18, TC-3-19 (2 tests)
  xfail TC-0-04, TC-0-05 → green                   Verifier calls made explicit
  ─────────────────────────────────                ─────────────────────────────────
         |                                                   |
         |                           ────────────────────────┤
         |                          |                        |
         ↓                          ↓                        ↓
Phase 7: Code Cleanup         Phase 5: API Mutation    Phase 6: API Read-Only
(can start after Phase 3)     ─────────────────────    ─────────────────────
  ─────────────────────        6 mutation endpoints     6 read endpoints
  Delete configure_paths.py    Tests: TC-3-01→TC-3-13   Tests: TC-3-14→TC-3-17
  Delete path_resolver.py      (23 tests)               (4 tests)
  Add skills --scope           ─────────────────────    ─────────────────────
  Tests: TC-2-18→TC-2-22               |
  ─────────────────────                v
         |                    Phase 8: Socket.IO + Docs
         |                    ─────────────────────────
         |                    Scope field in all events
         |                    Dashboard integration doc
         |                    ─────────────────────────
         |                             |
    ─────┴─────────────────────────────┘
    ↓ (after Phase 4A and Phase 6 both complete)
Phase 9: E2E Integration Tests
  ─────────────────────────────────────────────────────
  tests/e2e/test_scope_deployment_e2e.py
  TC-4-01 → TC-4-16 (16 tests)
  ─────────────────────────────────────────────────────
```

**Parallelism summary:**
- Phases 4A and 4B are the ONLY phases that can run simultaneously
- Phase 7 can start after Phase 3 (not blocked by Phase 4A)
- All other phases are strictly sequential within their track

---

## 5. Responsibility Matrix (RACI-Style)

| Deliverable | Implements | Reviews | Tests | Approves |
|-------------|-----------|---------|-------|---------|
| Characterization tests (Phase 1) | test-engineer | engineer | test-engineer | team-lead |
| `core/deployment_context.py` (Phase 2) | engineer | test-engineer | test-engineer | team-lead |
| CLI config path wire (Phase 3) | engineer | test-engineer | test-engineer | team-lead |
| CLI bug fix: agent + skill paths (Phase 4A) | engineer | test-engineer | test-engineer | team-lead |
| API singleton fix (Phase 4B) | engineer | test-engineer | test-engineer | team-lead |
| API mutation scope (Phase 5) | engineer | test-engineer | test-engineer | team-lead |
| API read-only scope (Phase 6) | engineer | test-engineer | test-engineer | team-lead |
| Code cleanup: retire resolvers (Phase 7) | refactoring-engineer | engineer | test-engineer | team-lead |
| Skills command `--scope` (Phase 7) | engineer | test-engineer | test-engineer | team-lead |
| Socket.IO events + dashboard doc (Phase 8) | engineer / documentation-agent | frontend-engineer | test-engineer | team-lead |
| E2E integration tests (Phase 9) | test-engineer | engineer | test-engineer | team-lead |

**Notes:**
- "Implements" = the agent type writing code
- "Reviews" = the agent type verifying correctness before marking done
- "Tests" = the agent type running `pytest` and checking coverage
- "Approves" = team-lead marks task complete in task list

---

## 6. Risk Register

### R-1: CLI `shutil.copy2` vs `AgentDeploymentService.deploy_agent()` (Behavior Masquerade)

**Source:** devils-advocate.md, Section 8, Risk 1
**Description:** The CLI's `_deploy_single_agent()` uses `shutil.copy2` (a direct file copy). If
Phase 4A accidentally switches to calling `AgentDeploymentService.deploy_agent()`, agents may be
rebuilt/templated, changing their content. This is a behavior change masked as a refactor.
**Severity:** High
**Phase:** 4A
**Mitigation:** Phase 4A only changes the **target directory** computed from `self._ctx.agents_dir`.
The copy mechanism (`shutil.copy2`) remains unchanged. Do not alter the copy call itself.
Characterization tests (Phase 1) confirm the copy mechanism is preserved.
**Status:** Mitigated by plan design.

### R-2: Singleton Trap Causes Silent Wrong-Scope Reads

**Source:** api-path-plan.md Phase 2; devils-advocate.md, Section 6
**Description:** If scope is added to API endpoints (Phase 5) before the singleton is fixed
(Phase 4B), user-scope GET requests silently read from the project-scope `AgentManager`.
**Severity:** Critical
**Phase:** 4B (fix must precede Phase 5)
**Mitigation:** Phase ordering enforces 4B before 5. Phase 4B tests TC-3-18 and TC-3-19 confirm
the singleton is gone before any scope parameter is threaded.
**Status:** Mitigated by phase ordering.

### R-3: Backward Compatibility — `scope: null` or `scope: ""`

**Source:** devils-advocate.md, Section 8, Risk 2
**Description:** Adding scope to request schema validation means `scope: null` or `scope: ""`
triggers a new HTTP 400 that didn't exist before. Existing dashboard clients send no scope field,
but malformed clients sending `null` would newly break.
**Severity:** Medium
**Phase:** 5
**Mitigation:** Parse scope as `body.get("scope", "project") or "project"` — coerces null to
default. Only explicit non-empty invalid strings get 400. Document this in API changelog.
**Status:** Mitigated in implementation detail.

### R-4: `_get_config_path()` Change for User-Scope — Missing File

**Source:** devils-advocate.md, Section 8, Risk 3
**Description:** `~/.claude-mpm/configuration.yaml` does not exist on first user-scope request.
The existing code calls `_load_config()` which already handles missing files (returns `{}`). The
write path must call `config_path.parent.mkdir(parents=True, exist_ok=True)` before writing.
**Severity:** High (would cause first-run failure without mitigation)
**Phase:** 5
**Mitigation:** Verify `_load_config()` handles missing file. Add `mkdir(parents=True)` before
every write to `ctx.configuration_yaml`. Integration test TC-4-14 (user-scope skill deploy E2E)
confirms this works on a fresh empty home dir.
**Status:** Mitigated by explicit code change + test.

### R-5: `DeploymentVerifier` Initialized at Module Load with Hardcoded Project Path

**Source:** devils-advocate.md, Section 8, Risk 4
**Description:** `deployment_verifier.py` captures `default_agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` at module import time. Even with `DeploymentContext` providing the correct user-scope path to the handler, `DeploymentVerifier` would verify the wrong directory unless `agents_dir` is passed explicitly.
**Severity:** High
**Phase:** 4B
**Mitigation:** Phase 4B Tasks 4B.3 and 4B.4 make all `verifier.verify_*()` calls explicitly
pass `agents_dir` or `skills_dir`. The default is never used.
**Status:** Mitigated by Phase 4B design.

### R-6: Cross-Scope Isolation — Deploy Bleeds into Wrong Scope

**Source:** test-plan.md, Phase 4-B
**Description:** A bug in path resolution could cause a user-scope deploy to write files into the
project directory (or vice versa).
**Severity:** High (data integrity)
**Phase:** 9 (E2E verification)
**Mitigation:** TC-4-07 and TC-4-08 specifically test that deploying to one scope does not affect
the other. These are E2E tests with real filesystem (no path mocking).
**Status:** Detected by Phase 9 tests.

### R-7: Circular Import in `core/__init__.py`

**Source:** cli-path-plan.md Phase 2 risk
**Description:** Adding `DeploymentContext` to `core/__init__.py` could create a circular import
if `deployment_context.py` imports from modules that in turn import from `core`.
**Severity:** Medium (would break all imports)
**Phase:** 2
**Mitigation:** Use lazy import pattern in `__init__.py` if circular import detected:
```python
def __getattr__(name):
    if name == "DeploymentContext":
        from .deployment_context import DeploymentContext
        return DeploymentContext
```
**Status:** Contingency plan ready.

### R-8: YAGNI — API Scope Has No Dashboard UI Yet

**Source:** devils-advocate.md, Section 4
**Description:** The dashboard currently has zero scope UI. The devil's advocate argues threading
scope through 14 API endpoints is premature without a confirmed dashboard requirement.
**Severity:** Low (risk of wasted effort, not data corruption)
**Resolution:** The team has decided to proceed with Strategy 1 (API scope support). The
dashboard integration document (Phase 8) specifically includes a `SCOPE_SELECTOR: false` feature
flag so the backend changes ship without exposing scope UI prematurely. The API changes are
additive — clients without scope still work identically.
**Status:** Acknowledged; mitigated by feature flag strategy.

### R-9: Test Coverage Decrease at Any Phase

**Source:** Plan constraint (coverage must never decrease)
**Description:** Any phase that modifies production code without adding corresponding tests could
leave gaps.
**Severity:** Medium
**Mitigation:** Each phase's "Milestone" section specifies the exact tests that must pass.
Pre-condition checks at each phase: `pytest --cov=claude_mpm --cov-fail-under=<current_threshold>`.
The characterization tests in Phase 1 establish the baseline; subsequent phases only add tests.
**Status:** Enforced by phase milestone criteria.

---

## 7. Definition of Done

The entire scope abstraction effort is **complete** when ALL of the following are true:

### CLI

- [x] `claude-mpm configure --scope user` deploys agent `.md` files to `~/.claude/agents/`
- [x] `claude-mpm configure --scope user` deploys skill directories to `~/.claude/skills/`
- [x] `claude-mpm configure --scope project` (or no scope) behavior is identical to pre-change
- [x] `claude-mpm skills deploy <name> --scope user` deploys to `~/.claude/skills/<name>/`
- [x] `claude-mpm skills deploy <name>` behavior is identical to pre-change
- [x] `configure_paths.py` is deleted from the codebase
- [x] `core/shared/path_resolver.py` is deleted from the codebase
- [x] `core/config_scope.py` is the sole canonical path resolver
- [x] `self._ctx` (`DeploymentContext`) is initialized in `ConfigureCommand.__init__()` and
      recreated in `_switch_scope()`

### API

- [x] All 6 mutation endpoints accept optional `scope` defaulting to `"project"` — HTTP 200/201
- [x] All 6 read endpoints accept optional `?scope=` query param defaulting to `"project"`
- [x] `scope: "user"` routes operations to `~/.claude/agents/` or `~/.claude/skills/`
- [x] `scope: "invalid"` returns HTTP 400 `VALIDATION_ERROR`
- [x] No singleton trap: `_get_agent_manager("project")` and `_get_agent_manager("user")` return
      different `AgentManager` instances
- [x] All `config_event` Socket.IO emissions include `data.scope`
- [x] Autoconfig endpoints explicitly reject user scope with HTTP 400 `SCOPE_NOT_SUPPORTED`
- [x] `BackupManager` has a TODO comment acknowledging project-scope-only backup limitation
- [x] Dashboard integration document exists at
      `docs-local/agent_skill_scope_selection/plans/dashboard-integration-notes.md`

### Shared

- [x] `src/claude_mpm/core/deployment_context.py` exists (~65 lines)
- [x] `DeploymentContext.from_string("project")`, `.from_user()`, `.from_request_scope()` all work
- [x] `DeploymentContext` is frozen (immutable) — `ctx.scope = X` raises `FrozenInstanceError`
- [x] `DeploymentContext` is hashable (usable as dict key)

### Tests

- [x] All 16 characterization tests pass on the pre-change codebase (Phase 1)
- [x] All 23 `test_deployment_context.py` unit tests pass (Phase 2)
- [x] All 17 CLI scope behavior tests pass (Phase 4A)
- [x] All 2 singleton scoping tests pass (Phase 4B)
- [x] All 23 API scope parameter tests pass (Phase 5 + 6)
- [x] All 5 skills scope tests pass (Phase 7)
- [x] All 16 E2E integration tests pass (Phase 9)
- [x] Total new tests: ~100 (≥96 by file count above)
- [x] Test coverage % is equal to or higher than before Phase 1

### Out of Scope (do NOT implement)

- Archive feature removal (`unused/` directory handling)
- Dashboard scope selector UI (deferred to a separate frontend ticket)
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
| `src/claude_mpm/services/monitor/config_routes.py` | Modified | 4B, 6 | +45 |
| `src/claude_mpm/services/config_api/agent_deployment_handler.py` | Modified | 4B, 5, 8 | +55 |
| `src/claude_mpm/services/config_api/skill_deployment_handler.py` | Modified | 4B, 5, 8 | +55 |
| `src/claude_mpm/services/config_api/autoconfig_handler.py` | Modified | 5 | +10 |
| `src/claude_mpm/services/config_api/backup_manager.py` | Modified (comment only) | 5 | +5 |

### Test Files

| File | Action | Phase | Test Count |
|------|--------|-------|-----------|
| `tests/conftest.py` | Modified (fixtures added) | 1 | — |
| `tests/cli/commands/test_configure_unit.py` | Modified (tests added) | 1 | +6 |
| `tests/cli/commands/test_skills_cli.py` | Modified | 1 | +1 |
| `tests/cli/commands/test_configure_scope_characterization.py` | **NEW** | 1 | 12 |
| `tests/services/config_api/test_scope_characterization.py` | **NEW** | 1 | 4 |
| `tests/integration/api/conftest.py` | **NEW** | 1 | — |
| `tests/core/test_scope_selector.py` | **NEW** | 1→2 | 7→12 |
| `tests/unit/core/test_deployment_context.py` | **NEW** | 2 | 23 |
| `tests/cli/commands/test_configure_scope_behavior.py` | **NEW** | 4A | 17 |
| `tests/unit/services/monitor/test_agent_manager_scoping.py` | **NEW** | 4B | 2 |
| `tests/services/config_api/test_agent_deployment_scope.py` | **NEW** | 5 | 8 |
| `tests/services/config_api/test_skill_deployment_scope.py` | **NEW** | 5 | 5 |
| `tests/services/config_api/test_config_routes_scope.py` | **NEW** | 5+6 | 6 |
| `tests/services/config_api/test_autoconfig_scope.py` | **NEW** | 5 | 4 |
| `tests/cli/commands/test_skills_scope.py` | **NEW** | 7 | 5 |
| `tests/e2e/test_scope_deployment_e2e.py` | **NEW** | 9 | 16 |

### Documentation Files

| File | Action | Phase |
|------|--------|-------|
| `docs-local/agent_skill_scope_selection/plans/dashboard-integration-notes.md` | **NEW** | 8 |

---

*Total estimated implementation time: 9 phases, independently mergeable, each ~1–3 hours of
focused engineering. Critical path: Phase 1 → 2 → 3 → 4A+4B → 5 → 6 → 7 → 8 → 9.*
