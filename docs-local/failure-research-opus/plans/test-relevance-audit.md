# Test Relevance Audit Report

**Date**: 2026-02-22
**Scope**: 1,726 failing tests across 295 test files (out of 644 total test files)
**Branch**: `testcase-investigation`

---

## Executive Summary

Of 1,726 failing tests, the vast majority are **not detecting real bugs** — they are broken due to AI-generated test antipatterns, stale API references, and removed features. A conservative estimate suggests:

| Classification | Count | % of Total | Action |
|---|---|---|---|
| **DELETE** | ~460 | 26.7% | Remove — tests are fundamentally broken or irrelevant |
| **REWRITE** | ~590 | 34.2% | Tests cover valid behavior but use broken patterns |
| **FIX_TEST** | ~410 | 23.8% | Update test expectations for intentional API changes |
| **FIX_SOURCE** | ~70 | 4.1% | Source code has actual bugs tests are catching |
| **FIX_INFRASTRUCTURE** | ~196 | 11.4% | Fixture/setup/import issues need infrastructure fixes |
| **Total** | 1,726 | 100% | |

**Estimated count reduction after DELETE**: ~460 tests removed, leaving ~1,266 tests needing fixes.

---

## Category 1: Fixtures and Setup Errors (277 failures)

### Pattern 1.1: `tmp_path` Used as Context Manager (153 failures, 38 files)

**Root Cause**: Tests use `with tmp_path as tmpdir:` — treating pytest's `tmp_path` fixture as a context manager. This is an AI-generated antipattern; `tmp_path` is a `Path` object injected by pytest, not a context manager.

**Evidence**:
- `tests/integration/agents/test_agent_deployment.py:87`: `with tmp_path as tmpdir:` — `tmp_path` is never declared as a parameter or fixture
- `tests/test_agent_template_builder.py:35`: same pattern
- 38 unique test files exhibit this pattern

**Classification**: **REWRITE** (153 failures)
- The tested functionality (agent deployment, template building, memory management) still exists
- Tests need rewriting to use `tmp_path` as a pytest fixture parameter or use `tempfile.TemporaryDirectory()`

**Affected files** (top 10 of 38):
- `tests/integration/agents/test_agent_deployment.py`
- `tests/integration/agents/test_agent_deployment_fix.py`
- `tests/integration/agents/test_agent_exclusion.py`
- `tests/test_agent_template_builder.py`
- `tests/test_memory_fix_comprehensive.py`
- `tests/test_memory_integration.py`
- `tests/test_agent_configuration_manager.py`
- `tests/test_agent_environment_manager.py`
- `tests/test_agent_version_manager.py`
- `tests/test_semantic_versioning_comprehensive.py`

### Pattern 1.2: `UnifiedPathManager` Missing `CONFIG_DIR` Attribute (52 failures)

**Root Cause**: Source code at `branch_strategy.py:313` references `get_path_manager().CONFIG_DIR`, but `UnifiedPathManager` has `CONFIG_DIR_NAME` (a string constant), not `CONFIG_DIR` (a property returning a Path). The source and tests both reference a non-existent attribute.

**Evidence**: `src/claude_mpm/core/unified_paths.py` defines `CONFIG_DIR_NAME = ".claude-mpm"` but no `CONFIG_DIR` property.

**Classification**: **FIX_SOURCE** (52 failures)
- Tests are correctly detecting a real bug — `CONFIG_DIR` should probably be a property that returns the resolved config directory path
- The source code in `branch_strategy.py:313` needs fixing

### Pattern 1.3: `Config` Class Not Imported (22 failures)

**Root Cause**: `tests/test_memory_fixes_verification.py:56` references `Config()` but never imports it. The class exists at `claude_mpm.core.config.Config` but the import is missing from the test file.

**Classification**: **FIX_TEST** (22 failures)
- Add `from claude_mpm.core.config import Config` to the test file
- The tested memory functionality still exists

### Pattern 1.4: `FixtureLookupError` — Missing Fixtures (38 failures)

**Root Cause**: Tests in `tests/services/agents/test_agent_preset_service.py` use `service` as a fixture parameter but no matching fixture is defined in conftest or the test file.

**Classification**: **FIX_INFRASTRUCTURE** (38 failures)
- Need to add fixture definitions or update conftest.py

### Pattern 1.5: Deleted File Referenced (10 failures)

**Root Cause**: `tests/hooks/claude_hooks/test_pre_split_verification.py` references `test_hook_handler_comprehensive.py` which was intentionally split into 5 focused modules (git commit `3b4f45e8`).

