# Implementation Plan: Test Failure Remediation

**Date**: 2026-02-22
**Total Failures**: 1,726 across 14 categories
**Branch**: `testcase-investigation`

## Executive Summary

Analysis of 1,726 test failures (of 7,330 total tests) reveals **10 cross-cutting root causes** that account for the vast majority of failures. These can be addressed in 4 phases, with Phase 1 alone targeting ~55% of all failures through infrastructure fixes that require no behavioral test changes.

### Root Cause Classification (from root-cause-analysis.md)

| Root Cause Class | Estimated Failures | % of Total |
|---|---|---|
| **Test quality issues** (LLM-generated tests with systematic errors) | ~900-1,000 | ~57-63% |
| **Intentional API changes** (tests not updated after code changes) | ~350-400 | ~22-25% |
| **Source code bugs** (actual defects in production code) | ~150-200 | ~10-13% |

**Key insight**: The single largest root cause is **LLM-generated tests with systematic errors** (~600+ failures from `self/path` confusion, `tmp_path` misuse, and calling SUT methods via `self`).

### Failure Distribution

| Category | Count | % of Total |
|---|---|---|
| attribute_errors | 448 | 26.0% |
| type_errors | 425 | 24.6% |
| assertion_failures | 334 | 19.4% |
| fixtures_and_setup | 277 | 16.0% |
| file_and_fs | 103 | 6.0% |
| unknown | 56 | 3.2% |
| db_and_migrations | 37 | 2.1% |
| imports_and_env | 13 | 0.8% |
| value_errors | 12 | 0.7% |
| timeouts | 7 | 0.4% |
| network_and_http | 6 | 0.3% |
| key_errors | 4 | 0.2% |
| runtime_errors | 3 | 0.2% |
| not_implemented | 1 | 0.1% |

### Cross-Cutting Root Causes (Ranked by Impact)

| # | Root Cause | Affected Tests | Categories |
|---|---|---|---|
| 1 | Missing `self` parameter in test class methods | ~379 | type_errors, db_and_migrations, timeouts |
| 2 | `tmp_path` used as context manager / undefined name | ~153 | fixtures_and_setup |
| 3 | `Config` class not imported in test files | ~61 | fixtures_and_setup, unknown |
| 4 | `UnifiedPathManager` missing `CONFIG_DIR` attribute | ~52 | fixtures_and_setup |
| 5 | `claude_mpm.__getattr__` blocks submodule patching | ~43 | attribute_errors, timeouts |
| 6 | `self / "filename"` path division on test instances | ~38 | type_errors |
| 7 | Missing JSON template files (migrated to .md) | ~78 | file_and_fs |
| 8 | API/attribute renames not reflected in tests | ~100+ | attribute_errors, assertion_failures |
| 9 | Missing modules/imports | ~13 | imports_and_env |
| 10 | PosixPath not JSON serializable (source bug) | ~5 | type_errors |

---

## Phase 1: Infrastructure Quick Wins

**Target**: Fix ~950 tests (~55% of total)
**Estimated Effort**: 2-3 days
**Dependencies**: None

### 1A. Fix Missing `self` Parameter in Test Class Methods (~379 tests)

**Root Cause**: Test methods in classes defined without `self` parameter. When pytest invokes the method on the class instance, it passes `self` as first positional argument, causing `takes 0 positional arguments but 1 was given`.

**Pattern**:
```python
# BROKEN:
class TestFoo:
    def test_something():  # missing self
        pass

# FIXED:
class TestFoo:
    def test_something(self):
        pass
```

**Files to modify** (identified from failure data):

| File | Test Class | Est. Methods |
|---|---|---|
| `tests/cli/test_base_command.py` | TestBaseCommand, TestCommandResult, TestServiceCommand, TestAgentCommand | ~20 |
| `tests/cli/test_shared_utilities.py` | TestCommonArguments, TestArgumentPatterns, TestOutputFormatter | ~15 |
| `tests/test_run_command_migration.py` | TestRunCommandMigration | ~8 |
| `tests/test_tickets_command_migration.py` | TestTicketsCommandMigration | ~8 |
| `tests/security/test_mcp_server_security.py` | TestMCPServerSecurity | ~1 |
| `tests/security/test_subprocess_security.py` | TestSubprocessSecurity | ~1 |
| `tests/test_health_monitoring_comprehensive.py` | TestCircuitBreaker | ~1 |
| `tests/test_socketio_startup_timing_fix.py` | TestSocketIOStartupTimingFix | ~1 |
| `tests/integration/test_schema_integration.py` | TestSchemaIntegration | ~1 |

