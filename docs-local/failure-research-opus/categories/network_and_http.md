# Network and HTTP Errors

**Category**: `network_and_http`

## A. Snapshot

- **Total failures in this category**: 6
- **Distinct subpatterns**: 3

### Top Exception Types

| Exception Type | Count |
|---|---|
| `claude_mpm.services.exceptions.SocketIOServerError` | 4 |
| `AssertionError` | 1 |
| `RuntimeError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `claude_mpm.services.exceptions.SocketIOServerError: claude_mpm.services.exceptions.SocketIOServerErr...` | 4 |
| 2 | `AssertionError: AssertionError: assert <N> == <N> + where <N> = len([]) + where [] = <claude_mpm.ser...` | 1 |
| 3 | `RuntimeError: RuntimeError: Socket.IO server not available` | 1 |

## B. Representative Examples

### Subpattern: `claude_mpm.services.exceptions.SocketIOServerError: claude_mpm.services.exceptions.SocketIOServerError: Failed to start `
- **Count**: 4
- **Exception**: `claude_mpm.services.exceptions.SocketIOServerError`

**Example 1**:
- **nodeid**: `tests.test_http_event_flow::test_http_event_flow`
- **file_hint**: `tests/test_http_event_flow.py`

```
Message: claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s

tests/test_http_event_flow.py:33: in test_http_event_flow
    server.start_sync()
src/claude_mpm/services/socketio/server/main.py:116: in start_sync
    self.core.start_sync()
