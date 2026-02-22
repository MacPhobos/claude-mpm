# Failure Category: network_and_http

## A. Snapshot
- **Total failures**: 4
- **Top exception types**:
  - `SocketIOServerError`: 4
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s \| <unknown>` | 4 |

## B. Representative Examples

### Subpattern: `claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s | <unknown>` (4 failures)

**Example 1**
- **nodeid**: `tests/test_http_event_flow.py::test_http_event_flow`
- **file_hint**: `tests/test_http_event_flow.py`
- **failure**:
```
exc_type: SocketIOServerError
message: claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
--- relevant traceback (up to 30 lines) ---
tests/test_http_event_flow.py:33: in test_http_event_flow
    server.start_sync()
src/claude_mpm/services/socketio/server/main.py:116: in start_sync
    self.core.start_sync()
src/claude_mpm/services/socketio/server/core.py:190: in start_sync
    raise MPMConnectionError(
E   claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
```

**Example 2**
- **nodeid**: `tests/test_socketio_broadcast.py::test_socketio_broadcast`
- **file_hint**: `tests/test_socketio_broadcast.py`
- **failure**:
```
exc_type: SocketIOServerError
message: claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
--- relevant traceback (up to 30 lines) ---
tests/test_socketio_broadcast.py:34: in test_socketio_broadcast
    server.start_sync()
src/claude_mpm/services/socketio/server/main.py:116: in start_sync
    self.core.start_sync()
src/claude_mpm/services/socketio/server/core.py:190: in start_sync
    raise MPMConnectionError(
E   claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
```

**Example 3**
- **nodeid**: `tests/test_hook_http_integration.py::test_hook_http_integration`
- **file_hint**: `tests/test_hook_http_integration.py`
- **failure**:
```
exc_type: SocketIOServerError
message: claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
--- relevant traceback (up to 30 lines) ---
tests/test_hook_http_integration.py:31: in test_hook_http_integration
    server.start_sync()
src/claude_mpm/services/socketio/server/main.py:116: in start_sync
    self.core.start_sync()
src/claude_mpm/services/socketio/server/core.py:190: in start_sync
    raise MPMConnectionError(
E   claude_mpm.services.exceptions.SocketIOServerError: Failed to start Socket.IO server within 30s
```

## C. Hypotheses

- External service not mocked in test environment.
- TLS/SSL certificate validation failing in CI.
- Service port not bound yet when test runs (race condition).
- Proxy or firewall blocking outbound connections in CI.
- Incorrect base URL configured for test environment.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Check if external HTTP calls are mocked via `responses`, `httpretty`, or `aioresponses`.
- [ ] Verify `pytest-httpserver` or similar is configured for service mocking.
- [ ] Check if CI has outbound internet access for the required endpoints.

## E. Targeted Repo Queries

```bash
rg "requests\.get|httpx\.get|aiohttp" src/ --include="*.py"
rg "mock_responses|responses\.activate|patch.*requests" tests/ --include="*.py"
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/test_http_event_flow.py::test_http_event_flow" -xvs

# Run small set for this bucket
pytest -k 'http or request or network' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the network_and_http bucket:
  tests/test_http_event_flow.py::test_http_event_flow

And these relevant source files:
  tests/test_http_event_flow.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
