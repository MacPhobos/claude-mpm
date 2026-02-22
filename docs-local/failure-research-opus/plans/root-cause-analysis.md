# Root Cause Analysis: Top 5 Test Failure Categories

**Date**: 2026-02-22
**Analyst**: root-cause-analyst
**Scope**: 1,587 failures across 5 categories (of 1,726 total across 7,330 tests)

---

## Executive Summary

The 1,587 failures decompose into three root cause classes:

| Root Cause Class | Estimated Failures | % of Total |
|---|---|---|
| **Test quality issues** (badly written tests) | ~900-1,000 | ~57-63% |
| **Intentional API changes** (tests not updated) | ~350-400 | ~22-25% |
| **Source code bugs** (actual defects) | ~150-200 | ~10-13% |

The single largest root cause is **LLM-generated tests with systematic errors** (~600+ failures from `self/path` confusion, `tmp_path` misuse, and calling SUT methods via `self`). The second largest is **API changes with no test updates** (~350 from template migration, enum consolidation, variable renames).

---

## Category 1: Fixtures and Setup (277 failures)

### 1.1 `tmp_path` as context manager (153 failures)

**Root Cause: TEST QUALITY ISSUE**

Tests use `with tmp_path as tmpdir:` treating pytest's `tmp_path` fixture as a context manager. `tmp_path` is a fixture injected by pytest as a function parameter, not `tempfile.TemporaryDirectory()`.

**Evidence:**
- `tests/integration/agents/test_agent_deployment.py:87`: `with tmp_path as tmpdir:` in a standalone function that doesn't receive `tmp_path` as a parameter
- `tests/test_agent_template_builder.py:35`: Same pattern inside a fixture that doesn't receive `tmp_path`
- **111 occurrences across 38 files** (confirmed via grep)

**Pattern**: Tests appear to have been LLM-generated, confusing:
```python
# WRONG (what tests do):
with tmp_path as tmpdir:   # tmp_path is not defined in scope

# CORRECT option A (pytest fixture):
def test_something(self, tmp_path):
    tmpdir = tmp_path  # tmp_path is already a Path

# CORRECT option B (stdlib):
with tempfile.TemporaryDirectory() as tmpdir:
    ...
```

**Affected files (sample)**: `test_agent_deployment.py`, `test_agent_deployment_fix.py`, `test_agent_exclusion.py`, `test_comprehensive_agent_exclusion.py`, `test_agent_template_builder.py`, `test_agent_management.py`, `test_memory_deduplication.py`, `test_error_handling.py`, +30 more

---

### 1.2 UnifiedPathManager missing `CONFIG_DIR` (52 failures)

**Root Cause: SOURCE CODE BUG**

`get_path_manager().CONFIG_DIR` is referenced in **8 source files** but `UnifiedPathManager` only defines `CONFIG_DIR_NAME = ".claude-mpm"` — there is no `CONFIG_DIR` attribute or property.

**Evidence:**
- `src/claude_mpm/core/unified_paths.py:302`: Defines `CONFIG_DIR_NAME = ".claude-mpm"` (NO `CONFIG_DIR`)
- `src/claude_mpm/services/version_control/branch_strategy.py:313`: Uses `get_path_manager().CONFIG_DIR`
- `src/claude_mpm/config/agent_config.py:242,261`: Uses `get_path_manager().CONFIG_DIR`
- `src/claude_mpm/services/agents/management/agent_management_service.py:68`: Uses `get_path_manager().CONFIG_DIR`
- `src/claude_mpm/services/agents/loading/framework_agent_loader.py:70,91`: Uses `get_path_manager().CONFIG_DIR`
- `src/claude_mpm/agents/async_agent_loader.py:113`: Uses `get_path_manager().CONFIG_DIR`
- `src/claude_mpm/services/agents/registry/modification_tracker.py:640`: Uses `get_path_manager().CONFIG_DIR`

**Likely history**: The attribute was probably called `CONFIG_DIR` in an earlier path manager implementation and was renamed to `CONFIG_DIR_NAME` during the unified path refactoring, but 8 call sites were not updated.

**Fix**: Add `CONFIG_DIR = CONFIG_DIR_NAME` alias to `UnifiedPathManager`, OR change all 8 call sites to use `CONFIG_DIR_NAME` or `get_config_dir()`.

---

### 1.3 `Config` not defined (22 failures)

**Root Cause: TEST QUALITY ISSUE (missing import)**

`tests/test_memory_fixes_verification.py:56` uses `self.config = Config()` in `setup_method` but `Config` is never imported in the file.