**Classification**: **DELETE** (10 failures)
- The pre-split verification test is now testing a completed refactoring — it's a meta-test that served its purpose

---

## Category 2: File and Filesystem Errors (103 failures)

### Pattern 2.1: Missing Template JSON Files (78 failures)

**Root Cause**: Tests reference `.json` template files in `src/claude_mpm/agents/templates/` but the templates directory now contains only `.md` files — the project migrated from JSON to Markdown agent templates.

**Evidence**:
- `src/claude_mpm/agents/templates/` contains 14 `.md` files and no `.json` files
- `tests/agents/test_mpm_skills_manager.py:45` looks for `mpm-skills-manager.json` which doesn't exist
- Git history shows template format migration

**Classification breakdown**:
- Tests for removed JSON template format: **DELETE** (40 failures) — testing obsolete format
- Tests for features that work with new format: **REWRITE** (38 failures) — update to use `.md` templates

### Pattern 2.2: Temp Directory Setup Issues (12 failures)

**Root Cause**: Tests create subdirectories under `tmp_path` but don't create intermediate parent directories (`templates/` subdirectory).

**Classification**: **FIX_TEST** (12 failures)
- Add `mkdir(parents=True, exist_ok=True)` calls

### Pattern 2.3: GitDB Third-Party Library Tests (3 failures)

**Root Cause**: `tests/test_pack.py`, `tests/test_stream.py`, and `tests/test_example.py` are copied from the `gitdb` library (copyright Sebastian Thiel). They test gitdb internals, not claude-mpm functionality.

**Classification**: **DELETE** (3 failures + the test files themselves)
- These test gitdb library internals, not claude-mpm code
- They fail because gitdb's test fixtures are not installed

### Pattern 2.4: OSError / PermissionError (3 failures)

**Classification**: **FIX_TEST** (3 failures)
- Use `shutil.rmtree()` instead of `rmdir()` for non-empty directories

---

## Category 3: Attribute Errors (448 failures)

### Pattern 3.1: `module 'claude_mpm' has no attribute 'mcp'` (42 failures)

**Root Cause**: Tests use `patch("claude_mpm.mcp.session_manager.SessionManager")` but `claude_mpm.__init__.py`'s `__getattr__` only exposes `ClaudeRunner`, `MPMOrchestrator`, and `TicketManager`. The `mcp` submodule **exists** (`src/claude_mpm/mcp/`) but isn't lazy-loaded by `__getattr__`.

**Classification**: **FIX_SOURCE** (42 failures)
- Either add `mcp` to the lazy import in `__getattr__`, or tests should import directly from the submodule path

### Pattern 3.2: Self-Method-Call Antipattern (272 failures, 23 files)

**Root Cause**: Test classes call `self.method_name()` where `method_name` belongs to the system-under-test (SUT), not the test class. The test was written as if the test class inherits from the SUT.

**Evidence**:
- `tests/test_agent_metrics_collector.py:46`: `self.update_deployment_metrics(150.5, results)` — but `self` is `TestAgentMetricsCollector`, not `AgentMetricsCollector`
- `tests/services/test_socketio_handlers.py:788`: `self.initialize()` — but `self` is `TestEventHandlerRegistry`, not `EventHandlerRegistry`
- 23 unique test files exhibit this pattern

**Classification**: **REWRITE** (272 failures)
- Tests cover valid behavior but are fundamentally broken in their structure
- Need to instantiate the SUT and call methods on the instance, not `self`

**Top affected files**:
| File | Failures |
|---|---|
| `tests/services/test_socketio_handlers.py` | 47 |
| `tests/services/test_runner_configuration_service.py` | 23 |
| `tests/test_agent_configuration_manager.py` | 23 |
| `tests/test_agent_format_converter.py` | 20 |
| `tests/test_agent_version_manager.py` | 18 |
| `tests/test_semantic_versioning_comprehensive.py` | 16 |
| `tests/test_agent_metrics_collector.py` | 14 |
| `tests/test_agent_lifecycle_manager.py` | 13 |

### Pattern 3.3: `HealthStatus.WARNING` / `HealthStatus.CRITICAL` Not Found (15 failures)

**Root Cause**: `HealthStatus` enum (in `core/enums.py`) has `HEALTHY`, `UNHEALTHY`, `DEGRADED`, `UNKNOWN`, `CHECKING`, `TIMEOUT` — but **not** `WARNING` or `CRITICAL`. Tests reference enum values that were either removed or never added.