**Plus ~300+ additional methods** across many test files (the type_errors category has 382 distinct subpatterns, most of which are this issue).

**Fix Strategy**: Automated script to find and fix:
```bash
# Find test methods in classes missing self
python3 -c "
import ast, sys, glob
for f in glob.glob('tests/**/*.py', recursive=True):
    try:
        tree = ast.parse(open(f).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name.startswith('test_'):
                            args = [a.arg for a in item.args.args]
                            if not args or args[0] != 'self':
                                print(f'{f}:{item.lineno}: {node.name}.{item.name}')
    except: pass
"
```

**Verification**:
```bash
pytest tests/cli/test_base_command.py -x --tb=short
pytest tests/cli/test_shared_utilities.py -x --tb=short
pytest tests/test_run_command_migration.py -x --tb=short
```

**Success Criteria**: All 379 `takes N positional arguments but N was given` errors eliminated.

---

### 1B. Fix `tmp_path` Misuse (~153 tests)

**Root Cause**: Tests use `tmp_path` as a context manager (`with tmp_path as tmpdir:`) or reference it as a bare name. `tmp_path` is a pytest fixture injected as a function parameter, not a context manager.

**Pattern**:
```python
# BROKEN (in test functions):
def test_something():
    with tmp_path as tmpdir:  # tmp_path is not defined here
        ...

# BROKEN (in fixture):
@pytest.fixture
def temp_dir():
    with tmp_path as temp_dir:  # tmp_path is not a context manager
        ...

# FIXED:
def test_something(tmp_path):
    tmpdir = tmp_path  # Just use it directly
    ...

# FIXED fixture:
@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path
```

**Files to modify** (20 files identified by grep):

| File | Est. Occurrences |
|---|---|
| `tests/test_semantic_versioning_comprehensive.py` | multiple |
| `tests/test_response_tracker_critical.py` | multiple |
| `tests/test_output_style_system.py` | multiple |
| `tests/test_output_style_enforcement.py` | multiple |
| `tests/test_memory_project_only.py` | multiple |
| `tests/test_memory_integration_e2e.py` | multiple |
| `tests/test_memory_integration.py` | multiple |
| `tests/test_memory_glob_pattern.py` | multiple |
| `tests/test_memory_filtering_fix.py` | multiple |
| `tests/test_memory_fix_comprehensive.py` | multiple |
| `tests/test_memory_deduplication.py` | multiple |
| `tests/test_mcp_install_config.py` | multiple |
| `tests/test_integration_with_agents.py` | multiple |
| `tests/test_enhanced_pid_validation.py` | multiple |
| `tests/test_error_handling.py` | multiple |
| `tests/test_deployment_manager_config.py` | multiple |
| `tests/test_config_v2_unit.py` | multiple |
| `tests/test_agent_registry_cache.py` | multiple |
| `tests/integration/agents/test_agent_deployment.py` | multiple |
| `tests/integration/agents/test_agent_deployment_fix.py` | multiple |

**Fix Strategy**: For each file:
1. If `tmp_path` is used in a fixture: add `tmp_path` as fixture parameter
2. If `with tmp_path as x:` pattern: replace with `x = tmp_path` (no context manager)
3. If `tmp_path` referenced in test function: add `tmp_path` as function parameter

**Verification**:
```bash
pytest tests/integration/agents/test_agent_deployment.py -x --tb=short
pytest tests/test_agent_registry_cache.py -x --tb=short
pytest tests/test_memory_integration.py -x --tb=short
```

**Success Criteria**: All 153 `NameError: name 'tmp_path' is not defined` errors eliminated.

---

### 1C. Fix `Config` Class Not Imported (~61 tests)

**Root Cause**: Tests reference `Config()` without importing it. The class exists at `claude_mpm.core.config.Config` (confirmed via grep). Some test files had imports that were removed or never added.

**Pattern**:
```python
# BROKEN:
class TestSomething:
    def setup_method(self):
        self.config = Config()  # NameError!

# FIXED:
from claude_mpm.core.config import Config

class TestSomething:
    def setup_method(self):
        self.config = Config()
```