**Evidence:**
- File imports: `HookContext`, `HookType`, `MemoryPostDelegationHook`, `MemoryPreDelegationHook`, `AgentMemoryManager` — no `Config`
- Also note: `test_pm_memory_persistence_to_user_directory` at line 63 is missing `self` parameter

---

### 1.4 Missing test file references (10 failures)

**Root Cause: TEST QUALITY ISSUE (stale reference)**

`tests/hooks/claude_hooks/test_pre_split_verification.py` references `tests/hooks/claude_hooks/test_hook_handler_comprehensive.py` which no longer exists (likely split in a prior refactoring).

---

## Category 2: File and Filesystem (103 failures)

### 2.1 Missing JSON template files (78 failures)

**Root Cause: INTENTIONAL API CHANGE (tests not updated)**

Commit `831be541` (2025-12-01) deliberately removed `mpm-skills-manager.json` and `mpm-agent-manager.json` from `src/claude_mpm/agents/templates/`. The commit message states:

> "These agents now exist in bobmatnyc/claude-mpm-agents Git repository. JSON templates are deprecated in favor of Git cache workflow."

Tests at `tests/agents/test_mpm_skills_manager.py` still open the deleted files.

**Evidence:**
- `git show 831be541`: Deletes `mpm-agent-manager.json` (110 lines) and `mpm-skills-manager.json` (114 lines)
- `src/claude_mpm/agents/templates/`: Now contains only `.md` files, `README.md`, and `__init__.py` — zero JSON files
- Tests reference: `/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/agents/templates/mpm-skills-manager.json`

**Fix**: Delete or rewrite tests to use the new Git-cached markdown agent format.

---

### 2.2 Missing parent directories in temp paths (12 failures)

**Root Cause: TEST QUALITY ISSUE**

Tests create file paths like `tmp_path / "templates" / "corrupted_agent.json"` but don't create intermediate directories before writing.

**Evidence:**
- `tests/test_agent_deployment_comprehensive.py:384`: `corrupted_template.write_text(...)` fails because `templates/` subdirectory doesn't exist
- `tests/test_agent_deployment_system.py:51`: Same pattern — writes to `templates/test_agent.json` without creating `templates/`

**Fix**: Add `template_file.parent.mkdir(parents=True, exist_ok=True)` before writes.

---

### 2.3 gitdb pack fixtures (3 failures) + OSError (2 failures) + Other (8 failures)

**Root Cause: TEST QUALITY ISSUES**

- `tests/test_pack.py`: Tests third-party library internals (gitdb pack files) that aren't installed
- `tests/unit/services/cli/test_session_resume_helper.py`: Uses `rmdir()` on non-empty directory, should use `shutil.rmtree()`

---

## Category 3: Attribute Errors (448 failures)

### 3.1 `module 'claude_mpm' has no attribute 'mcp'` (42 failures)

**Root Cause: SOURCE CODE BUG**

The custom `__getattr__` in `src/claude_mpm/__init__.py:42-57` implements lazy loading but only handles 3 names (`ClaudeRunner`, `MPMOrchestrator`, `TicketManager`). For all other names, it raises `AttributeError`. This blocks submodule access via `getattr()`.

When `unittest.mock.patch("claude_mpm.mcp.session_manager.ClaudeMPMSubprocess")` resolves its target, Python's `pkgutil.resolve_name` calls `getattr(claude_mpm_module, 'mcp')`, which hits the custom `__getattr__` and raises `AttributeError`.

**Evidence:**
- `src/claude_mpm/__init__.py:57`: `raise AttributeError(f"module '{__name__}' has no attribute '{name}'")`
- `src/claude_mpm/mcp/` directory exists with `__init__.py`, `session_manager.py`, and 12 other modules
- Direct imports work (`from claude_mpm.mcp.session_manager import SessionManager`), but `getattr`-based resolution fails

**Introduced by**: Commit `e027d76e` ("perf: optimize hook handler initialization with lazy imports")

**Fix**: The `__getattr__` should fall through to allow Python's standard submodule resolution for subpackages:
```python
def __getattr__(name):
    if name == "ClaudeRunner": ...
    if name == "MPMOrchestrator": ...
    if name == "TicketManager": ...
    # Allow submodule access (e.g., claude_mpm.mcp)
    import importlib
    try:
        return importlib.import_module(f".{name}", __name__)
    except ImportError:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
```

---

### 3.2 HealthStatus missing `WARNING` and `CRITICAL` (15 failures)

**Root Cause: INTENTIONAL API CHANGE (tests not updated)**