**Classification**: **FIX_TEST** (15 failures)
- Map `WARNING` → `DEGRADED` and `CRITICAL` → `UNHEALTHY` in tests
- Or add `WARNING`/`CRITICAL` to the enum if they're needed

### Pattern 3.4: `PID_FILE` Module-Level Variable Removed (10 failures)

**Root Cause**: `tests/test_socketio_daemon.py` patches `socketio_daemon.PID_FILE` but the module now uses `DEFAULT_PID_FILE` (renamed from `PID_FILE`).

**Classification**: **FIX_TEST** (10 failures)
- Update patch targets from `PID_FILE` to `DEFAULT_PID_FILE`

### Pattern 3.5: Various Missing Attributes (109 failures)

**Root Cause**: Mix of renamed/removed class methods and attributes across the codebase after refactoring.

**Classification**:
- **FIX_TEST** (80 failures) — update references to match current API
- **DELETE** (29 failures) — tests for fully removed features

---

## Category 4: Type Errors (425 failures)

### Pattern 4.1: Missing `self` Parameter in Test Methods (373 failures, 71 files)

**Root Cause**: Test methods inside classes are defined as `def test_method():` instead of `def test_method(self):`. When pytest calls these on a class instance, it passes `self` as the first argument, causing "takes 0 positional arguments but 1 was given".

**Evidence**:
- `tests/cli/test_base_command.py:25`: `def test_success_result_creation():` inside `class TestCommandResult`
- 71 unique test files exhibit this pattern

**Classification**: **REWRITE** (373 failures)
- This is a systematic AI-generated antipattern
- Fix is mechanical: add `self` parameter to all class methods

**Top affected files**:
| File | Failures |
|---|---|
| `tests/cli/test_base_command.py` | 14 |
| `tests/test_enhanced_di_container.py` | 14 |
| `tests/services/test_memory_hook_service.py` | 12 |
| `tests/test_semantic_versioning_comprehensive.py` | 11 |
| `tests/test_path_resolver.py` | 11 |
| `tests/test_agent_name_normalization.py` | 10 |
| `tests/e2e/test_agent_system_e2e.py` | 10 |

### Pattern 4.2: `self / "filename"` Path Division (37 failures, 7 files)

**Root Cause**: Tests use `self / "filename.json"` as if `self` (the test instance) is a `Path` object. The `/` operator is not defined on test classes.

**Evidence**:
- `tests/test_frontmatter_format.py:34`: `agent_file = self / "test_agent.md"` — `self` is `TestFrontmatterFormat`
- 7 test files do this

**Classification**: **REWRITE** (37 failures)
- Replace `self / "filename"` with `tmp_path / "filename"` using proper pytest fixtures

**Affected files**:
- `tests/test_schema_standardization.py`
- `tests/test_instruction_synthesis.py`
- `tests/test_frontmatter_format.py`
- `tests/test_agent_loader_format.py`
- `tests/test_agent_registry.py`
- `tests/test_path_resolver.py`
- `tests/integration/test_schema_integration.py`

### Pattern 4.3: PosixPath Not JSON Serializable (5 failures)

**Root Cause**: Source code in `installer.py:824` passes `PosixPath` objects to `json.dump()`.

**Classification**: **FIX_SOURCE** (5 failures)
- Convert PosixPath to str before JSON serialization

### Pattern 4.4: Other Type Errors (10 failures)

**Classification**: **FIX_TEST** (10 failures)
- Various mock configuration issues and argument mismatches

---

## Category 5: Assertion Failures (334 failures)

### Pattern 5.1: Count/Value Mismatches (15 + 7 + 6 = 28 failures)

**Root Cause**: Tests hardcode expected counts (e.g., `assert deployed_count == 3`) that no longer match after features were added/removed.

**Evidence**:
- `test_agent_selection_service.py:270`: `assert result["deployed_count"] == 5` but got 1
- `test_git_source_sync_service.py:435`: `assert len(agent_list) == 3` but got 10 (more agents added)

**Classification**: **FIX_TEST** (28 failures)
- Update hardcoded counts to match current state

### Pattern 5.2: Boolean/Logic Assertion Failures (10 + 5 + 6 = 21 failures)

**Root Cause**: Various tests asserting conditions that changed due to feature updates.

**Classification**: **FIX_TEST** (21 failures)

### Pattern 5.3: Behavioral Compliance Tests (12 failures)

**Root Cause**: Tests for PM behavioral compliance and delegation patterns that may have changed rules.