**Files to modify** (from unknown + fixtures_and_setup categories):

| File | Count |
|---|---|
| `tests/test_memory_fixes_verification.py` | 22 (all tests share setup_method) |
| `tests/integration/infrastructure/test_activity_logging.py` | ~5 |
| `tests/integration/infrastructure/test_response_logging.py` | ~5 |
| `tests/integration/infrastructure/test_response_logging_debug.py` | ~5 |
| `tests/integration/infrastructure/test_response_logging_edge_cases.py` | ~5 |
| `tests/test_config_duplicate_comprehensive.py` | ~3 |
| `tests/test_config_duplicate_fix.py` | ~3 |
| `tests/test_config_duplicate_logging.py` | ~3 |
| Plus ~10 additional files | ~10 |

**Fix Strategy**: Add `from claude_mpm.core.config import Config` to each affected file's imports.

**Verification**:
```bash
pytest tests/test_memory_fixes_verification.py -x --tb=short
pytest tests/integration/infrastructure/ -x --tb=short
```

**Success Criteria**: All 61 `NameError: name 'Config' is not defined` errors eliminated.

---

### 1D. Fix `UnifiedPathManager.CONFIG_DIR` Missing Attribute (~52 tests)

**Root Cause**: Source code at `src/claude_mpm/services/version_control/branch_strategy.py:313` and `src/claude_mpm/services/agents/loading/framework_agent_loader.py:70` access `get_path_manager().CONFIG_DIR`, but `UnifiedPathManager` only defines `CONFIG_DIR_NAME = ".claude-mpm"` (a class attribute with a different name).

**Pattern**:
```python
# SOURCE CODE (broken):
f"{get_path_manager().CONFIG_DIR}/config.json"

# UnifiedPathManager only has:
CONFIG_DIR_NAME = ".claude-mpm"  # Not CONFIG_DIR
```

**Fix Option A (Preferred - Source Fix)**: Add `CONFIG_DIR` property to `UnifiedPathManager`:
```python
# In src/claude_mpm/core/unified_paths.py
@property
def CONFIG_DIR(self) -> str:
    """Backwards-compatible alias for CONFIG_DIR_NAME."""
    return self.CONFIG_DIR_NAME
```

**Fix Option B (Alternative)**: Update all callers to use `CONFIG_DIR_NAME`.

**Files to modify**:
- `src/claude_mpm/core/unified_paths.py` (add property, ~3 lines)

**Verification**:
```bash
pytest tests/unit/services/version_control/test_branch_strategy.py -x --tb=short
```

**Success Criteria**: All 52 `AttributeError: 'UnifiedPathManager' object has no attribute 'CONFIG_DIR'` errors eliminated.

---

### 1E. Fix `claude_mpm.__getattr__` Blocking Submodule Patches (~43 tests)

**Root Cause**: `src/claude_mpm/__init__.py` defines a `__getattr__` that raises `AttributeError` for any attribute not in its whitelist (`ClaudeRunner`, `MPMOrchestrator`, `TicketManager`). When tests do `patch("claude_mpm.mcp.session_manager.SessionManager")`, Python tries to resolve `claude_mpm.mcp` which triggers `__getattr__`, which raises `AttributeError`.

**Pattern**:
```python
# __init__.py (broken for patching):
def __getattr__(name):
    if name == "ClaudeRunner": ...
    if name == "MPMOrchestrator": ...
    if name == "TicketManager": ...
    raise AttributeError(...)  # Blocks all submodule access!
```

**Introduced by**: Commit `e027d76e` ("perf: optimize hook handler initialization with lazy imports")

**Fix**: Update `__getattr__` to allow normal submodule resolution:
```python
def __getattr__(name):
    if name == "ClaudeRunner":
        from .core.claude_runner import ClaudeRunner
        return ClaudeRunner
    if name == "MPMOrchestrator":
        from .core.claude_runner import ClaudeRunner
        return ClaudeRunner
    if name == "TicketManager":
        from .services.ticket_manager import TicketManager
        return TicketManager
    # Allow normal submodule resolution for patch() targets
    try:
        import importlib
        return importlib.import_module(f".{name}", __name__)
    except ImportError:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
```

**Files to modify**:
- `src/claude_mpm/__init__.py` (~5 lines changed)

