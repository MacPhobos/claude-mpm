# Not Implemented Errors

**Category**: `not_implemented`

## A. Snapshot

- **Total failures in this category**: 1
- **Distinct subpatterns**: 1

### Top Exception Types

| Exception Type | Count |
|---|---|
| `NotImplementedError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `NotImplementedError: NotImplementedError: No events to register` | 1 |

## B. Representative Examples

### Subpattern: `NotImplementedError: NotImplementedError: No events to register`
- **Count**: 1
- **Exception**: `NotImplementedError`

**Example 1**:
- **nodeid**: `tests.socketio.test_event_handler_registry.TestEventHandlerRegistry::test_add_handler_after_initialization`
- **file_hint**: `tests/socketio/test_event_handler_registry.py`

```
Message: NotImplementedError: No events to register

tests/socketio/test_event_handler_registry.py:238: in test_add_handler_after_initialization
    registry.add_handler(MockNoEventsHandler)
src/claude_mpm/services/socketio/handlers/registry.py:193: in add_handler
    handler.register_events()
tests/socketio/test_event_handler_registry.py:55: in register_events
    raise NotImplementedError("No events to register")
E   NotImplementedError: No events to register
```

## C. Hypotheses

- Stub methods not yet implemented being called by tests.
- Abstract methods missing implementations in concrete subclasses.
- Feature flags toggling off implementations that tests expect.
- The dominant subpattern (`NotImplementedError: NotImplementedError: No events to register`) accounts for 1/1 failures, suggesting a single root cause.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/socketio/test_event_handler_registry.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where NotImplementedError is raised in source code
rg 'raise NotImplementedError' src/ --type py

# Key test files to inspect
# tests/socketio/test_event_handler_registry.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/socketio/test_event_handler_registry/TestEventHandlerRegistry.py::test_add_handler_after_initialization' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_add_handler_after_initialization' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **1 test failures** in the `not_implemented` category (Not Implemented Errors).

**Top patterns**:
  - `NotImplementedError: NotImplementedError: No events to register` (1 occurrences)

**Sample failing tests**:
  - `tests.socketio.test_event_handler_registry.TestEventHandlerRegistry::test_add_handler_after_initialization`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/not_implemented.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
