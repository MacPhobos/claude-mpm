# Failure Category: value_errors

## A. Snapshot
- **Total failures**: 12
- **Top exception types**:
  - `ValueError`: 12
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `ValueError: Markdown template missing YAML frontmatter: <path> \| <unknown>` | 10 |
  | `ValueError: Invalid isoformat string: <str> \| <unknown>` | 1 |
  | `ValueError: a coroutine was expected, got <MagicMock name=<str> id=<str>> \| <unknown>` | 1 |

## B. Representative Examples

### Subpattern: `ValueError: Markdown template missing YAML frontmatter: <path> | <unknown>` (10 failures)

**Example 1**
- **nodeid**: `tests/integration/test_non_compliant_repo_compatibility.py::TestNonCompliantRepositoryCompatibility::test_simple_agent_without_any_base_templates`
- **file_hint**: `tests/integration/test_non_compliant_repo_compatibility/TestNonCompliantRepositoryCompatibility.py`
- **failure**:
```
exc_type: ValueError
message: ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmp52za3ndj/agents/engineer.md
--- relevant traceback (up to 30 lines) ---
tests/integration/test_non_compliant_repo_compatibility.py:68: in test_simple_agent_without_any_base_templates
    result = template_builder.build_agent_markdown(
src/claude_mpm/services/agents/deployment/agent_template_builder.py:364: in build_agent_markdown
    template_data = self._parse_markdown_template(template_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/deployment/agent_template_builder.py:181: in _parse_markdown_template
    raise ValueError(
E   ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmp52za3ndj/agents/engineer.md
```

**Example 2**
- **nodeid**: `tests/integration/test_non_compliant_repo_compatibility.py::TestNonCompliantRepositoryCompatibility::test_nested_agent_without_any_base_templates`
- **file_hint**: `tests/integration/test_non_compliant_repo_compatibility/TestNonCompliantRepositoryCompatibility.py`
- **failure**:
```
exc_type: ValueError
message: ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmppzve1n2j/agents/engineering/python/fastapi-engineer.md
--- relevant traceback (up to 30 lines) ---
tests/integration/test_non_compliant_repo_compatibility.py:108: in test_nested_agent_without_any_base_templates
    result = template_builder.build_agent_markdown(
src/claude_mpm/services/agents/deployment/agent_template_builder.py:364: in build_agent_markdown
    template_data = self._parse_markdown_template(template_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/deployment/agent_template_builder.py:181: in _parse_markdown_template
    raise ValueError(
E   ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmppzve1n2j/agents/engineering/python/fastapi-engineer.md
```

**Example 3**
- **nodeid**: `tests/integration/test_non_compliant_repo_compatibility.py::TestNonCompliantRepositoryCompatibility::test_multiple_agents_no_shared_base`
- **file_hint**: `tests/integration/test_non_compliant_repo_compatibility/TestNonCompliantRepositoryCompatibility.py`
- **failure**:
```
exc_type: ValueError
message: ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmp1akccc_x/agents/engineer.md
--- relevant traceback (up to 30 lines) ---
tests/integration/test_non_compliant_repo_compatibility.py:160: in test_multiple_agents_no_shared_base
    result = template_builder.build_agent_markdown(
src/claude_mpm/services/agents/deployment/agent_template_builder.py:364: in build_agent_markdown
    template_data = self._parse_markdown_template(template_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/deployment/agent_template_builder.py:181: in _parse_markdown_template
    raise ValueError(
E   ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmp1akccc_x/agents/engineer.md
```

### Subpattern: `ValueError: Invalid isoformat string: <str> | <unknown>` (1 failures)

**Example 1**
- **nodeid**: `tests/test_memory_system_integration.py::TestMemorySystemIntegration::test_memory_file_creation_simple_list_format`
- **file_hint**: `tests/test_memory_system_integration/TestMemorySystemIntegration.py`
- **failure**:
```
exc_type: ValueError
message: ValueError: Invalid isoformat string: '2026-02-22T14:24:53.277885+00:00+00:00'
--- relevant traceback (up to 30 lines) ---
tests/test_memory_system_integration.py:95: in test_memory_file_creation_simple_list_format
    timestamp = datetime.fromisoformat(timestamp_match.replace("Z", "+00:00"))
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ValueError: Invalid isoformat string: '2026-02-22T14:24:53.277885+00:00+00:00'
```

### Subpattern: `ValueError: a coroutine was expected, got <MagicMock name=<str> id=<str>> | <unknown>` (1 failures)

**Example 1**
- **nodeid**: `tests/test_socketio_service.py::TestEventBroadcasting::test_broadcast_with_namespace_isolation`
- **file_hint**: `tests/test_socketio_service/TestEventBroadcasting.py`
- **failure**:
```
exc_type: ValueError
message: ValueError: a coroutine was expected, got <MagicMock name='emit()' id='4648324032'>
--- relevant traceback (up to 30 lines) ---
tests/test_socketio_service.py:277: in test_broadcast_with_namespace_isolation
    asyncio.run(
../../.asdf/installs/python/3.12.11/lib/python3.12/asyncio/runners.py:195: in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/asyncio/runners.py:89: in run
    raise ValueError("a coroutine was expected, got {!r}".format(coro))
E   ValueError: a coroutine was expected, got <MagicMock name='emit()' id='4648324032'>
```

## C. Hypotheses

- Invalid test data format not matching validation expectations.
- Edge case input (empty string, zero, negative) not handled.
- Enum value changed or removed.
- Date/time format mismatch between components.
- Configuration value outside permitted range.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Review failure messages for common patterns.
- [ ] Check for recent changes to the affected modules.

## E. Targeted Repo Queries

```bash
rg "# TODO|# FIXME" src/ --include="*.py"
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/integration/test_non_compliant_repo_compatibility.py::TestNonCompliantRepositoryCompatibility::test_simple_agent_without_any_base_templates" -xvs

# Run small set for this bucket
pytest -k 'value' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the value_errors bucket:
  tests/integration/test_non_compliant_repo_compatibility.py::TestNonCompliantRepositoryCompatibility::test_simple_agent_without_any_base_templates
  tests/test_memory_system_integration.py::TestMemorySystemIntegration::test_memory_file_creation_simple_list_format
  tests/test_socketio_service.py::TestEventBroadcasting::test_broadcast_with_namespace_isolation

And these relevant source files:
  tests/integration/test_non_compliant_repo_compatibility/TestNonCompliantRepositoryCompatibility.py
  tests/test_memory_system_integration/TestMemorySystemIntegration.py
  tests/test_socketio_service/TestEventBroadcasting.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
