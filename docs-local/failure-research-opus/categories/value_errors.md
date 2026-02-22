# Value Errors

**Category**: `value_errors`

## A. Snapshot

- **Total failures in this category**: 12
- **Distinct subpatterns**: 3

### Top Exception Types

| Exception Type | Count |
|---|---|
| `ValueError` | 12 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `ValueError: ValueError: Markdown template missing YAML frontmatter: <PATH>` | 10 |
| 2 | `ValueError: ValueError: Invalid isoformat string: '<TIMESTAMP>:<N>+<N>:<N>'` | 1 |
| 3 | `ValueError: ValueError: a coroutine was expected, got <MagicMock name='emit()' id='<N>'>` | 1 |

## B. Representative Examples

### Subpattern: `ValueError: ValueError: Markdown template missing YAML frontmatter: <PATH>`
- **Count**: 10
- **Exception**: `ValueError`

**Example 1**:
- **nodeid**: `tests.integration.test_non_compliant_repo_compatibility.TestNonCompliantRepositoryCompatibility::test_simple_agent_without_any_base_templates`
- **file_hint**: `tests/integration/test_non_compliant_repo_compatibility.py`

```
Message: ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmp52za3ndj/agents/engineer.md

tests/integration/test_non_compliant_repo_compatibility.py:68: in test_simple_agent_without_any_base_templates
    result = template_builder.build_agent_markdown(
src/claude_mpm/services/agents/deployment/agent_template_builder.py:364: in build_agent_markdown
    template_data = self._parse_markdown_template(template_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/deployment/agent_template_builder.py:181: in _parse_markdown_template
    raise ValueError(
E   ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmp52za3ndj/agents/engineer.md
```

**Example 2**:
- **nodeid**: `tests.integration.test_non_compliant_repo_compatibility.TestNonCompliantRepositoryCompatibility::test_nested_agent_without_any_base_templates`
- **file_hint**: `tests/integration/test_non_compliant_repo_compatibility.py`

```
Message: ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmppzve1n2j/agents/engineering/python/fastapi-engineer.md

tests/integration/test_non_compliant_repo_compatibility.py:108: in test_nested_agent_without_any_base_templates
    result = template_builder.build_agent_markdown(
src/claude_mpm/services/agents/deployment/agent_template_builder.py:364: in build_agent_markdown
    template_data = self._parse_markdown_template(template_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/deployment/agent_template_builder.py:181: in _parse_markdown_template
    raise ValueError(
E   ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmppzve1n2j/agents/engineering/python/fastapi-engineer.md
```

**Example 3**:
- **nodeid**: `tests.integration.test_non_compliant_repo_compatibility.TestNonCompliantRepositoryCompatibility::test_multiple_agents_no_shared_base`
- **file_hint**: `tests/integration/test_non_compliant_repo_compatibility.py`

```
Message: ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmp1akccc_x/agents/engineer.md

tests/integration/test_non_compliant_repo_compatibility.py:160: in test_multiple_agents_no_shared_base
    result = template_builder.build_agent_markdown(
src/claude_mpm/services/agents/deployment/agent_template_builder.py:364: in build_agent_markdown
    template_data = self._parse_markdown_template(template_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/agents/deployment/agent_template_builder.py:181: in _parse_markdown_template
    raise ValueError(
E   ValueError: Markdown template missing YAML frontmatter: /var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/tmp1akccc_x/agents/engineer.md
```

### Subpattern: `ValueError: ValueError: Invalid isoformat string: '<TIMESTAMP>:<N>+<N>:<N>'`
- **Count**: 1
- **Exception**: `ValueError`

**Example 1**:
- **nodeid**: `tests.test_memory_system_integration.TestMemorySystemIntegration::test_memory_file_creation_simple_list_format`
- **file_hint**: `tests/test_memory_system_integration.py`

```
Message: ValueError: Invalid isoformat string: '2026-02-22T14:24:53.277885+00:00+00:00'

tests/test_memory_system_integration.py:95: in test_memory_file_creation_simple_list_format
    timestamp = datetime.fromisoformat(timestamp_match.replace("Z", "+00:00"))
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ValueError: Invalid isoformat string: '2026-02-22T14:24:53.277885+00:00+00:00'
```

### Subpattern: `ValueError: ValueError: a coroutine was expected, got <MagicMock name='emit()' id='<N>'>`
- **Count**: 1
- **Exception**: `ValueError`

**Example 1**:
- **nodeid**: `tests.test_socketio_service.TestEventBroadcasting::test_broadcast_with_namespace_isolation`
- **file_hint**: `tests/test_socketio_service.py`

```
Message: ValueError: a coroutine was expected, got <MagicMock name='emit()' id='4648324032'>

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

- Input validation changes that now reject previously accepted values.
- Enum or constant changes not reflected in tests.
- String parsing failures due to format changes.
- Configuration values outside new validation bounds.
- The dominant subpattern (`ValueError: ValueError: Markdown template missing YAML frontmatter: <PATH>`) accounts for 10/12 failures, suggesting a single root cause.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/integration/test_non_compliant_repo_compatibility.py`
  - `tests/test_memory_system_integration.py`
  - `tests/test_socketio_service.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where ValueError is raised in source code
rg 'raise ValueError' src/ --type py

# Key test files to inspect
# tests/integration/test_non_compliant_repo_compatibility.py
# tests/test_memory_system_integration.py
# tests/test_socketio_service.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/integration/test_non_compliant_repo_compatibility/TestNonCompliantRepositoryCompatibility.py::test_simple_agent_without_any_base_templates' -x --tb=short
pytest 'tests/integration/test_non_compliant_repo_compatibility/TestNonCompliantRepositoryCompatibility.py::test_nested_agent_without_any_base_templates' -x --tb=short
pytest 'tests/test_memory_system_integration/TestMemorySystemIntegration.py::test_memory_file_creation_simple_list_format' -x --tb=short
pytest 'tests/test_socketio_service/TestEventBroadcasting.py::test_broadcast_with_namespace_isolation' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_simple_agent_without_any_base_templates or test_memory_file_creation_simple_list_format or test_broadcast_with_namespace_isolation' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **12 test failures** in the `value_errors` category (Value Errors).

**Top patterns**:
  - `ValueError: ValueError: Markdown template missing YAML frontmatter: <PATH>` (10 occurrences)
  - `ValueError: ValueError: Invalid isoformat string: '<TIMESTAMP>:<N>+<N>:<N>'` (1 occurrences)
  - `ValueError: ValueError: a coroutine was expected, got <MagicMock name='emit()' id='<N>'>` (1 occurrences)

**Sample failing tests**:
  - `tests.integration.test_non_compliant_repo_compatibility.TestNonCompliantRepositoryCompatibility::test_simple_agent_without_any_base_templates`
  - `tests.integration.test_non_compliant_repo_compatibility.TestNonCompliantRepositoryCompatibility::test_nested_agent_without_any_base_templates`
  - `tests.test_memory_system_integration.TestMemorySystemIntegration::test_memory_file_creation_simple_list_format`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/value_errors.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
