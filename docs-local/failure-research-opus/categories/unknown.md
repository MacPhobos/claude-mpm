# Uncategorized / Unknown Errors

**Category**: `unknown`

## A. Snapshot

- **Total failures in this category**: 56
- **Distinct subpatterns**: 11

### Top Exception Types

| Exception Type | Count |
|---|---|
| `NameError` | 43 |
| `Unknown` | 4 |
| `socketio.exceptions.BadNamespaceError` | 3 |
| `claude_mpm.services.version_control.git_operations.GitOperationError` | 3 |
| `ProcessLookupError` | 1 |
| `json.decoder.JSONDecodeError` | 1 |
| `IndexError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `NameError: NameError: name 'Config' is not defined` | 39 |
| 2 | `NameError: NameError: name 'get_agent_registry' is not defined` | 4 |
| 3 | `socketio.exceptions.BadNamespaceError: socketio.exceptions.BadNamespaceError: / is not a connected n...` | 3 |
| 4 | `claude_mpm.services.version_control.git_operations.GitOperationError: claude_mpm.services.version_co...` | 3 |
| 5 | `ProcessLookupError: ProcessLookupError` | 1 |
| 6 | `Exception: Broadcast failed` | 1 |
| 7 | `json.decoder.JSONDecodeError: json.decoder.JSONDecodeError: Expecting value: line <N> column <N> (ch...` | 1 |
| 8 | `Exception: Router error` | 1 |
| 9 | `Exception: Test exception` | 1 |
| 10 | `SystemExit: <N>` | 1 |
| 11 | `IndexError: IndexError: list index out of range` | 1 |

## B. Representative Examples

### Subpattern: `NameError: NameError: name 'Config' is not defined`
- **Count**: 39
- **Exception**: `NameError`

**Example 1**:
- **nodeid**: `tests.integration.infrastructure.test_activity_logging::test_configuration`
- **file_hint**: `tests/integration/infrastructure/test_activity_logging.py`

```
Message: NameError: name 'Config' is not defined

tests/integration/infrastructure/test_activity_logging.py:23: in test_configuration
    config = Config()
             ^^^^^^
E   NameError: name 'Config' is not defined
```

**Example 2**:
- **nodeid**: `tests.integration.infrastructure.test_response_logging::test_response_logging`
- **file_hint**: `tests/integration/infrastructure/test_response_logging.py`

```
Message: NameError: name 'Config' is not defined

tests/integration/infrastructure/test_response_logging.py:27: in test_response_logging
    config = Config()
             ^^^^^^
E   NameError: name 'Config' is not defined
```

**Example 3**:
- **nodeid**: `tests.integration.infrastructure.test_response_logging_debug::test_delegation_tracking`
- **file_hint**: `tests/integration/infrastructure/test_response_logging_debug.py`

```
Message: NameError: name 'Config' is not defined

tests/integration/infrastructure/test_response_logging_debug.py:35: in test_delegation_tracking
    test_config = Config()
                  ^^^^^^
E   NameError: name 'Config' is not defined
```

### Subpattern: `NameError: NameError: name 'get_agent_registry' is not defined`
- **Count**: 4
- **Exception**: `NameError`

**Example 1**:
- **nodeid**: `tests.test_agent_registry_cache::test_basic_caching`
- **file_hint**: `tests/test_agent_registry_cache.py`

```
Message: NameError: name 'get_agent_registry' is not defined

tests/test_agent_registry_cache.py:29: in test_basic_caching
    registry = get_agent_registry()
               ^^^^^^^^^^^^^^^^^^
E   NameError: name 'get_agent_registry' is not defined
```

**Example 2**:
- **nodeid**: `tests.test_agent_registry_cache::test_force_refresh`
- **file_hint**: `tests/test_agent_registry_cache.py`

```
Message: NameError: name 'get_agent_registry' is not defined

tests/test_agent_registry_cache.py:61: in test_force_refresh
    registry = get_agent_registry()
               ^^^^^^^^^^^^^^^^^^
E   NameError: name 'get_agent_registry' is not defined
```

**Example 3**:
- **nodeid**: `tests.test_agent_registry_cache::test_cache_invalidation`
- **file_hint**: `tests/test_agent_registry_cache.py`

```
Message: NameError: name 'get_agent_registry' is not defined

tests/test_agent_registry_cache.py:134: in test_cache_invalidation
    registry = get_agent_registry()
               ^^^^^^^^^^^^^^^^^^
E   NameError: name 'get_agent_registry' is not defined
```

### Subpattern: `socketio.exceptions.BadNamespaceError: socketio.exceptions.BadNamespaceError: / is not a connected namespace.`
- **Count**: 3
- **Exception**: `socketio.exceptions.BadNamespaceError`

**Example 1**:
- **nodeid**: `tests.dashboard.test_dashboard_fixes::test_file_operations`
- **file_hint**: `tests/dashboard/test_dashboard_fixes.py`

```
Message: socketio.exceptions.BadNamespaceError: / is not a connected namespace.

tests/dashboard/test_dashboard_fixes.py:61: in test_file_operations
    emit_test_event("hook", "pre_tool", tool, file_path)
tests/dashboard/test_dashboard_fixes.py:41: in emit_test_event
    sio.emit("claude_event", event)
.venv/lib/python3.12/site-packages/socketio/client.py:223: in emit
    raise exceptions.BadNamespaceError(
E   socketio.exceptions.BadNamespaceError: / is not a connected namespace.
```

**Example 2**:
- **nodeid**: `tests.dashboard.test_dashboard_fixes::test_tool_operations`
- **file_hint**: `tests/dashboard/test_dashboard_fixes.py`

```
Message: socketio.exceptions.BadNamespaceError: / is not a connected namespace.

tests/dashboard/test_dashboard_fixes.py:92: in test_tool_operations
    event = emit_test_event("hook", "pre_tool", tool, None)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/dashboard/test_dashboard_fixes.py:41: in emit_test_event
    sio.emit("claude_event", event)
.venv/lib/python3.12/site-packages/socketio/client.py:223: in emit
    raise exceptions.BadNamespaceError(
E   socketio.exceptions.BadNamespaceError: / is not a connected namespace.
```

**Example 3**:
- **nodeid**: `tests.dashboard.test_dashboard_fixes::test_agent_events`
- **file_hint**: `tests/dashboard/test_dashboard_fixes.py`

```
Message: socketio.exceptions.BadNamespaceError: / is not a connected namespace.

tests/dashboard/test_dashboard_fixes.py:129: in test_agent_events
    sio.emit("claude_event", event)
.venv/lib/python3.12/site-packages/socketio/client.py:223: in emit
    raise exceptions.BadNamespaceError(
E   socketio.exceptions.BadNamespaceError: / is not a connected namespace.
```

### Subpattern: `claude_mpm.services.version_control.git_operations.GitOperationError: claude_mpm.services.version_control.git_operations`
- **Count**: 3
- **Exception**: `claude_mpm.services.version_control.git_operations.GitOperationError`

**Example 1**:
- **nodeid**: `tests.unit.services.version_control.test_git_operations.TestMergeOperations::test_merge_branch_keeps_source_when_requested`
- **file_hint**: `tests/unit/services/version_control/test_git_operations.py`

```
Message: claude_mpm.services.version_control.git_operations.GitOperationError: Error running Git command:

src/claude_mpm/services/version_control/git_operations.py:229: in _run_git_command
    result = subprocess.run(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1139: in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ... (truncated) ...
tests/unit/services/version_control/test_git_operations.py:632: in test_merge_branch_keeps_source_when_requested
    result = git_manager.merge_branch("feature-branch", "main", delete_source=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:600: in merge_branch
    protection_result = self._enforce_branch_protection(target_branch, "merge")
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:192: in _enforce_branch_protection
    branch_before=self.get_current_branch(),
                  ^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:255: in get_current_branch
    result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:246: in _run_git_command
    raise GitOperationError(f"Error running Git command: {e}") from e
E   claude_mpm.services.version_control.git_operations.GitOperationError: Error running Git command:
```

**Example 2**:
- **nodeid**: `tests.unit.services.version_control.test_git_operations.TestRemoteOperations::test_push_to_remote_success`
- **file_hint**: `tests/unit/services/version_control/test_git_operations.py`

```
Message: claude_mpm.services.version_control.git_operations.GitOperationError: Error running Git command:

src/claude_mpm/services/version_control/git_operations.py:229: in _run_git_command
    result = subprocess.run(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1139: in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ... (truncated) ...
tests/unit/services/version_control/test_git_operations.py:658: in test_push_to_remote_success
    result = git_manager.push_to_remote()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:761: in push_to_remote
    protection_result = self._enforce_branch_protection(branch_name, "push")
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:192: in _enforce_branch_protection
    branch_before=self.get_current_branch(),
                  ^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:255: in get_current_branch
    result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:246: in _run_git_command
    raise GitOperationError(f"Error running Git command: {e}") from e
E   claude_mpm.services.version_control.git_operations.GitOperationError: Error running Git command:
```

**Example 3**:
- **nodeid**: `tests.unit.services.version_control.test_git_operations.TestRemoteOperations::test_push_to_remote_with_upstream`
- **file_hint**: `tests/unit/services/version_control/test_git_operations.py`

```
Message: claude_mpm.services.version_control.git_operations.GitOperationError: Error running Git command:

src/claude_mpm/services/version_control/git_operations.py:229: in _run_git_command
    result = subprocess.run(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1139: in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ... (truncated) ...
tests/unit/services/version_control/test_git_operations.py:673: in test_push_to_remote_with_upstream
    result = git_manager.push_to_remote(set_upstream=True)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:761: in push_to_remote
    protection_result = self._enforce_branch_protection(branch_name, "push")
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:192: in _enforce_branch_protection
    branch_before=self.get_current_branch(),
                  ^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:255: in get_current_branch
    result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/git_operations.py:246: in _run_git_command
    raise GitOperationError(f"Error running Git command: {e}") from e
E   claude_mpm.services.version_control.git_operations.GitOperationError: Error running Git command:
```

### Subpattern: `ProcessLookupError: ProcessLookupError`
- **Count**: 1
- **Exception**: `ProcessLookupError`

**Example 1**:
- **nodeid**: `tests.integration.mcp.test_mcp_client_integration::test_mcp_integration`
- **file_hint**: `tests/integration/mcp/test_mcp_client_integration.py`

```
Message: ProcessLookupError

tests/integration/mcp/test_mcp_client_integration.py:187: in test_mcp_integration
    server_process.terminate()
../../.asdf/installs/python/3.12.11/lib/python3.12/asyncio/subprocess.py:143: in terminate
    self._transport.terminate()
../../.asdf/installs/python/3.12.11/lib/python3.12/asyncio/base_subprocess.py:149: in terminate
    self._check_proc()
../../.asdf/installs/python/3.12.11/lib/python3.12/asyncio/base_subprocess.py:142: in _check_proc
    raise ProcessLookupError()
E   ProcessLookupError
```

## C. Hypotheses

- Miscellaneous errors that do not fit standard categories.
- Custom exception types from project-specific code.
- Multiple error types combined in a single failure.
- The dominant subpattern (`NameError: NameError: name 'Config' is not defined`) accounts for 39/56 failures, suggesting a single root cause.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/dashboard/test_dashboard_fixes.py`
  - `tests/integration/infrastructure/test_activity_logging.py`
  - `tests/integration/infrastructure/test_response_logging.py`
  - `tests/integration/infrastructure/test_response_logging_debug.py`
  - `tests/integration/infrastructure/test_response_logging_edge_cases.py`
  - `tests/integration/mcp/test_mcp_client_integration.py`
  - `tests/test_agent_registry_cache.py`
  - `tests/test_config_duplicate_comprehensive.py`
  - `tests/test_config_duplicate_fix.py`
  - `tests/test_config_duplicate_logging.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where NameError is raised in source code
rg 'raise NameError' src/ --type py

# Find where ProcessLookupError is raised in source code
rg 'raise ProcessLookupError' src/ --type py

# Find where claude_mpm.services.version_control.git_operations.GitOperationError is raised in source code
rg 'raise claude_mpm.services.version_control.git_operations.GitOperationError' src/ --type py

# Key test files to inspect
# tests/integration/infrastructure/test_activity_logging.py
# tests/integration/infrastructure/test_response_logging.py
# tests/integration/infrastructure/test_response_logging_debug.py
# tests/integration/infrastructure/test_response_logging_edge_cases.py
# tests/integration/mcp/test_mcp_client_integration.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/integration/infrastructure/test_activity_logging.py::test_configuration' -x --tb=short
pytest 'tests/integration/infrastructure/test_response_logging.py::test_response_logging' -x --tb=short
pytest 'tests/test_agent_registry_cache.py::test_basic_caching' -x --tb=short
pytest 'tests/test_agent_registry_cache.py::test_force_refresh' -x --tb=short
pytest 'tests/dashboard/test_dashboard_fixes.py::test_file_operations' -x --tb=short
pytest 'tests/dashboard/test_dashboard_fixes.py::test_tool_operations' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_configuration or test_basic_caching or test_file_operations' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **56 test failures** in the `unknown` category (Uncategorized / Unknown Errors).

**Top patterns**:
  - `NameError: NameError: name 'Config' is not defined` (39 occurrences)
  - `NameError: NameError: name 'get_agent_registry' is not defined` (4 occurrences)
  - `socketio.exceptions.BadNamespaceError: socketio.exceptions.BadNamespaceError: / is not a connected n` (3 occurrences)

**Sample failing tests**:
  - `tests.integration.infrastructure.test_activity_logging::test_configuration`
  - `tests.integration.infrastructure.test_response_logging::test_response_logging`
  - `tests.test_agent_registry_cache::test_basic_caching`
  - `tests.test_agent_registry_cache::test_force_refresh`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/unknown.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
