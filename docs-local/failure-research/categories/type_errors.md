# Failure Category: type_errors

## A. Snapshot
- **Total failures**: 448
- **Top exception types**:
  - `TypeError`: 448
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `TypeError: unsupported operand type(s) for <path> <str> and <str> \| <unknown>` | 38 |
  | `TypeError: <str> object is not subscriptable \| <unknown>` | 5 |
  | `TypeError: Object of type PosixPath is not JSON serializable \| <unknown>` | 5 |
  | `TypeError: <str> requires string as left operand, not list \| <unknown>` | 3 |
  | `TypeError: Object of type MagicMock is not JSON serializable \| <unknown>` | 3 |
  | `TypeError: cannot unpack non-iterable TestRollbackScenarios object \| <unknown>` | 2 |
  | `TypeError: object of type <str> has no len() \| <unknown>` | 2 |
  | `TypeError: TestCommandResult.test_success_result_creation() takes N positional arguments but N was given \| <unknown>` | 1 |
  | `TypeError: TestCommandResult.test_success_result_with_data() takes N positional arguments but N was given \| <unknown>` | 1 |
  | `TypeError: TestCommandResult.test_error_result_creation() takes N positional arguments but N was given \| <unknown>` | 1 |

## B. Representative Examples

### Subpattern: `TypeError: unsupported operand type(s) for <path> <str> and <str> | <unknown>` (38 failures)

**Example 1**
- **nodeid**: `tests/integration/test_schema_integration.py::TestSchemaIntegration::test_task_tool_with_standardized_agents`
- **file_hint**: `tests/integration/test_schema_integration/TestSchemaIntegration.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: unsupported operand type(s) for /: 'TestSchemaIntegration' and 'str'
--- relevant traceback (up to 30 lines) ---
tests/integration/test_schema_integration.py:70: in test_task_tool_with_standardized_agents
    with open(self / "qa.json") as f:
              ^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestSchemaIntegration' and 'str'
```

**Example 2**
- **nodeid**: `tests/integration/test_schema_integration.py::TestSchemaIntegration::test_cli_with_standardized_agents`
- **file_hint**: `tests/integration/test_schema_integration/TestSchemaIntegration.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: unsupported operand type(s) for /: 'TestSchemaIntegration' and 'str'
--- relevant traceback (up to 30 lines) ---
tests/integration/test_schema_integration.py:110: in test_cli_with_standardized_agents
    test_script = self / "test_cli.py"
                  ^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestSchemaIntegration' and 'str'
```

**Example 3**
- **nodeid**: `tests/integration/test_schema_integration.py::TestSchemaIntegration::test_error_handling_invalid_agents`
- **file_hint**: `tests/integration/test_schema_integration/TestSchemaIntegration.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: unsupported operand type(s) for /: 'TestSchemaIntegration' and 'str'
--- relevant traceback (up to 30 lines) ---
tests/integration/test_schema_integration.py:234: in test_error_handling_invalid_agents
    invalid_path = self / "invalid.json"
                   ^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestSchemaIntegration' and 'str'
```

### Subpattern: `TypeError: <str> object is not subscriptable | <unknown>` (5 failures)

**Example 1**
- **nodeid**: `tests/hooks/claude_hooks/test_hook_handler_state.py::TestSubagentStopProcessing::test_handle_subagent_stop_memory_extraction`
- **file_hint**: `tests/hooks/claude_hooks/test_hook_handler_state/TestSubagentStopProcessing.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: 'NoneType' object is not subscriptable
--- relevant traceback (up to 30 lines) ---
tests/hooks/claude_hooks/test_hook_handler_state.py:222: in test_handle_subagent_stop_memory_extraction
    emitted_data = mock_emit.call_args[0][2]
                   ^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: 'NoneType' object is not subscriptable
```

**Example 2**
- **nodeid**: `tests/hooks/claude_hooks/test_hook_handler_state.py::TestSubagentStopProcessing::test_handle_subagent_stop_agent_type_inference`
- **file_hint**: `tests/hooks/claude_hooks/test_hook_handler_state/TestSubagentStopProcessing.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: 'NoneType' object is not subscriptable
--- relevant traceback (up to 30 lines) ---
tests/hooks/claude_hooks/test_hook_handler_state.py:283: in test_handle_subagent_stop_agent_type_inference
    emitted_data = mock_emit.call_args[0][2]
                   ^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: 'NoneType' object is not subscriptable
```