Commit `7a84f920` (2025-10-26) consolidated `HealthStatus` enums. The commit message explicitly states:

> "Semantic mapping: WARNING -> DEGRADED, CRITICAL -> UNHEALTHY"

The enum now has: `HEALTHY`, `UNHEALTHY`, `DEGRADED`, `UNKNOWN`, `CHECKING` — no `WARNING` or `CRITICAL`.

**Evidence:**
- `src/claude_mpm/core/enums.py:236-249`: Current enum members
- `tests/services/test_monitoring_refactored.py:56`: `HealthStatus.WARNING` — member doesn't exist
- Commit `7a84f920` shows 16 files updated but test files were not

**Fix**: Replace `HealthStatus.WARNING` -> `HealthStatus.DEGRADED` and `HealthStatus.CRITICAL` -> `HealthStatus.UNHEALTHY` in tests.

---

### 3.3 `PID_FILE` renamed to `DEFAULT_PID_FILE` (10 failures)

**Root Cause: INTENTIONAL API CHANGE (tests not updated)**

`src/claude_mpm/scripts/socketio_daemon.py:27` defines `DEFAULT_PID_FILE` but tests try to patch `PID_FILE`.

**Evidence:**
- Source: `DEFAULT_PID_FILE = Path.home() / ".claude-mpm" / "socketio-server.pid"`
- Test: `tests/test_socketio_daemon.py:50`: `with patch("claude_mpm.scripts.socketio_daemon.PID_FILE", ...)`

**Fix**: Update patch targets in tests to use `DEFAULT_PID_FILE`.

---

### 3.4 Test classes calling SUT methods via `self` (~80+ failures)

**Root Cause: TEST QUALITY ISSUE**

Multiple test classes call methods that belong to the System Under Test (SUT), not the test class, via `self`:
- `TestEventHandlerRegistry.test_initialize_default_handlers`: `self.initialize()` (9 failures)
- `TestAgentMetricsCollector`: `self.update_deployment_metrics()` (9 failures)
- `TestAgentConfigurationManager`: `self.get_agent_types()` (8 failures)
- `TestGitEventHandler`: `self.sio` (7 failures)
- `TestAdvancedHealthMonitor`: `self.get()` (6 failures)
- And many more across ~171 distinct subpatterns

**Evidence:**
- `tests/test_agent_metrics_collector.py:46`: `self.update_deployment_metrics(150.5, results)` — method is on `AgentMetricsCollector`, not on `TestAgentMetricsCollector`
- `tests/services/test_socketio_handlers.py:788`: `self.initialize()` — method is on `EventHandlerRegistry`, not on `TestEventHandlerRegistry`

**Pattern**: Tests were generated as if the test class IS the SUT, calling `self.method()` instead of `fixture.method()`.

---

### 3.5 Other attribute mismatches (~291 failures)

Various smaller patterns including:
- `ClaudeMPMPaths` property deleter issues (7 failures)
- Module-level attribute renames (`logger`, etc.) (6 failures)
- Missing `_validate_agent` methods (6 failures)
- Missing `_discover_agents` methods (5 failures)

Most are a mix of API changes and test quality issues.

---

## Category 4: Type Errors (425 failures)

### 4.1 `self / "filename"` path division (37+ failures across 7 files)

**Root Cause: TEST QUALITY ISSUE**

Tests use `self / "test_agent.md"` treating `self` (test class instance) as a `Path` object. This is the same systematic pattern as 3.4 — tests confuse the test instance with a directory path.

**Evidence:**
- `tests/test_frontmatter_format.py:34`: `agent_file = self / "test_agent.md"`
- `tests/test_instruction_synthesis.py:31`: `instructions_file = self / "INSTRUCTIONS.md"`
- `tests/test_schema_standardization.py:240`: `agent_path = self / "test_agent.json"`
- **45 occurrences across 7 files**