src/claude_mpm/services/socketio/server/core.py:190: in start_sync
    raise MPMConnectionError(
E   claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
```

**Example 2**:
- **nodeid**: `tests.test_socketio_broadcast::test_socketio_broadcast`
- **file_hint**: `tests/test_socketio_broadcast.py`

```
Message: claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s

tests/test_socketio_broadcast.py:34: in test_socketio_broadcast
    server.start_sync()
src/claude_mpm/services/socketio/server/main.py:116: in start_sync
    self.core.start_sync()
src/claude_mpm/services/socketio/server/core.py:190: in start_sync
    raise MPMConnectionError(
E   claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
```

**Example 3**:
- **nodeid**: `tests.test_hook_http_integration::test_hook_http_integration`
- **file_hint**: `tests/test_hook_http_integration.py`

```
Message: claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s

tests/test_hook_http_integration.py:31: in test_hook_http_integration
    server.start_sync()
src/claude_mpm/services/socketio/server/main.py:116: in start_sync
    self.core.start_sync()
src/claude_mpm/services/socketio/server/core.py:190: in start_sync
    raise MPMConnectionError(
E   claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
```

### Subpattern: `AssertionError: AssertionError: assert <N> == <N> + where <N> = len([]) + where [] = <claude_mpm.services.socketio.handl`
- **Count**: 1
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.services.test_socketio_handlers.TestIntegration::test_registry_with_all_handlers`
- **file_hint**: `tests/services/test_socketio_handlers.py`

```
Message: AssertionError: assert 0 == 6
 +  where 0 = len([])
 +    where [] = <claude_mpm.services.socketio.handlers.registry.EventHandlerRegistry object at 0x11550edb0>.handlers
 +  and   6 = len([<class 'claude_mpm.services.socketio.handlers.connection.ConnectionEventHandler'>, <class 'claude_mpm.services.

tests/services/test_socketio_handlers.py:917: in test_registry_with_all_handlers
    assert len(registry.handlers) == len(registry.DEFAULT_HANDLERS)
E   AssertionError: assert 0 == 6
E    +  where 0 = len([])
E    +    where [] = <claude_mpm.services.socketio.handlers.registry.EventHandlerRegistry object at 0x11550edb0>.handlers
E    +  and   6 = len([<class 'claude_mpm.services.socketio.handlers.connection.ConnectionEventHandler'>, <class 'claude_mpm.services.socket...etio.handlers.project.ProjectEventHandler'>, <class 'claude_mpm.services.socketio.handlers.memory.MemoryEventHandler'>])
E    +    where [<class 'claude_mpm.services.socketio.handlers.connection.ConnectionEventHandler'>, <class 'claude_mpm.services.socket...etio.handlers.project.ProjectEventHandler'>, <class 'claude_mpm.services.socketio.handlers.memory.MemoryEventHandler'>] = <claude_mpm.services.socketio.handlers.registry.EventHandlerRegistry object at 0x11550edb0>.DEFAULT_HANDLERS
```

### Subpattern: `RuntimeError: RuntimeError: Socket.IO server not available`
- **Count**: 1
- **Exception**: `RuntimeError`

**Example 1**:
- **nodeid**: `tests.services.test_socketio_handlers.TestIntegration::test_end_to_end_file_operations`
- **file_hint**: `tests/services/test_socketio_handlers.py`

```
Message: RuntimeError: Socket.IO server not available

tests/services/test_socketio_handlers.py:941: in test_end_to_end_file_operations
    registry.register_all_events()
src/claude_mpm/services/socketio/handlers/registry.py:133: in register_all_events
    raise RuntimeError("Socket.IO server not available")
E   RuntimeError: Socket.IO server not available
```

## C. Hypotheses

- Tests making real HTTP calls instead of using mocks/fixtures.
- Server not started before integration test execution.
- TLS/SSL certificate issues in test environment.
- Port conflicts or firewall rules blocking test connections.
- The dominant subpattern (`claude_mpm.services.exceptions.SocketIOServerError: claude_mpm.services.exceptio`) accounts for 4/6 failures, suggesting a single root cause.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/services/test_socketio_handlers.py`
  - `tests/test_event_flow.py`
  - `tests/test_hook_http_integration.py`
  - `tests/test_http_event_flow.py`
  - `tests/test_socketio_broadcast.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where AssertionError is raised in source code
rg 'raise AssertionError' src/ --type py

# Find where RuntimeError is raised in source code
rg 'raise RuntimeError' src/ --type py

# Find where claude_mpm.services.exceptions.SocketIOServerError is raised in source code
rg 'raise claude_mpm.services.exceptions.SocketIOServerError' src/ --type py

# Search for 'at' references
rg 'at' src/ --type py -l

# Search for 'claude_mpm' references
rg 'claude_mpm' src/ --type py -l

# Key test files to inspect
# tests/services/test_socketio_handlers.py
# tests/test_event_flow.py
# tests/test_hook_http_integration.py
# tests/test_http_event_flow.py
# tests/test_socketio_broadcast.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/test_http_event_flow.py::test_http_event_flow' -x --tb=short
pytest 'tests/test_socketio_broadcast.py::test_socketio_broadcast' -x --tb=short
pytest 'tests/services/test_socketio_handlers/TestIntegration.py::test_registry_with_all_handlers' -x --tb=short
pytest 'tests/services/test_socketio_handlers/TestIntegration.py::test_end_to_end_file_operations' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_http_event_flow or test_registry_with_all_handlers or test_end_to_end_file_operations' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **6 test failures** in the `network_and_http` category (Network and HTTP Errors).

**Top patterns**:
  - `claude_mpm.services.exceptions.SocketIOServerError: claude_mpm.services.exceptions.SocketIOServerErr` (4 occurrences)
  - `AssertionError: AssertionError: assert <N> == <N> + where <N> = len([]) + where [] = <claude_mpm.ser` (1 occurrences)
  - `RuntimeError: RuntimeError: Socket.IO server not available` (1 occurrences)

**Sample failing tests**:
  - `tests.test_http_event_flow::test_http_event_flow`
  - `tests.test_socketio_broadcast::test_socketio_broadcast`
  - `tests.services.test_socketio_handlers.TestIntegration::test_registry_with_all_handlers`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/network_and_http.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
