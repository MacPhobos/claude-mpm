# Attribute Errors

**Category**: `attribute_errors`

## A. Snapshot

- **Total failures in this category**: 448
- **Distinct subpatterns**: 171

### Top Exception Types

| Exception Type | Count |
|---|---|
| `AttributeError` | 447 |
| `json.decoder.JSONDecodeError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `AttributeError: AttributeError: module 'claude_mpm' has no attribute 'mcp'` | 42 |
| 2 | `AttributeError: AttributeError: type object 'HealthStatus' has no attribute 'WARNING'` | 10 |
| 3 | `AttributeError: AttributeError: <module '<LONG_STR>' from '<PATH>'<LONG_STR>'PID_FILE'` | 10 |
| 4 | `AttributeError: AttributeError: 'TestEventHandlerRegistry' object has no attribute 'initialize'` | 9 |
| 5 | `AttributeError: AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployme...` | 9 |
| 6 | `AttributeError: AttributeError: 'TestAgentConfigurationManager' object has no attribute 'get_agent_t...` | 8 |
| 7 | `AttributeError: AttributeError: 'TestGitEventHandler' object has no attribute 'sio'` | 7 |
| 8 | `AttributeError: AttributeError: property 'project_root' of 'ClaudeMPMPaths' object has no deleter` | 7 |
| 9 | `AttributeError: AttributeError: 'TestConnectionEventHandler' object has no attribute 'sio'` | 6 |
| 10 | `AttributeError: AttributeError: 'TestAgentConfigurationManager' object has no attribute 'get_agent_s...` | 6 |
| 11 | `AttributeError: AttributeError: <module '<LONG_STR>' from '<PATH>'<LONG_STR>'logger` | 6 |
| 12 | `AttributeError: AttributeError: 'TestAdvancedHealthMonitor' object has no attribute 'get'` | 6 |
| 13 | `AttributeError: AttributeError: 'TestSchemaStandardization' object has no attribute '_validate_agent...` | 6 |
| 14 | `AttributeError: AttributeError: 'TestAgentCapabilitiesService' object has no attribute '_discover_ag...` | 5 |
| 15 | `AttributeError: AttributeError: type object 'HealthStatus' has no attribute 'CRITICAL'` | 5 |

## B. Representative Examples

### Subpattern: `AttributeError: AttributeError: module 'claude_mpm' has no attribute 'mcp'`
- **Count**: 42
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.mcp.test_session_manager.TestStartSession::test_creates_session_and_returns_result`
- **file_hint**: `tests/mcp/test_session_manager.py`

```
Message: AttributeError: module 'claude_mpm' has no attribute 'mcp'

tests/mcp/test_session_manager.py:76: in test_creates_session_and_returns_result
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1451: in __enter__
    self.target = self.getter()
                  ^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pkgutil.py:528: in resolve_name
    result = getattr(result, p)
             ^^^^^^^^^^^^^^^^^^
src/claude_mpm/__init__.py:57: in __getattr__
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
E   AttributeError: module 'claude_mpm' has no attribute 'mcp'
```

**Example 2**:
- **nodeid**: `tests.mcp.test_session_manager.TestStartSession::test_tracks_session`
- **file_hint**: `tests/mcp/test_session_manager.py`

```
Message: AttributeError: module 'claude_mpm' has no attribute 'mcp'

tests/mcp/test_session_manager.py:106: in test_tracks_session
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1451: in __enter__
    self.target = self.getter()
                  ^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pkgutil.py:528: in resolve_name
    result = getattr(result, p)
             ^^^^^^^^^^^^^^^^^^
src/claude_mpm/__init__.py:57: in __getattr__
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
E   AttributeError: module 'claude_mpm' has no attribute 'mcp'
```

**Example 3**:
- **nodeid**: `tests.mcp.test_session_manager.TestStartSession::test_session_status_transitions`
- **file_hint**: `tests/mcp/test_session_manager.py`

```
Message: AttributeError: module 'claude_mpm' has no attribute 'mcp'

tests/mcp/test_session_manager.py:138: in test_session_status_transitions
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1451: in __enter__
    self.target = self.getter()
                  ^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pkgutil.py:528: in resolve_name
    result = getattr(result, p)
             ^^^^^^^^^^^^^^^^^^
src/claude_mpm/__init__.py:57: in __getattr__
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
E   AttributeError: module 'claude_mpm' has no attribute 'mcp'
```

### Subpattern: `AttributeError: AttributeError: type object 'HealthStatus' has no attribute 'WARNING'`
- **Count**: 10
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.services.test_monitoring_refactored.TestIntegration::test_full_monitoring_cycle`
- **file_hint**: `tests/services/test_monitoring_refactored.py`