**Verification**:
```bash
pytest tests/mcp/test_session_manager.py -x --tb=short
pytest tests/mcp/test_session_server_http.py -x --tb=short
```

**Success Criteria**: All 43 `module 'claude_mpm' has no attribute 'mcp'` errors eliminated.

---

### 1F. Fix `self / "filename"` Path Division on Test Instances (~38 tests)

**Root Cause**: Test class methods use `self / "filename.json"` as if `self` were a `pathlib.Path` object. This is a pattern where tests were likely converted from standalone functions (where a path variable was named `self` or `tmp_path` was in scope) to class methods without updating the references.

**Pattern**:
```python
# BROKEN:
class TestFrontmatterFormat:
    def test_frontmatter_structure_valid(self):
        agent_file = self / "test_agent.md"  # self is not a Path!

# FIXED:
class TestFrontmatterFormat:
    def test_frontmatter_structure_valid(self, tmp_path):
        agent_file = tmp_path / "test_agent.md"
```

**Files to modify**:

| File | Test Class | Methods |
|---|---|---|
| `tests/test_frontmatter_format.py` | TestFrontmatterFormat | 9 |
| `tests/test_instruction_synthesis.py` | TestInstructionSynthesis | 9 |
| `tests/test_schema_standardization.py` | TestSchemaStandardization | 5 |
| `tests/test_agent_loader_format.py` | TestAgentLoaderFormats | 4 |
| `tests/test_unified_config.py` | TestUnifiedPathManager | 4 |
| `tests/integration/test_schema_integration.py` | TestSchemaIntegration | 3 |
| `tests/test_unified_agent_registry.py` | TestAgentRegistryAdapter | 3 |

**Fix Strategy**: In each test method, add `tmp_path` as parameter and replace `self / "..."` with `tmp_path / "..."`.

**Verification**:
```bash
pytest tests/test_frontmatter_format.py -x --tb=short
pytest tests/test_instruction_synthesis.py -x --tb=short
pytest tests/test_schema_standardization.py -x --tb=short
```

**Success Criteria**: All 38 `unsupported operand type(s) for /: 'TestFoo' and 'str'` errors eliminated.

---

### 1G. Fix `get_agent_registry` Not Imported (~4 tests)

**Root Cause**: Tests reference `get_agent_registry()` without importing it.

**File**: `tests/test_agent_registry_cache.py`

**Fix**: Add import: `from claude_mpm.core.unified_agent_registry import get_agent_registry`

**Verification**:
```bash
pytest tests/test_agent_registry_cache.py -x --tb=short
```

---

### Phase 1 Summary

| Fix | Tests Fixed | Effort |
|---|---|---|
| 1A. Missing `self` parameter | ~379 | 4 hours (scripted) |
| 1B. `tmp_path` misuse | ~153 | 3 hours |
| 1C. `Config` not imported | ~61 | 1 hour |
| 1D. `CONFIG_DIR` property | ~52 | 30 min |
| 1E. `__getattr__` fix | ~43 | 30 min |
| 1F. `self / "filename"` | ~38 | 2 hours |
| 1G. `get_agent_registry` | ~4 | 15 min |
| **TOTAL** | **~730** | **~11 hours** |

**Smoke Test After Phase 1**:
```bash
# Quick verification across all fixed categories
pytest tests/cli/test_base_command.py tests/cli/test_shared_utilities.py \
  tests/test_frontmatter_format.py tests/test_instruction_synthesis.py \
  tests/test_memory_fixes_verification.py tests/mcp/test_session_manager.py \
  tests/unit/services/version_control/test_branch_strategy.py \
  --tb=short -q 2>&1 | tail -5

# Full regression (should show ~730 fewer failures)
pytest --tb=no -q 2>&1 | tail -3
```

---

## Phase 2: File and Module Infrastructure (~170 tests)

**Target**: Fix ~170 additional tests (~10% of total)
**Estimated Effort**: 1-2 days
**Dependencies**: Phase 1 complete

### 2A. Fix Missing Template Files (~78 tests)

**Root Cause**: Tests reference JSON template files in `src/claude_mpm/agents/templates/` but the directory only contains `.md` files. Templates were migrated from JSON to Markdown format.

