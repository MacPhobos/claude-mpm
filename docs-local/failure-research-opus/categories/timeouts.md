# Timeout Errors

**Category**: `timeouts`

## A. Snapshot

- **Total failures in this category**: 7
- **Distinct subpatterns**: 7

### Top Exception Types

| Exception Type | Count |
|---|---|
| `TypeError` | 4 |
| `AssertionError` | 2 |
| `AttributeError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `AttributeError: AttributeError: module 'claude_mpm' has no attribute 'mcp'` | 1 |
| 2 | `TypeError: TypeError: TestMCPServerSecurity.test_run_command_timeout_protection() takes <N> position...` | 1 |
| 3 | `TypeError: TypeError: TestSubprocessSecurity.test_run_command_timeout_protection() takes <N> positio...` | 1 |
| 4 | `TypeError: TypeError: TestCircuitBreaker.test_circuit_breaker_timeout_transition() takes <N> positio...` | 1 |
| 5 | `TypeError: TypeError: TestSocketIOStartupTimingFix.test_health_check_timeout_behavior() takes <N> po...` | 1 |
| 6 | `AssertionError: AssertionError: assert None == <N> + where None = get('api.timeout') + where get = <...` | 1 |
| 7 | `AssertionError: AssertionError: assert <N> == <N> + where <N> = SocketIOConfig(host='localhost'<LONG...` | 1 |

## B. Representative Examples

### Subpattern: `AttributeError: AttributeError: module 'claude_mpm' has no attribute 'mcp'`
- **Count**: 1
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.mcp.test_session_server_http.TestSessionServerHTTPCLIParsing::test_timeout_argument`
- **file_hint**: `tests/mcp/test_session_server_http.py`

```
Message: AttributeError: module 'claude_mpm' has no attribute 'mcp'

tests/mcp/test_session_server_http.py:624: in test_timeout_argument
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

### Subpattern: `TypeError: TypeError: TestMCPServerSecurity.test_run_command_timeout_protection() takes <N> positional arguments but <N>`
- **Count**: 1
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.security.test_mcp_server_security.TestMCPServerSecurity::test_run_command_timeout_protection`
- **file_hint**: `tests/security/test_mcp_server_security/TestMCPServerSecurity.py`

```
Message: TypeError: TestMCPServerSecurity.test_run_command_timeout_protection() takes 0 positional arguments but 1 was given

.venv/lib/python3.12/site-packages/pytest_asyncio/plugin.py:469: in runtest
    super().runtest()
.venv/lib/python3.12/site-packages/pytest_asyncio/plugin.py:715: in inner
    coro = func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
E   TypeError: TestMCPServerSecurity.test_run_command_timeout_protection() takes 0 positional arguments but 1 was given
```

### Subpattern: `TypeError: TypeError: TestSubprocessSecurity.test_run_command_timeout_protection() takes <N> positional arguments but <N`
- **Count**: 1
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.security.test_subprocess_security.TestSubprocessSecurity::test_run_command_timeout_protection`
- **file_hint**: `tests/security/test_subprocess_security/TestSubprocessSecurity.py`

```
Message: TypeError: TestSubprocessSecurity.test_run_command_timeout_protection() takes 0 positional arguments but 1 was given

.venv/lib/python3.12/site-packages/_pytest/runner.py:353: in from_call
    result: TResult | None = func()
                             ^^^^^^
.venv/lib/python3.12/site-packages/_pytest/runner.py:245: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
    ... (truncated) ...
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/pluggy/_callers.py:53: in run_old_style_hookwrapper
    return result.get_result()
           ^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/pluggy/_callers.py:38: in run_old_style_hookwrapper
    res = yield
          ^^^^^
.venv/lib/python3.12/site-packages/_pytest/python.py:166: in pytest_pyfunc_call
    result = testfunction(**testargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: TestSubprocessSecurity.test_run_command_timeout_protection() takes 0 positional arguments but 1 was given
```

### Subpattern: `TypeError: TypeError: TestCircuitBreaker.test_circuit_breaker_timeout_transition() takes <N> positional arguments but <N`
- **Count**: 1
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.test_health_monitoring_comprehensive.TestCircuitBreaker::test_circuit_breaker_timeout_transition`
- **file_hint**: `tests/test_health_monitoring_comprehensive/TestCircuitBreaker.py`

```
Message: TypeError: TestCircuitBreaker.test_circuit_breaker_timeout_transition() takes 0 positional arguments but 1 was given

.venv/lib/python3.12/site-packages/_pytest/runner.py:353: in from_call
    result: TResult | None = func()
                             ^^^^^^
.venv/lib/python3.12/site-packages/_pytest/runner.py:245: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
    ... (truncated) ...
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/pluggy/_callers.py:53: in run_old_style_hookwrapper
    return result.get_result()
           ^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/pluggy/_callers.py:38: in run_old_style_hookwrapper
    res = yield
          ^^^^^
.venv/lib/python3.12/site-packages/_pytest/python.py:166: in pytest_pyfunc_call
    result = testfunction(**testargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: TestCircuitBreaker.test_circuit_breaker_timeout_transition() takes 0 positional arguments but 1 was given
```

### Subpattern: `TypeError: TypeError: TestSocketIOStartupTimingFix.test_health_check_timeout_behavior() takes <N> positional arguments b`
- **Count**: 1
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.test_socketio_startup_timing_fix.TestSocketIOStartupTimingFix::test_health_check_timeout_behavior`
- **file_hint**: `tests/test_socketio_startup_timing_fix/TestSocketIOStartupTimingFix.py`

```
Message: TypeError: TestSocketIOStartupTimingFix.test_health_check_timeout_behavior() takes 2 positional arguments but 3 were given

../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1396: in patched
    return func(*newargs, **newkeywargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: TestSocketIOStartupTimingFix.test_health_check_timeout_behavior() takes 2 positional arguments but 3 were given
```

## C. Hypotheses

- Async operations not properly awaited or missing event loop.
- Network calls hitting real endpoints instead of mocks.
- Deadlocks in concurrent test execution.
- Resource-constrained CI environment causing slow operations.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/mcp/test_session_server_http.py`
  - `tests/security/test_mcp_server_security/TestMCPServerSecurity.py`
  - `tests/security/test_subprocess_security/TestSubprocessSecurity.py`
  - `tests/socketio/test_socketio_configuration.py`
  - `tests/test_health_monitoring_comprehensive/TestCircuitBreaker.py`
  - `tests/test_socketio_startup_timing_fix/TestSocketIOStartupTimingFix.py`
  - `tests/test_unified_config.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where AttributeError is raised in source code
rg 'raise AttributeError' src/ --type py

# Find where TypeError is raised in source code
rg 'raise TypeError' src/ --type py

# Search for 'mcp' references
rg 'mcp' src/ --type py -l

# Key test files to inspect
# tests/mcp/test_session_server_http.py
# tests/security/test_mcp_server_security/TestMCPServerSecurity.py
# tests/security/test_subprocess_security/TestSubprocessSecurity.py
# tests/socketio/test_socketio_configuration.py
# tests/test_health_monitoring_comprehensive/TestCircuitBreaker.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/mcp/test_session_server_http/TestSessionServerHTTPCLIParsing.py::test_timeout_argument' -x --tb=short
pytest 'tests/security/test_mcp_server_security/TestMCPServerSecurity.py::test_run_command_timeout_protection' -x --tb=short
pytest 'tests/security/test_subprocess_security/TestSubprocessSecurity.py::test_run_command_timeout_protection' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_timeout_argument or test_run_command_timeout_protection or test_run_command_timeout_protection' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **7 test failures** in the `timeouts` category (Timeout Errors).

**Top patterns**:
  - `AttributeError: AttributeError: module 'claude_mpm' has no attribute 'mcp'` (1 occurrences)
  - `TypeError: TypeError: TestMCPServerSecurity.test_run_command_timeout_protection() takes <N> position` (1 occurrences)
  - `TypeError: TypeError: TestSubprocessSecurity.test_run_command_timeout_protection() takes <N> positio` (1 occurrences)

**Sample failing tests**:
  - `tests.mcp.test_session_server_http.TestSessionServerHTTPCLIParsing::test_timeout_argument`
  - `tests.security.test_mcp_server_security.TestMCPServerSecurity::test_run_command_timeout_protection`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/timeouts.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
