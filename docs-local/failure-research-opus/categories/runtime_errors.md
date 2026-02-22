# Runtime Errors

**Category**: `runtime_errors`

## A. Snapshot

- **Total failures in this category**: 3
- **Distinct subpatterns**: 1

### Top Exception Types

| Exception Type | Count |
|---|---|
| `RuntimeError` | 3 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `RuntimeError: RuntimeError: There is no current event loop in thread 'MainThread'.` | 3 |

## B. Representative Examples

### Subpattern: `RuntimeError: RuntimeError: There is no current event loop in thread 'MainThread'.`
- **Count**: 3
- **Exception**: `RuntimeError`

**Example 1**:
- **nodeid**: `tests.services.agents.test_auto_config_manager::test_preview_configuration_success`
- **file_hint**: `tests/services/agents/test_auto_config_manager.py`

```
Message: RuntimeError: There is no current event loop in thread 'MainThread'.

tests/services/agents/test_auto_config_manager.py:493: in test_preview_configuration_success
    preview = service.preview_configuration(temp_project_dir, min_confidence=0.8)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/auto_config_manager.py:534: in preview_configuration
    loop = asyncio.get_event_loop()
           ^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/asyncio/events.py:702: in get_event_loop
    raise RuntimeError('There is no current event loop in thread %r.'
E   RuntimeError: There is no current event loop in thread 'MainThread'.
```

**Example 2**:
- **nodeid**: `tests.services.agents.test_auto_config_manager::test_preview_configuration_with_low_confidence`
- **file_hint**: `tests/services/agents/test_auto_config_manager.py`

```
Message: RuntimeError: There is no current event loop in thread 'MainThread'.

tests/services/agents/test_auto_config_manager.py:504: in test_preview_configuration_with_low_confidence
    preview = service.preview_configuration(temp_project_dir, min_confidence=0.90)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/auto_config_manager.py:534: in preview_configuration
    loop = asyncio.get_event_loop()
           ^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/asyncio/events.py:702: in get_event_loop
    raise RuntimeError('There is no current event loop in thread %r.'
E   RuntimeError: There is no current event loop in thread 'MainThread'.
```

**Example 3**:
- **nodeid**: `tests.services.agents.test_auto_config_manager::test_preview_configuration_includes_validation`
- **file_hint**: `tests/services/agents/test_auto_config_manager.py`

```
Message: RuntimeError: There is no current event loop in thread 'MainThread'.

tests/services/agents/test_auto_config_manager.py:520: in test_preview_configuration_includes_validation
    preview = service.preview_configuration(temp_project_dir)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/auto_config_manager.py:534: in preview_configuration
    loop = asyncio.get_event_loop()
           ^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/asyncio/events.py:702: in get_event_loop
    raise RuntimeError('There is no current event loop in thread %r.'
E   RuntimeError: There is no current event loop in thread 'MainThread'.
```

## C. Hypotheses

- Async event loop issues (already running, not running, wrong type).
- Resource exhaustion or thread safety issues.
- Logic errors in production code surfacing as RuntimeError.
- The dominant subpattern (`RuntimeError: RuntimeError: There is no current event loop in thread 'MainThread`) accounts for 3/3 failures, suggesting a single root cause.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/services/agents/test_auto_config_manager.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where RuntimeError is raised in source code
rg 'raise RuntimeError' src/ --type py

# Key test files to inspect
# tests/services/agents/test_auto_config_manager.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/services/agents/test_auto_config_manager.py::test_preview_configuration_success' -x --tb=short
pytest 'tests/services/agents/test_auto_config_manager.py::test_preview_configuration_with_low_confidence' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_preview_configuration_success' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **3 test failures** in the `runtime_errors` category (Runtime Errors).

**Top patterns**:
  - `RuntimeError: RuntimeError: There is no current event loop in thread 'MainThread'.` (3 occurrences)

**Sample failing tests**:
  - `tests.services.agents.test_auto_config_manager::test_preview_configuration_success`
  - `tests.services.agents.test_auto_config_manager::test_preview_configuration_with_low_confidence`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/runtime_errors.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