**Historical context**: Commit `831be541` (2025-12-01) deliberately removed `mpm-skills-manager.json` and `mpm-agent-manager.json`. Commit message: *"These agents now exist in bobmatnyc/claude-mpm-agents Git repository. JSON templates are deprecated in favor of Git cache workflow."*

**Current state of `src/claude_mpm/agents/templates/`**:
```
__init__.py, archive/, circuit-breakers.md, context-management-examples.md,
git-file-tracking.md, pm-examples.md, pm-red-flags.md, pr-workflow-examples.md,
README.md, research-gate-examples.md, response-format.md,
structured-questions-examples.md, ticket-completeness-examples.md,
ticketing-examples.md, validation-templates.md
```

No `.json` files exist. Tests expect files like `mpm-skills-manager.json`, `test_agent.json`, etc.

**Fix Strategy**: Two-pronged approach:
1. **For tests referencing specific template files** (e.g., `mpm-skills-manager.json`): Update tests to use the new `.md` template format or mock the template loading
2. **For tests creating temp dir structures** (e.g., `tmp_path / "templates" / "agent.json"`): Tests need `mkdir -p` for the parent directory before writing

**Key files**:

| File | Issue | Fix |
|---|---|---|
| `tests/agents/test_mpm_skills_manager.py` | Opens non-existent `mpm-skills-manager.json` | Update to correct file path or mark as obsolete |
| `tests/test_agent_deployment_comprehensive.py` | Writes to `tmp_path/templates/` without mkdir | Add `(tmp_path / "templates").mkdir()` |
| `tests/test_agent_deployment_system.py` | Same mkdir issue | Add directory creation |
| `tests/hooks/claude_hooks/test_pre_split_verification.py` | References deleted file `test_hook_handler_comprehensive.py` | Skip/delete these verification tests |

**Verification**:
```bash
pytest tests/agents/test_mpm_skills_manager.py -x --tb=short
pytest tests/test_agent_deployment_comprehensive.py -x --tb=short
pytest tests/test_agent_deployment_system.py -x --tb=short
```

**Success Criteria**: All 78 `FileNotFoundError` tests in file_and_fs category resolved.

---

### 2B. Fix Missing Module Imports (~13 tests)

**Root Cause**: Tests import modules that have been moved, renamed, or whose dependencies aren't installed.

| Module | Issue | Fix |
|---|---|---|
| `aggregate_agent_dependencies` | Script moved/removed | Skip tests or update import path |
| `mcp.server` | Optional dependency not installed | Add `pytest.importorskip("mcp")` |
| `claude_mpm.cli.commands.parser` | Module removed | Update to current CLI structure |
| `get_python_executable` | Function renamed in socketio_daemon | Update import name |
| `_ensure_run_attributes` | Function removed from `claude_mpm.cli` | Update or remove tests |
| `PYTHON_EXECUTABLE` | Constant removed | Update or remove tests |

**Files to modify**:

| File | Fix |
|---|---|
| `tests/integration/misc/test_dependency_system.py` | Update import or skip |
| `tests/mcp/test_errors.py` | Add `pytest.importorskip("mcp")` |
| `tests/mcp/test_session_server.py` | Add `pytest.importorskip("mcp")` |
| `tests/test_resume_command_build.py` | Update to current CLI module |
| `tests/test_resume_flag_fix.py` | Update to current CLI module |
| `tests/test_socketio_daemon.py` | Update function name imports |
| `tests/test_socketio_fixes.py` | Update function name imports |
| `tests/test_unified_config.py` | Update import |

**Verification**:
```bash
pytest tests/integration/misc/test_dependency_system.py -x --tb=short
pytest tests/mcp/test_errors.py tests/mcp/test_session_server.py -x --tb=short
```

---

### 2C. Fix `PosixPath` Not JSON Serializable (~5 tests, SOURCE BUG)

**Root Cause**: `src/claude_mpm/hooks/claude_hooks/installer.py:824` passes a `PosixPath` object to `json.dump()` without converting to string.

**Fix**:
```python
# In src/claude_mpm/hooks/claude_hooks/installer.py
# Before json.dump(settings, f, indent=2), ensure all paths are strings:
# Option: Use a custom JSON encoder
class PathEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

json.dump(settings, f, indent=2, cls=PathEncoder)
```

**Files to modify**:
- `src/claude_mpm/hooks/claude_hooks/installer.py` (~5 lines)

