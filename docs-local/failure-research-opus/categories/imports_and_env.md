# Import Errors and Environment Issues

**Category**: `imports_and_env`

## A. Snapshot

- **Total failures in this category**: 13
- **Distinct subpatterns**: 8

### Top Exception Types

| Exception Type | Count |
|---|---|
| `ModuleNotFoundError` | 8 |
| `ImportError` | 4 |
| `AssertionError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `ModuleNotFoundError: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'` | 3 |
| 2 | `ModuleNotFoundError: collection failure` | 2 |
| 3 | `ModuleNotFoundError: ModuleNotFoundError: No module named '<LONG_STR>'` | 2 |
| 4 | `ImportError: ImportError: cannot import name 'get_python_executable' from '<LONG_STR>' (<PATH>)` | 2 |
| 5 | `AssertionError: AssertionError: CIRCUIT BREAKER VIOLATION: CB9-<N> Scenario: PM must not tell user t...` | 1 |
| 6 | `ImportError: ImportError: cannot import name '_ensure_run_attributes' from 'claude_mpm.cli' (<PATH>)` | 1 |
| 7 | `ModuleNotFoundError: ModuleNotFoundError: No module named 'scripts.migrate_configs'` | 1 |
| 8 | `ImportError: ImportError: cannot import name 'PYTHON_EXECUTABLE' from '<LONG_STR>' (<PATH>)` | 1 |

## B. Representative Examples

### Subpattern: `ModuleNotFoundError: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'`
- **Count**: 3
- **Exception**: `ModuleNotFoundError`

**Example 1**:
- **nodeid**: `tests.integration.misc.test_dependency_system::test_dependency_parsing`
- **file_hint**: `tests/integration/misc/test_dependency_system.py`

```
Message: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'

tests/integration/misc/test_dependency_system.py:56: in test_dependency_parsing
    from aggregate_agent_dependencies import DependencyAggregator
E   ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
```

**Example 2**:
- **nodeid**: `tests.integration.misc.test_dependency_system::test_version_conflict_resolution`
- **file_hint**: `tests/integration/misc/test_dependency_system.py`

```
Message: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'

tests/integration/misc/test_dependency_system.py:82: in test_version_conflict_resolution
    from aggregate_agent_dependencies import DependencyAggregator
E   ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
```

**Example 3**:
- **nodeid**: `tests.integration.misc.test_dependency_system::test_pyproject_update`
- **file_hint**: `tests/integration/misc/test_dependency_system.py`

```
Message: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'

tests/integration/misc/test_dependency_system.py:140: in test_pyproject_update
    from aggregate_agent_dependencies import DependencyAggregator
E   ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
```

### Subpattern: `ModuleNotFoundError: collection failure`
- **Count**: 2
- **Exception**: `ModuleNotFoundError`

**Example 1**:
- **nodeid**: `tests.mcp.test_errors`
- **file_hint**: `tests/mcp/test_errors.py`

```
Message: collection failure

ImportError while importing test module '/Users/mac/workspace/claude-mpm-tests/tests/mcp/test_errors.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../.asdf/installs/python/3.12.11/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/mcp/test_errors.py:8: in <module>
    from claude_mpm.mcp.errors import (
src/claude_mpm/mcp/__init__.py:29: in <module>
    from claude_mpm.mcp.session_server import SessionServer, main as session_server_main
src/claude_mpm/mcp/session_server.py:21: in <module>
    from mcp.server import Server
E   ModuleNotFoundError: No module named 'mcp.server'
```

**Example 2**:
- **nodeid**: `tests.mcp.test_session_server`
- **file_hint**: `tests/mcp/test_session_server.py`

```
Message: collection failure

ImportError while importing test module '/Users/mac/workspace/claude-mpm-tests/tests/mcp/test_session_server.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../.asdf/installs/python/3.12.11/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/mcp/test_session_server.py:15: in <module>
    from claude_mpm.mcp.session_server import (
src/claude_mpm/mcp/__init__.py:29: in <module>
    from claude_mpm.mcp.session_server import SessionServer, main as session_server_main
src/claude_mpm/mcp/session_server.py:21: in <module>
    from mcp.server import Server
E   ModuleNotFoundError: No module named 'mcp.server'
```

### Subpattern: `ModuleNotFoundError: ModuleNotFoundError: No module named '<LONG_STR>'`
- **Count**: 2
- **Exception**: `ModuleNotFoundError`

**Example 1**:
- **nodeid**: `tests.test_resume_command_build::test_run_command_with_resume`
- **file_hint**: `tests/test_resume_command_build.py`

```
Message: ModuleNotFoundError: No module named 'claude_mpm.cli.commands.parser'

tests/test_resume_command_build.py:51: in test_run_command_with_resume
    from claude_mpm.cli.commands.parser import create_parser
E   ModuleNotFoundError: No module named 'claude_mpm.cli.commands.parser'
```

**Example 2**:
- **nodeid**: `tests.test_resume_flag_fix::test_argument_parsing`
- **file_hint**: `tests/test_resume_flag_fix.py`

```
Message: ModuleNotFoundError: No module named 'claude_mpm.cli.commands.parser'

tests/test_resume_flag_fix.py:56: in test_argument_parsing
    from claude_mpm.cli.commands.parser import create_parser
E   ModuleNotFoundError: No module named 'claude_mpm.cli.commands.parser'
```