**Fix**: Replace `self /` with `tmp_path /` (using pytest's `tmp_path` fixture injected as a method parameter).

---

### 4.2 PosixPath not JSON serializable (5 failures)

**Root Cause: SOURCE CODE BUG**

`src/claude_mpm/hooks/claude_hooks/installer.py:824` calls `json.dump(settings, f, indent=2)` where `settings` contains `PosixPath` objects.

**Evidence:**
- Stack trace from `tests/test_hook_installer.py:587`: `self.installer._update_claude_settings(script_path)` -> `json.dump(settings, ...)` -> `TypeError: Object of type PosixPath is not JSON serializable`

**Fix**: Convert `PosixPath` to `str()` before JSON serialization in `installer.py:824`.

---

### 4.3 Remaining type errors (~383 failures)

**Root Cause: MIXED (382 distinct subpatterns)**

The extreme fragmentation (382 distinct patterns in 425 failures) indicates these are individual test-level issues, not a systemic root cause. Categories include:
- Mock objects returning wrong types (`MagicMock` not subscriptable, no `len()`, etc.)
- `NoneType` not subscriptable (functions returning None unexpectedly)
- Argument count mismatches (API signatures changed)

---

## Category 5: Assertion Failures (334 failures)

### 5.1 Count/value mismatches (33+ failures)

**Root Cause: INTENTIONAL API CHANGES (tests not updated)**

Multiple tests assert hardcoded counts that no longer match reality:
- Agent count: Expected 3, got 10 (more agents added)
- Deployment count: Expected 5, got 1 (deployment logic changed)
- Memory metrics: Expected 50.0, got 100.0 (calculation changed)
- Deployed files count: Expected specific, got different (file listing changed)

**Evidence:**
- `test_git_source_sync_service.py:435`: `assert len(agent_list) == 3` but got 10 (7 new agents added)
- `test_agent_selection_service.py:270`: `assert result["deployed_count"] == 5` but got 1
- `test_agent_memory_manager_comprehensive.py:689`: `assert 100.0 == 50.0`

---

### 5.2 Boolean/condition failures (10 failures)

**Root Cause: MIXED**

- `ci_mode_used` flag assertions: Agent infrastructure tests expect `True` but get `False`
- Async wait conditions timing out

---

### 5.3 Custom logging level (7 failures)

**Root Cause: CONFIGURATION CHANGE**

Root logger level is 51 (custom) instead of standard `INFO` (20) or `DEBUG` (10).

---

### 5.4 Remaining assertion failures (~284 failures)

**Root Cause: MIXED (239 distinct subpatterns)**

Similar to type errors, the high fragmentation indicates individual test issues rather than systemic causes.

---

## Cross-Cutting Patterns

### Pattern A: LLM-Generated Test Antipatterns (~600+ failures)

Three systematic errors appear across hundreds of tests, suggesting LLM generation without review:

| Antipattern | Occurrences | Files | Estimated Failures |
|---|---|---|---|
| `with tmp_path as tmpdir:` (not a context manager) | 111 | 38 | ~153 |
| `self / "filename"` (test class is not a Path) | 45 | 7 | ~37 |
| `self.sut_method()` (test class is not the SUT) | ~80+ | ~20+ | ~80+ |
| Missing imports (`Config`, etc.) | ~25 | ~5 | ~25 |

**Recommendation**: Establish a test writing standard and/or pre-commit check that flags these patterns.

### Pattern B: Source Changes Without Test Updates (~350 failures)

| Change | Commit | Failures |
|---|---|---|
| JSON templates removed | `831be541` (2025-12-01) | ~78 |
| HealthStatus enum consolidated | `7a84f920` (2025-10-26) | ~15 |
| PID_FILE renamed | Unknown | ~10 |
| Agent count/behavior changes | Multiple commits | ~50+ |
| Various API signature changes | Multiple commits | ~200+ |

**Recommendation**: Enforce test updates in PRs that change public APIs.

### Pattern C: Source Code Bugs (~150 failures)

| Bug | File | Failures |
|---|---|---|
| Missing `CONFIG_DIR` property | `unified_paths.py` | 52 |
| `__getattr__` blocks submodule access | `__init__.py` | 42 |
| PosixPath JSON serialization | `installer.py` | 5 |
| Other source bugs | Various | ~50 |

**Recommendation**: Fix these directly — they affect production code, not just tests.

---

## Priority Fix Order

1. **`__init__.py` `__getattr__` fix** (42 test failures + affects production `patch()` usage) — 1 line change
2. **`UnifiedPathManager.CONFIG_DIR` property** (52 test failures + affects 8 source files) — 1 line change
3. **`installer.py` PosixPath serialization** (5 test failures + production bug) — 1 line change
4. **Delete/rewrite template tests** (78 failures, templates intentionally removed)
5. **Bulk fix `with tmp_path` pattern** (153 failures, regex replace across 38 files)
6. **Bulk fix `self /` pattern** (37 failures, regex replace across 7 files)
7. **Update HealthStatus references** (15 failures, find-and-replace)
8. **Update PID_FILE references** (10 failures, find-and-replace)
9. **Fix `self.method()` antipattern** (80+ failures, requires per-test rewrite)
10. **Address remaining assertion failures** (284 failures, per-test investigation needed)