**Verification**:
```bash
pytest tests/test_hook_installer.py -x --tb=short
```

---

### 2D. Fix Missing Template Directories in Tests (~12 tests)

**Root Cause**: Tests write to subdirectories of `tmp_path` (e.g., `tmp_path / "templates" / "agent.json"`) without first creating the parent directory.

**Fix**: Add `(tmp_path / "templates").mkdir(parents=True, exist_ok=True)` before writes.

**Files**: `test_agent_deployment_comprehensive.py`, `test_agent_deployment_system.py`

---

### 2E. Fix `rmdir()` on Non-Empty Directories (~2 tests)

**Root Cause**: Tests use `pathlib.Path.rmdir()` which only works on empty directories.

**Fix**: Replace `rmdir()` with `shutil.rmtree()`.

**File**: `tests/unit/services/cli/test_session_resume_helper.py`

---

### Phase 2 Summary

| Fix | Tests Fixed | Effort |
|---|---|---|
| 2A. Missing templates | ~78 | 4 hours |
| 2B. Missing modules | ~13 | 2 hours |
| 2C. PosixPath serialization | ~5 | 30 min |
| 2D. Missing temp dirs | ~12 | 1 hour |
| 2E. rmdir non-empty | ~2 | 15 min |
| **TOTAL** | **~110** | **~8 hours** |

**Smoke Test After Phase 2**:
```bash
pytest tests/agents/ tests/mcp/ tests/hooks/ tests/test_hook_installer.py --tb=short -q 2>&1 | tail -5
pytest --tb=no -q 2>&1 | tail -3  # Should show ~840 fewer total failures
```

---

## Phase 3: API Contract Alignment (~500 tests)

**Target**: Fix ~500 additional tests (~29% of total)
**Estimated Effort**: 3-5 days
**Dependencies**: Phase 1 and Phase 2 complete

### 3A. Fix `HealthStatus` Enum Mismatches (~15 tests)

**Root Cause**: Tests reference `HealthStatus.WARNING` and `HealthStatus.CRITICAL`, but the actual enum at `src/claude_mpm/core/enums.py:220` has:
- `HEALTHY`, `UNHEALTHY`, `DEGRADED`, `UNKNOWN`, `CHECKING`

No `WARNING` or `CRITICAL` members exist.

**Historical context**: Commit `7a84f920` (2025-10-26) consolidated enums with explicit mapping: `WARNING -> DEGRADED`, `CRITICAL -> UNHEALTHY`. Test files were not updated.

**Files to modify**:
- `tests/services/test_monitoring_refactored.py` (10 tests)
- `tests/test_health_monitoring_comprehensive.py` (5 tests)

**Fix**: Replace `HealthStatus.WARNING` → `HealthStatus.DEGRADED` and `HealthStatus.CRITICAL` → `HealthStatus.UNHEALTHY`.

---

### 3B. Fix `PID_FILE` → `DEFAULT_PID_FILE` Rename (~10 tests)

**Root Cause**: Tests patch `claude_mpm.scripts.socketio_daemon.PID_FILE` but the module uses `DEFAULT_PID_FILE`.

**File**: `tests/test_socketio_daemon.py`

**Fix**: Update all `patch("claude_mpm.scripts.socketio_daemon.PID_FILE")` to `patch("claude_mpm.scripts.socketio_daemon.DEFAULT_PID_FILE")`.

---

### 3C. Fix Test Class Calling SUT Methods via `self` (~80+ tests)

**Root Cause**: Test classes call `self.method_name()` where `method_name` belongs to the System Under Test (SUT), not the test class. This is a systematic LLM-generated test antipattern where the test class was written as if it IS the SUT.

**Pattern**:
```python
# BROKEN (test class calls SUT method on self):
class TestAgentMetricsCollector:
    def test_update_deployment_metrics_success(self):
        self.update_deployment_metrics(150.5, results)  # self is not the collector!

# FIXED:
class TestAgentMetricsCollector:
    def setup_method(self):
        self.collector = AgentMetricsCollector()

    def test_update_deployment_metrics_success(self):
        self.collector.update_deployment_metrics(150.5, results)
```

**Key patterns**:

| Test Class | Missing Attribute | Likely Fix |
|---|---|---|
| `TestEventHandlerRegistry` | `self.initialize()` | Call on the subject: `self.registry.initialize()` |
| `TestAgentMetricsCollector` | `self.update_deployment_metrics()` | Call on the subject: `self.collector.update_deployment_metrics()` |
| `TestAgentConfigurationManager` | `self.get_agent_types()`, `self.get_agent_status()` | Call on subject |
| `TestGitEventHandler` | `self.sio` | Set up in `setup_method` |
| `TestConnectionEventHandler` | `self.sio` | Set up in `setup_method` |
| `TestAdvancedHealthMonitor` | `self.get()` | Call on subject |
| `TestSchemaStandardization` | `self._validate_agent_schema()` | Call on subject |
| `TestAgentCapabilitiesService` | `self._discover_agent_capabilities()` | Call on subject |

**Estimated files**: ~15-20 test files
**Fix Strategy**: For each test class, identify the test subject (the object being tested) and redirect method calls from `self.method()` to `self.subject.method()`.

---

### 3D. Fix Stale Mock Patches (~42+ tests in attribute_errors)

**Root Cause**: Tests use `patch("claude_mpm.module.ClassName.old_method")` but the method was renamed. The `patch()` call fails because the attribute doesn't exist on the target.

**Key patterns**:
- `patch("claude_mpm.scripts.socketio_daemon.PID_FILE")` → `DEFAULT_PID_FILE`
- `patch.object(manager, "_get_memory_file_with_migration")` → method removed/renamed
- `property 'project_root' of 'ClaudeMPMPaths' has no deleter` → property changed

**Fix**: Update patch targets to match current API.

---

### 3E. Fix `ValueError: Markdown template missing YAML frontmatter` (~10 tests)

**Root Cause**: Tests create agent markdown files without YAML frontmatter, but `agent_template_builder.py:181` now requires it.

**File**: `tests/integration/test_non_compliant_repo_compatibility.py`

**Fix**: Add YAML frontmatter to test template files:
```markdown
---
name: test-agent
version: "1.0.0"
---
# Agent content
```

---

### 3F. Fix Assertion Value Mismatches (~200+ tests)

**Root Cause**: Tests assert specific values that have changed due to code evolution:
- Agent list counts changed (e.g., `assert len(agents) == 3` but now returns 10)
- Return value shapes changed
- Mock configurations don't match current API

**Strategy**: For each assertion failure:
1. Read the source code to understand current behavior
2. Determine if the test expectation or the code is wrong
3. Update the test to match current correct behavior

**This is the largest and most labor-intensive fix**. Many of these will require individual investigation.

**Key files** (highest failure count):
- `tests/services/agents/test_agent_selection_service.py`
- `tests/services/agents/sources/test_git_source_sync_service.py`
- `tests/eval/agents/shared/test_agent_infrastructure.py`
- `tests/eval/test_cases/test_pm_behavioral_compliance.py`
- `tests/cli/commands/test_agents_comprehensive.py`

---

### 3G. Fix AsyncIO Event Loop Issues (~3 tests)

**Root Cause**: `asyncio.get_event_loop()` in Python 3.12 raises `RuntimeError` when no event loop exists.

**File**: `tests/services/agents/test_auto_config_manager.py`

**Fix**: Use `asyncio.new_event_loop()` or add `@pytest.fixture` with `asyncio.run()`.

---

### Phase 3 Summary

| Fix | Tests Fixed | Effort |
|---|---|---|
| 3A. HealthStatus enum | ~15 | 1 hour |
| 3B. PID_FILE rename | ~10 | 30 min |
| 3C. Method/attribute redirects | ~67 | 6 hours |
| 3D. Stale mock patches | ~42 | 4 hours |
| 3E. Missing frontmatter | ~10 | 1 hour |
| 3F. Assertion value updates | ~200+ | 12-16 hours |
| 3G. AsyncIO event loop | ~3 | 30 min |
| **TOTAL** | **~350+** | **~25-30 hours** |

**Smoke Test After Phase 3**:
```bash
pytest tests/services/ tests/eval/ tests/cli/ --tb=short -q 2>&1 | tail -5
pytest --tb=no -q 2>&1 | tail -3  # Target: <300 remaining failures
```

---

## Phase 4: Cleanup and Hardening

**Target**: Fix remaining ~200-300 tests + remove obsolete tests
**Estimated Effort**: 2-3 days
**Dependencies**: Phase 3 complete