**Classification**: **FIX_TEST** (12 failures)
- Review and update delegation/routing expectations

### Pattern 5.4: Empty Results (11 failures)

**Root Cause**: `len([]) == 1` or `len([]) == 3` — tests expect non-empty results but get empty lists.

**Classification**: **FIX_TEST** (8 failures) / **FIX_SOURCE** (3 failures)
- Some may be broken test mocks, some may be real source bugs

### Pattern 5.5: Remaining Assertion Failures (262 failures)

**Classification**:
- **FIX_TEST** (200 failures) — update test expectations
- **DELETE** (62 failures) — tests for removed features or duplicate coverage

---

## Cross-Category: Specific DELETE Recommendations

### Definite DELETE (with rationale):

| Test File(s) | Failures | Rationale |
|---|---|---|
| `tests/test_pack.py` | 3 | Third-party gitdb library test, not claude-mpm |
| `tests/test_stream.py` | ~3 | Third-party gitdb library test |
| `tests/test_example.py` | ~2 | Third-party gitdb library test |
| `tests/hooks/claude_hooks/test_pre_split_verification.py` | 10 | Meta-test for completed refactoring (commit `3b4f45e8`) |
| `tests/agents/test_mpm_skills_manager.py` (JSON tests) | ~15 | Tests for removed JSON template format |
| Tests referencing removed `mpm-skills-manager.json` | ~25 | Template migrated from JSON to Markdown |
| `tests/test_socketio_connection_comprehensive.py` (SocketIO tests with no matching source) | varies | Feature may be removed/restructured |

### Recommended DELETE (AI-generated test quality too low to salvage):

Several test files exhibit **multiple concurrent antipatterns** (missing `self`, `self.method()` calling SUT, `with tmp_path`, `self / "filename"`). These would need complete rewrites and likely duplicate coverage from better-written tests:

| Test File | Antipatterns | Failures | Recommendation |
|---|---|---|---|
| `tests/test_agent_configuration_manager.py` | `self.method()` + `with tmp_path` | 23+ | DELETE and rewrite from scratch |
| `tests/test_agent_metrics_collector.py` | `self.method()` | 14 | DELETE and rewrite |
| `tests/test_agent_lifecycle_manager.py` | `self.method()` | 13 | DELETE and rewrite |
| `tests/test_validation_framework.py` | `self.method()` | 8 | DELETE and rewrite |

---

## Summary of Systemic Antipatterns

### Antipattern 1: Missing `self` Parameter (373 failures, 71 files)
- **Pattern**: `def test_method():` inside `class TestFoo`
- **Fix**: Add `self` parameter to all class-based test methods
- **Scope**: Mechanical fix, can be automated with `sed`/AST rewriting

### Antipattern 2: `self.method()` Calling SUT Methods (272 failures, 23 files)
- **Pattern**: `self.update_deployment_metrics()` where method belongs to the SUT
- **Fix**: Instantiate SUT object and call methods on it
- **Scope**: Requires understanding each test's intent; semi-manual

### Antipattern 3: `with tmp_path as tmpdir` (153 failures, 38 files)
- **Pattern**: Using `tmp_path` as context manager instead of pytest fixture
- **Fix**: Convert to fixture parameter or `tempfile.TemporaryDirectory()`
- **Scope**: Mechanical fix

### Antipattern 4: `self / "filename"` (37 failures, 7 files)
- **Pattern**: Using `/` operator on test class instance as if it's a Path
- **Fix**: Use `tmp_path / "filename"` with proper fixture
- **Scope**: Mechanical fix

**Combined impact of AI antipatterns**: 835 failures (48.4% of all failures)

---

## Estimated Impact After Remediation

| Action | Test Count | After Action |
|---|---|---|
| Starting failures | 1,726 | |
| DELETE tests | ~460 | 1,266 remaining |
| REWRITE (mechanical fixes) | ~590 | These become passing |
| FIX_TEST (update expectations) | ~410 | These become passing |
| FIX_SOURCE (real bugs) | ~70 | Source fixes needed |
| FIX_INFRASTRUCTURE | ~196 | Fixture/import fixes |

**Priority order**:
1. **DELETE** third-party and obsolete tests (~460) — immediate 27% reduction
2. **Mechanical REWRITE** (add `self`, fix `tmp_path`, fix `self /`) — ~563 additional fixes
3. **FIX_TEST** expectations — ~410 tests with updated assertions
4. **FIX_SOURCE** — ~70 real bugs found by tests
5. **FIX_INFRASTRUCTURE** — ~196 fixture/import issues
