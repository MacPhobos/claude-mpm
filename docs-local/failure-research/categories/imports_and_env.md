# Failure Category: imports_and_env

## A. Snapshot
- **Total failures**: 12
- **Top exception types**:
  - `ModuleNotFoundError`: 6
  - `ImportError`: 4
  - `Hint`: 2
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `ModuleNotFoundError: No module named <str> \| <unknown>` | 6 |
  | `ImportError: cannot import name <str> from <str> (<path> \| <unknown>` | 4 |
  | `collection failure \| <unknown>` | 2 |

## B. Representative Examples

### Subpattern: `ModuleNotFoundError: No module named <str> | <unknown>` (6 failures)

**Example 1**
- **nodeid**: `tests/integration/misc/test_dependency_system.py::test_dependency_parsing`
- **file_hint**: `tests/integration/misc/test_dependency_system.py`
- **failure**:
```
exc_type: ModuleNotFoundError
message: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
--- relevant traceback (up to 30 lines) ---
tests/integration/misc/test_dependency_system.py:56: in test_dependency_parsing
    from aggregate_agent_dependencies import DependencyAggregator
E   ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
```

**Example 2**
- **nodeid**: `tests/integration/misc/test_dependency_system.py::test_version_conflict_resolution`
- **file_hint**: `tests/integration/misc/test_dependency_system.py`
- **failure**:
```
exc_type: ModuleNotFoundError
message: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
--- relevant traceback (up to 30 lines) ---
tests/integration/misc/test_dependency_system.py:82: in test_version_conflict_resolution
    from aggregate_agent_dependencies import DependencyAggregator
E   ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
```

**Example 3**
- **nodeid**: `tests/integration/misc/test_dependency_system.py::test_pyproject_update`
- **file_hint**: `tests/integration/misc/test_dependency_system.py`
- **failure**:
```
exc_type: ModuleNotFoundError
message: ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
--- relevant traceback (up to 30 lines) ---
tests/integration/misc/test_dependency_system.py:140: in test_pyproject_update
    from aggregate_agent_dependencies import DependencyAggregator
E   ModuleNotFoundError: No module named 'aggregate_agent_dependencies'
```

### Subpattern: `ImportError: cannot import name <str> from <str> (<path> | <unknown>` (4 failures)

**Example 1**
- **nodeid**: `tests/test_resume_flag_fix.py::test_command_construction`
- **file_hint**: `tests/test_resume_flag_fix.py`
- **failure**:
```
exc_type: ImportError
message: ImportError: cannot import name '_ensure_run_attributes' from 'claude_mpm.cli' (/Users/mac/workspace/claude-mpm/src/claude_mpm/cli/__init__.py)
--- relevant traceback (up to 30 lines) ---
tests/test_resume_flag_fix.py:87: in test_command_construction
    from claude_mpm.cli import _ensure_run_attributes
E   ImportError: cannot import name '_ensure_run_attributes' from 'claude_mpm.cli' (/Users/mac/workspace/claude-mpm/src/claude_mpm/cli/__init__.py)
```

**Example 2**
- **nodeid**: `tests/test_socketio_fixes.py::test_python_environment_detection`
- **file_hint**: `tests/test_socketio_fixes.py`
- **failure**:
```
exc_type: ImportError
message: ImportError: cannot import name 'PYTHON_EXECUTABLE' from 'claude_mpm.scripts.socketio_daemon' (/Users/mac/workspace/claude-mpm/src/claude_mpm/scripts/socketio_daemon.py)
--- relevant traceback (up to 30 lines) ---
tests/test_socketio_fixes.py:29: in test_python_environment_detection
    from claude_mpm.scripts.socketio_daemon import PYTHON_EXECUTABLE
E   ImportError: cannot import name 'PYTHON_EXECUTABLE' from 'claude_mpm.scripts.socketio_daemon' (/Users/mac/workspace/claude-mpm/src/claude_mpm/scripts/socketio_daemon.py)
```

**Example 3**
- **nodeid**: `tests/test_socketio_daemon.py::TestPythonEnvironmentDetection::test_venv_detection_with_virtual_env`
- **file_hint**: `tests/test_socketio_daemon/TestPythonEnvironmentDetection.py`
- **failure**:
```
exc_type: ImportError
message: ImportError: cannot import name 'get_python_executable' from 'claude_mpm.scripts.socketio_daemon' (/Users/mac/workspace/claude-mpm/src/claude_mpm/scripts/socketio_daemon.py)
--- relevant traceback (up to 30 lines) ---
tests/test_socketio_daemon.py:516: in test_venv_detection_with_virtual_env
    from claude_mpm.scripts.socketio_daemon import get_python_executable
E   ImportError: cannot import name 'get_python_executable' from 'claude_mpm.scripts.socketio_daemon' (/Users/mac/workspace/claude-mpm/src/claude_mpm/scripts/socketio_daemon.py)
```

### Subpattern: `collection failure | <unknown>` (2 failures)

**Example 1**
- **nodeid**: `.py::tests.mcp.test_errors`
- **file_hint**: `.py`
- **failure**:
```
exc_type: Hint
message: collection failure
--- relevant traceback (up to 30 lines) ---
ImportError while importing test module '/Users/mac/workspace/claude-mpm/tests/mcp/test_errors.py'.
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

**Example 2**
- **nodeid**: `.py::tests.mcp.test_session_server`
- **file_hint**: `.py`
- **failure**:
```
exc_type: Hint
message: collection failure
--- relevant traceback (up to 30 lines) ---
ImportError while importing test module '/Users/mac/workspace/claude-mpm/tests/mcp/test_session_server.py'.
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

## C. Hypotheses

- Missing Python packages not installed in the test virtualenv.
- Environment variables required by the code are not set in the test harness.
- Optional dependency installed in dev but not in CI environment.
- Circular import introduced by recent refactoring.
- Package renamed or removed in a recent dependency upgrade.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Run `pip check` to verify installed packages are consistent.
- [ ] Compare `pip freeze` between dev and CI environments.
- [ ] Check if required env vars are set: search `os.environ` and `os.getenv` near failures.
- [ ] Verify `pyproject.toml` / `requirements.txt` includes all test dependencies.

## E. Targeted Repo Queries

```bash
rg "import" src/ --include="*.py" -l
rg "os\.environ|os\.getenv|dotenv" src/ --include="*.py"
rg "ModuleNotFoundError|ImportError" tests/ --include="*.py"
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/integration/misc/test_dependency_system.py::test_dependency_parsing" -xvs

# Run small set for this bucket
pytest -k 'import or env' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the imports_and_env bucket:
  tests/integration/misc/test_dependency_system.py::test_dependency_parsing
  tests/test_resume_flag_fix.py::test_command_construction
  .py::tests.mcp.test_errors

And these relevant source files:
  tests/integration/misc/test_dependency_system.py
  tests/test_resume_flag_fix.py
  .py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