### 4A. Remove Obsolete Tests

Based on analysis, the following test files test functionality that no longer exists:

| File | Reason | Action |
|---|---|---|
| `tests/hooks/claude_hooks/test_pre_split_verification.py` | References deleted `test_hook_handler_comprehensive.py` | Delete |
| `tests/test_pack.py` | Tests gitdb pack files that don't exist in venv | Delete |
| `tests/integration/misc/test_dependency_system.py` | Tests removed `aggregate_agent_dependencies` module | Delete or skip |
| Various `test_config_duplicate_*` files | Testing config behavior that's been refactored | Review and consolidate |

**Note**: Final list should be informed by task #4 (test relevance audit).

### 4B. Fix SocketIO / Network Integration Tests (~6 tests)

These tests require a running Socket.IO server or need proper mocking:
- `tests/test_http_event_flow.py`
- `tests/test_socketio_broadcast.py`
- `tests/test_hook_http_integration.py`
- `tests/dashboard/test_dashboard_fixes.py`

**Fix**: Add `@pytest.mark.integration` marker and proper server mocking.

### 4C. Fix Git Operations Mock Issues (~4 tests)

**File**: `tests/unit/services/version_control/test_git_operations.py`

Mock for `subprocess.run` not properly configured for the new `_enforce_branch_protection` call chain.

### 4D. Add Missing Fixtures

Create shared fixtures for common patterns:
- `config` fixture that provides `Config()` instance
- `path_manager` fixture that provides properly initialized `UnifiedPathManager`
- `template_dir` fixture that creates temp directory with proper structure

### 4E. Final Verification and Documentation

```bash
# Run full test suite
pytest --tb=short -q 2>&1 | tail -20

# Generate coverage report
pytest --cov=claude_mpm --cov-report=term-missing --tb=no -q

# Document remaining failures with reasons
pytest --tb=line -q 2>&1 | grep "FAILED" > docs-local/failure-research-opus/remaining-failures.txt
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Fix in Phase 1 breaks passing tests | Low | Medium | Run full suite after each fix batch |
| Source code fix (CONFIG_DIR, __getattr__) has side effects | Medium | High | Test with integration tests, not just unit |
| Phase 3 assertion updates mask real bugs | Medium | High | Review each assertion change for correctness |
| Obsolete test removal loses coverage | Low | Medium | Verify coverage before/after deletion |

## Rollback Strategy

Each phase should be committed separately:
```bash
git checkout -b fix/phase-1-infrastructure
# ... make changes ...
git commit -m "fix(tests): Phase 1 - infrastructure quick wins"

git checkout -b fix/phase-2-file-module
# ... make changes ...
git commit -m "fix(tests): Phase 2 - file and module infrastructure"

# etc.
```

If any phase introduces regressions:
```bash
git revert HEAD  # Revert last phase commit
```

## Execution Order Summary

```
Phase 1A (self params)     ──┐
Phase 1B (tmp_path)        ──┤
Phase 1C (Config import)   ──┤── Parallel execution possible
Phase 1D (CONFIG_DIR)      ──┤
Phase 1E (__getattr__)     ──┤
Phase 1F (self / path)     ──┤
Phase 1G (get_agent_reg)   ──┘
         │
    [Smoke Test]
         │
Phase 2A (templates)       ──┐
Phase 2B (modules)         ──┤── Parallel execution possible
Phase 2C (PosixPath)       ──┤
Phase 2D (temp dirs)       ──┤
Phase 2E (rmdir)           ──┘
         │
    [Smoke Test]
         │
Phase 3A-G (API alignment)  ── Sequential (each fix may affect others)
         │
    [Full Regression]
         │
Phase 4 (cleanup)            ── After relevance audit (task #4)
         │
    [Final Verification]
```

## Expected Outcome

| Phase | Cumulative Tests Fixed | % of 1,726 |
|---|---|---|
| After Phase 1 | ~730 | 42% |
| After Phase 2 | ~840 | 49% |
| After Phase 3 | ~1,200 | 70% |
| After Phase 4 | ~1,500+ | 87%+ |

Remaining ~200 tests will likely be:
- Genuinely broken tests needing individual investigation
- Tests for deprecated features (candidates for deletion)
- Environment-specific tests (CI-only, network-dependent)