**Example 3**
- **nodeid**: `tests/services/agents/deployment/test_template_discovery.py::TestTemplateDiscovery::test_get_multi_source_templates`
- **file_hint**: `tests/services/agents/deployment/test_template_discovery/TestTemplateDiscovery.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: 'Mock' object is not subscriptable
--- relevant traceback (up to 30 lines) ---
tests/services/agents/deployment/test_template_discovery.py:50: in test_get_multi_source_templates
    templates, sources, _cleanup = service._get_multi_source_templates(
src/claude_mpm/services/agents/deployment/agent_deployment.py:972: in _get_multi_source_templates
    exclusion_cleanup_results["removed"]
E   TypeError: 'Mock' object is not subscriptable
```

### Subpattern: `TypeError: Object of type PosixPath is not JSON serializable | <unknown>` (5 failures)

**Example 1**
- **nodeid**: `tests/test_hook_installer.py::TestHookInstaller::test_settings_backup_and_restore`
- **file_hint**: `tests/test_hook_installer/TestHookInstaller.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: Object of type PosixPath is not JSON serializable
--- relevant traceback (up to 30 lines) ---
    self.installer._update_claude_settings(script_path)
src/claude_mpm/hooks/claude_hooks/installer.py:824: in _update_claude_settings
    json.dump(settings, f, indent=2)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/__init__.py:179: in dump
    for chunk in iterable:
                 ^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:432: in _iterencode
    yield from _iterencode_dict(o, _current_indent_level)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:326: in _iterencode_list
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:326: in _iterencode_list
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:439: in _iterencode
    o = _default(o)
        ^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:180: in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
E   TypeError: Object of type PosixPath is not JSON serializable
```

**Example 2**
- **nodeid**: `tests/test_hook_installer.py::TestHookInstaller::test_update_claude_settings_existing_file`
- **file_hint**: `tests/test_hook_installer/TestHookInstaller.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: Object of type PosixPath is not JSON serializable
--- relevant traceback (up to 30 lines) ---
    self.installer._update_claude_settings(script_path)
src/claude_mpm/hooks/claude_hooks/installer.py:824: in _update_claude_settings
    json.dump(settings, f, indent=2)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/__init__.py:179: in dump
    for chunk in iterable:
                 ^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:432: in _iterencode
    yield from _iterencode_dict(o, _current_indent_level)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:326: in _iterencode_list
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:326: in _iterencode_list
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:439: in _iterencode
    o = _default(o)
        ^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:180: in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
E   TypeError: Object of type PosixPath is not JSON serializable
```

**Example 3**
- **nodeid**: `tests/test_hook_installer.py::TestHookInstaller::test_update_claude_settings_new_file`
- **file_hint**: `tests/test_hook_installer/TestHookInstaller.py`
- **failure**:
```
exc_type: TypeError
message: TypeError: Object of type PosixPath is not JSON serializable
--- relevant traceback (up to 30 lines) ---
    self.installer._update_claude_settings(script_path)
src/claude_mpm/hooks/claude_hooks/installer.py:824: in _update_claude_settings
    json.dump(settings, f, indent=2)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/__init__.py:179: in dump
    for chunk in iterable:
                 ^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:432: in _iterencode
    yield from _iterencode_dict(o, _current_indent_level)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:326: in _iterencode_list
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:326: in _iterencode_list
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:406: in _iterencode_dict
    yield from chunks
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:439: in _iterencode
    o = _default(o)
        ^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/json/encoder.py:180: in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
E   TypeError: Object of type PosixPath is not JSON serializable
```

## C. Hypotheses

- API signature changed (parameter added/removed/renamed).
- Wrong type passed due to missing coercion after refactor.
- None returned where object expected, propagating downstream.
- Mocked object missing attribute/method expected by code.
- Incompatible types between Python 3.x minor versions.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Check function signatures for recently changed parameters.
- [ ] Verify mock objects have same interface as the real class.
- [ ] Search for `None` returns where an object was expected.

## E. Targeted Repo Queries

```bash
rg "def .*\(.*\)" src/ --include="*.py" | head -50
rg "TypeError" tests/ --include="*.py"
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/integration/test_schema_integration.py::TestSchemaIntegration::test_task_tool_with_standardized_agents" -xvs

# Run small set for this bucket
pytest -k 'type' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the type_errors bucket:
  tests/integration/test_schema_integration.py::TestSchemaIntegration::test_task_tool_with_standardized_agents
  tests/hooks/claude_hooks/test_hook_handler_state.py::TestSubagentStopProcessing::test_handle_subagent_stop_memory_extraction
  tests/test_hook_installer.py::TestHookInstaller::test_settings_backup_and_restore

And these relevant source files:
  tests/integration/test_schema_integration/TestSchemaIntegration.py
  tests/hooks/claude_hooks/test_hook_handler_state/TestSubagentStopProcessing.py
  tests/test_hook_installer/TestHookInstaller.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