```
Message: AttributeError: type object 'HealthStatus' has no attribute 'WARNING'

tests/services/test_monitoring_refactored.py:685: in test_full_monitoring_cycle
    assert result.overall_status in [HealthStatus.HEALTHY, HealthStatus.WARNING]
                                                           ^^^^^^^^^^^^^^^^^^^^
E   AttributeError: type object 'HealthStatus' has no attribute 'WARNING'
```

**Example 2**:
- **nodeid**: `tests.services.test_monitoring_refactored.TestHealthMetric::test_health_metric_to_dict`
- **file_hint**: `tests/services/test_monitoring_refactored.py`

```
Message: AttributeError: type object 'HealthStatus' has no attribute 'WARNING'

tests/services/test_monitoring_refactored.py:56: in test_health_metric_to_dict
    status=HealthStatus.WARNING,
           ^^^^^^^^^^^^^^^^^^^^
E   AttributeError: type object 'HealthStatus' has no attribute 'WARNING'
```

**Example 3**:
- **nodeid**: `tests.services.test_monitoring_refactored.TestHealthCheckResult::test_health_check_result_creation`
- **file_hint**: `tests/services/test_monitoring_refactored.py`

```
Message: AttributeError: type object 'HealthStatus' has no attribute 'WARNING'

tests/services/test_monitoring_refactored.py:76: in test_health_check_result_creation
    HealthMetric("metric2", 20, HealthStatus.WARNING),
                                ^^^^^^^^^^^^^^^^^^^^
E   AttributeError: type object 'HealthStatus' has no attribute 'WARNING'
```

### Subpattern: `AttributeError: AttributeError: <module '<LONG_STR>' from '<PATH>'<LONG_STR>'PID_FILE'`
- **Count**: 10
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.test_socketio_daemon.TestDaemonProcessManagement::test_daemon_start_when_not_running`
- **file_hint**: `tests/test_socketio_daemon.py`

```
Message: AttributeError: <module 'claude_mpm.scripts.socketio_daemon' from '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py'> does not have the attribute 'PID_FILE'