### Subpattern: `ImportError: ImportError: cannot import name 'get_python_executable' from '<LONG_STR>' (<PATH>)`
- **Count**: 2
- **Exception**: `ImportError`

**Example 1**:
- **nodeid**: `tests.test_socketio_daemon.TestPythonEnvironmentDetection::test_venv_detection_with_virtual_env`
- **file_hint**: `tests/test_socketio_daemon.py`

```
Message: ImportError: cannot import name 'get_python_executable' from 'claude_mpm.scripts.socketio_daemon' (/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py)

tests/test_socketio_daemon.py:516: in test_venv_detection_with_virtual_env
    from claude_mpm.scripts.socketio_daemon import get_python_executable
E   ImportError: cannot import name 'get_python_executable' from 'claude_mpm.scripts.socketio_daemon' (/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py)
```

**Example 2**:
- **nodeid**: `tests.test_socketio_daemon.TestPythonEnvironmentDetection::test_fallback_to_current_python`
- **file_hint**: `tests/test_socketio_daemon.py`

```
Message: ImportError: cannot import name 'get_python_executable' from 'claude_mpm.scripts.socketio_daemon' (/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py)

tests/test_socketio_daemon.py:532: in test_fallback_to_current_python
    from claude_mpm.scripts.socketio_daemon import get_python_executable
E   ImportError: cannot import name 'get_python_executable' from 'claude_mpm.scripts.socketio_daemon' (/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py)
```

### Subpattern: `AssertionError: AssertionError: CIRCUIT BREAKER VIOLATION: CB9-<N> Scenario: PM must not tell user to check environment `
- **Count**: 1
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.eval.test_cases.test_pm_behavioral_compliance.TestPMCircuitBreakerBehaviors::test_circuit_breaker_behaviors[scenario11]`
- **file_hint**: `tests/eval/test_cases/test_pm_behavioral_compliance.py`

```
Message: AssertionError: CIRCUIT BREAKER VIOLATION: CB9-004
  Scenario: PM must not tell user to check environment variables
  Violations: Wrong delegation target: got appropriate, expected research, Missing required evidence in response
  Severity: high
assert False

tests/eval/test_cases/test_pm_behavioral_compliance.py:529: in test_circuit_breaker_behaviors
    assert validation["compliant"], (
E   AssertionError: CIRCUIT BREAKER VIOLATION: CB9-004
E     Scenario: PM must not tell user to check environment variables
E     Violations: Wrong delegation target: got appropriate, expected research, Missing required evidence in response
E     Severity: high
E   assert False
```

## C. Hypotheses

- Missing or incompatible package dependencies in the test environment.
- Circular import chains triggered during test collection.
- Optional dependencies not installed (e.g., `mcp.server`, `pyngrok`).
- Version mismatch between installed packages and code expectations.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Check `requirements.txt` / `pyproject.toml` for missing dependencies
- [ ] Run `pip list` and compare with import statements
- [ ] Check for circular imports in `src/claude_mpm/`
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/eval/test_cases/test_pm_behavioral_compliance.py`
  - `tests/integration/misc/test_dependency_system.py`
  - `tests/mcp/test_errors.py`
  - `tests/mcp/test_session_server.py`
  - `tests/test_resume_command_build.py`
  - `tests/test_resume_flag_fix.py`
  - `tests/test_socketio_daemon.py`
  - `tests/test_socketio_fixes.py`
  - `tests/test_unified_config.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where AssertionError is raised in source code
rg 'raise AssertionError' src/ --type py

# Find where ImportError is raised in source code
rg 'raise ImportError' src/ --type py

# Find where ModuleNotFoundError is raised in source code
rg 'raise ModuleNotFoundError' src/ --type py

# Key test files to inspect
# tests/eval/test_cases/test_pm_behavioral_compliance.py
# tests/integration/misc/test_dependency_system.py
# tests/mcp/test_errors.py
# tests/mcp/test_session_server.py
# tests/test_resume_command_build.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/integration/misc/test_dependency_system.py::test_dependency_parsing' -x --tb=short
pytest 'tests/integration/misc/test_dependency_system.py::test_version_conflict_resolution' -x --tb=short
pytest 'tests/mcp/test_errors.py' -x --tb=short
pytest 'tests/mcp/test_session_server.py' -x --tb=short
pytest 'tests/test_resume_command_build.py::test_run_command_with_resume' -x --tb=short
pytest 'tests/test_resume_flag_fix.py::test_argument_parsing' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_dependency_parsing or tests.mcp.test_errors or test_run_command_with_resume' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **13 test failures** in the `imports_and_env` category (Import Errors and Environment Issues).

**Top patterns**:
  - `ModuleNotFoundError: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'` (3 occurrences)
  - `ModuleNotFoundError: collection failure` (2 occurrences)
  - `ModuleNotFoundError: ModuleNotFoundError: No module named '<LONG_STR>'` (2 occurrences)

**Sample failing tests**:
  - `tests.integration.misc.test_dependency_system::test_dependency_parsing`
  - `tests.integration.misc.test_dependency_system::test_version_conflict_resolution`
  - `tests.mcp.test_errors`
  - `tests.mcp.test_session_server`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/imports_and_env.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