tests/test_socketio_daemon.py:50: in test_daemon_start_when_not_running
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1467: in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1437: in get_original
    raise AttributeError(
E   AttributeError: <module 'claude_mpm.scripts.socketio_daemon' from '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py'> does not have the attribute 'PID_FILE'
```

**Example 2**:
- **nodeid**: `tests.test_socketio_daemon.TestDaemonProcessManagement::test_daemon_start_when_already_running`
- **file_hint**: `tests/test_socketio_daemon.py`

```
Message: AttributeError: <module 'claude_mpm.scripts.socketio_daemon' from '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py'> does not have the attribute 'PID_FILE'

tests/test_socketio_daemon.py:88: in test_daemon_start_when_already_running
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1467: in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1437: in get_original
    raise AttributeError(
E   AttributeError: <module 'claude_mpm.scripts.socketio_daemon' from '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py'> does not have the attribute 'PID_FILE'
```

**Example 3**:
- **nodeid**: `tests.test_socketio_daemon.TestDaemonProcessManagement::test_daemon_stop_when_running`
- **file_hint**: `tests/test_socketio_daemon.py`

```
Message: AttributeError: <module 'claude_mpm.scripts.socketio_daemon' from '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py'> does not have the attribute 'PID_FILE'

tests/test_socketio_daemon.py:110: in test_daemon_stop_when_running
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1467: in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1437: in get_original
    raise AttributeError(
E   AttributeError: <module 'claude_mpm.scripts.socketio_daemon' from '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/scripts/socketio_daemon.py'> does not have the attribute 'PID_FILE'
```

### Subpattern: `AttributeError: AttributeError: 'TestEventHandlerRegistry' object has no attribute 'initialize'`
- **Count**: 9
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.services.test_socketio_handlers.TestEventHandlerRegistry::test_initialize_default_handlers`
- **file_hint**: `tests/services/test_socketio_handlers.py`

```
Message: AttributeError: 'TestEventHandlerRegistry' object has no attribute 'initialize'

tests/services/test_socketio_handlers.py:788: in test_initialize_default_handlers
    self.initialize()
    ^^^^^^^^^^^^^^^
E   AttributeError: 'TestEventHandlerRegistry' object has no attribute 'initialize'
```

**Example 2**:
- **nodeid**: `tests.services.test_socketio_handlers.TestEventHandlerRegistry::test_initialize_custom_handlers`
- **file_hint**: `tests/services/test_socketio_handlers.py`

```
Message: AttributeError: 'TestEventHandlerRegistry' object has no attribute 'initialize'

tests/services/test_socketio_handlers.py:802: in test_initialize_custom_handlers
    self.initialize(handler_classes=custom_handlers)
    ^^^^^^^^^^^^^^^
E   AttributeError: 'TestEventHandlerRegistry' object has no attribute 'initialize'
```

**Example 3**:
- **nodeid**: `tests.services.test_socketio_handlers.TestEventHandlerRegistry::test_initialize_already_initialized`
- **file_hint**: `tests/services/test_socketio_handlers.py`

```
Message: AttributeError: 'TestEventHandlerRegistry' object has no attribute 'initialize'

tests/services/test_socketio_handlers.py:813: in test_initialize_already_initialized
    self.initialize()
    ^^^^^^^^^^^^^^^
E   AttributeError: 'TestEventHandlerRegistry' object has no attribute 'initialize'
```

### Subpattern: `AttributeError: AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployment_metrics'`
- **Count**: 9
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.test_agent_metrics_collector.TestAgentMetricsCollector::test_update_deployment_metrics_success`
- **file_hint**: `tests/test_agent_metrics_collector.py`

```
Message: AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployment_metrics'

tests/test_agent_metrics_collector.py:46: in test_update_deployment_metrics_success
    self.update_deployment_metrics(150.5, results)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployment_metrics'
```

**Example 2**:
- **nodeid**: `tests.test_agent_metrics_collector.TestAgentMetricsCollector::test_update_deployment_metrics_failure`
- **file_hint**: `tests/test_agent_metrics_collector.py`

```
Message: AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployment_metrics'

tests/test_agent_metrics_collector.py:67: in test_update_deployment_metrics_failure
    self.update_deployment_metrics(75.0, results)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployment_metrics'
```

**Example 3**:
- **nodeid**: `tests.test_agent_metrics_collector.TestAgentMetricsCollector::test_rolling_average_calculation`
- **file_hint**: `tests/test_agent_metrics_collector.py`

```
Message: AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployment_metrics'

tests/test_agent_metrics_collector.py:97: in test_rolling_average_calculation
    self.update_deployment_metrics(100.0 + i * 10, results)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployment_metrics'
```

## C. Hypotheses

- Class/module API changes (renamed or removed attributes/methods).
- Mock objects missing expected attributes.
- Incorrect object types returned from factories or fixtures.
- Dynamic attribute access on objects that changed shape.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Search for renamed or removed class attributes
- [ ] Check module `__init__.py` exports
- [ ] Verify mock specs match current class interfaces
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/integration/test_schema_integration.py`
  - `tests/mcp/test_session_manager.py`
  - `tests/mcp/test_session_server_http.py`
  - `tests/services/agents/test_auto_config_manager.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where AttributeError is raised in source code
rg 'raise AttributeError' src/ --type py

# Search for 'mcp' references
rg 'mcp' src/ --type py -l

# Search for 'HealthStatus' references
rg 'HealthStatus' src/ --type py -l

# Search for 'WARNING' references
rg 'WARNING' src/ --type py -l

# Key test files to inspect
# tests/integration/test_schema_integration.py
# tests/mcp/test_session_manager.py
# tests/mcp/test_session_server_http.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/mcp/test_session_manager/TestStartSession.py::test_creates_session_and_returns_result' -x --tb=short
pytest 'tests/mcp/test_session_manager/TestStartSession.py::test_tracks_session' -x --tb=short
pytest 'tests/services/test_monitoring_refactored/TestIntegration.py::test_full_monitoring_cycle' -x --tb=short
pytest 'tests/services/test_monitoring_refactored/TestHealthMetric.py::test_health_metric_to_dict' -x --tb=short
pytest 'tests/test_socketio_daemon/TestDaemonProcessManagement.py::test_daemon_start_when_not_running' -x --tb=short
pytest 'tests/test_socketio_daemon/TestDaemonProcessManagement.py::test_daemon_start_when_already_running' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_creates_session_and_returns_result or test_full_monitoring_cycle or test_daemon_start_when_not_running' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **448 test failures** in the `attribute_errors` category (Attribute Errors).

**Top patterns**:
  - `AttributeError: AttributeError: module 'claude_mpm' has no attribute 'mcp'` (42 occurrences)
  - `AttributeError: AttributeError: type object 'HealthStatus' has no attribute 'WARNING'` (10 occurrences)
  - `AttributeError: AttributeError: <module '<LONG_STR>' from '<PATH>'<LONG_STR>'PID_FILE'` (10 occurrences)

**Sample failing tests**:
  - `tests.mcp.test_session_manager.TestStartSession::test_creates_session_and_returns_result`
  - `tests.mcp.test_session_manager.TestStartSession::test_tracks_session`
  - `tests.services.test_monitoring_refactored.TestIntegration::test_full_monitoring_cycle`
  - `tests.services.test_monitoring_refactored.TestHealthMetric::test_health_metric_to_dict`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/attribute_errors.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
