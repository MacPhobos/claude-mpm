# Type Errors

**Category**: `type_errors`

## A. Snapshot

- **Total failures in this category**: 425
- **Distinct subpatterns**: 382

### Top Exception Types

| Exception Type | Count |
|---|---|
| `TypeError` | 425 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `TypeError: TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'` | 9 |
| 2 | `TypeError: TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'` | 9 |
| 3 | `TypeError: TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'` | 5 |
| 4 | `TypeError: TypeError: Object of type PosixPath is not JSON serializable` | 5 |
| 5 | `TypeError: TypeError: unsupported operand type(s) for /: 'TestAgentLoaderFormats' and 'str'` | 4 |
| 6 | `TypeError: TypeError: unsupported operand type(s) for /: 'TestUnifiedPathManager' and 'str'` | 4 |
| 7 | `TypeError: TypeError: unsupported operand type(s) for /: 'TestSchemaIntegration' and 'str'` | 3 |
| 8 | `TypeError: TypeError: 'in <string>' requires string as left operand, not list` | 3 |
| 9 | `TypeError: TypeError: Object of type MagicMock is not JSON serializable` | 3 |
| 10 | `TypeError: TypeError: 'Mock' object is not subscriptable` | 3 |
| 11 | `TypeError: TypeError: unsupported operand type(s) for /: 'TestAgentRegistryAdapter' and 'str'` | 3 |
| 12 | `TypeError: TypeError: 'NoneType' object is not subscriptable` | 2 |
| 13 | `TypeError: TypeError: cannot unpack non-iterable TestRollbackScenarios object` | 2 |
| 14 | `TypeError: TypeError: object of type 'Mock' has no len()` | 2 |
| 15 | `TypeError: TypeError: TestCommandResult.test_success_result_creation() takes <N> positional argument...` | 1 |

## B. Representative Examples

### Subpattern: `TypeError: TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'`
- **Count**: 9
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.test_frontmatter_format.TestFrontmatterFormat::test_frontmatter_structure_valid`
- **file_hint**: `tests/test_frontmatter_format.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'

tests/test_frontmatter_format.py:34: in test_frontmatter_structure_valid
    agent_file = self / "test_agent.md"
                 ^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'
```

**Example 2**:
- **nodeid**: `tests.test_frontmatter_format.TestFrontmatterFormat::test_frontmatter_required_fields`
- **file_hint**: `tests/test_frontmatter_format.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'

tests/test_frontmatter_format.py:63: in test_frontmatter_required_fields
    agent_file = self / f"test_missing_{missing_field}.md"
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'
```

**Example 3**:
- **nodeid**: `tests.test_frontmatter_format.TestFrontmatterFormat::test_frontmatter_version_formats`
- **file_hint**: `tests/test_frontmatter_format.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'

tests/test_frontmatter_format.py:103: in test_frontmatter_version_formats
    agent_file = self / f"test_version_{version.replace('.', '_')}.md"
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'
```

### Subpattern: `TypeError: TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'`
- **Count**: 9
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.test_instruction_synthesis.TestInstructionSynthesis::test_instruction_file_loading`
- **file_hint**: `tests/test_instruction_synthesis.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'

tests/test_instruction_synthesis.py:31: in test_instruction_file_loading
    instructions_file = self / "INSTRUCTIONS.md"
                        ^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'
```

**Example 2**:
- **nodeid**: `tests.test_instruction_synthesis.TestInstructionSynthesis::test_todowrite_loading`
- **file_hint**: `tests/test_instruction_synthesis.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'

tests/test_instruction_synthesis.py:54: in test_todowrite_loading
    todowrite_file = self / "TODOWRITE.md"
                     ^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'
```

**Example 3**:
- **nodeid**: `tests.test_instruction_synthesis.TestInstructionSynthesis::test_memories_loading`
- **file_hint**: `tests/test_instruction_synthesis.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'

tests/test_instruction_synthesis.py:75: in test_memories_loading
    memories_file = self / "MEMORIES.md"
                    ^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'
```

### Subpattern: `TypeError: TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'`
- **Count**: 5
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.test_schema_standardization.TestSchemaStandardization::test_agent_loader_with_new_schema`
- **file_hint**: `tests/test_schema_standardization.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'

tests/test_schema_standardization.py:240: in test_agent_loader_with_new_schema
    agent_path = self / "test_agent.json"
                 ^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'
```

**Example 2**:
- **nodeid**: `tests.test_schema_standardization.TestSchemaStandardization::test_agent_loader_rejects_old_format`
- **file_hint**: `tests/test_schema_standardization.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'

tests/test_schema_standardization.py:262: in test_agent_loader_rejects_old_format
    agent_path = self / "test_agent.json"
                 ^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'
```

**Example 3**:
- **nodeid**: `tests.test_schema_standardization.TestSchemaStandardization::test_performance_agent_loading`
- **file_hint**: `tests/test_schema_standardization.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'

tests/test_schema_standardization.py:284: in test_performance_agent_loading
    with open(self / f"agent_{i}.json", "w") as f:
              ^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'
```

### Subpattern: `TypeError: TypeError: Object of type PosixPath is not JSON serializable`
- **Count**: 5
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.test_hook_installer.TestHookInstaller::test_settings_backup_and_restore`
- **file_hint**: `tests/test_hook_installer.py`

```
Message: TypeError: Object of type PosixPath is not JSON serializable

tests/test_hook_installer.py:587: in test_settings_backup_and_restore
    self.installer._update_claude_settings(script_path)
src/claude_mpm/hooks/claude_hooks/installer.py:824: in _update_claude_settings
    json.dump(settings, f, indent=2)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/__init__.py:179: in dump
    ... (truncated) ...
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

**Example 2**:
- **nodeid**: `tests.test_hook_installer.TestHookInstaller::test_update_claude_settings_existing_file`
- **file_hint**: `tests/test_hook_installer.py`

```
Message: TypeError: Object of type PosixPath is not JSON serializable

tests/test_hook_installer.py:285: in test_update_claude_settings_existing_file
    self.installer._update_claude_settings(script_path)
src/claude_mpm/hooks/claude_hooks/installer.py:824: in _update_claude_settings
    json.dump(settings, f, indent=2)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/__init__.py:179: in dump
    ... (truncated) ...
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

**Example 3**:
- **nodeid**: `tests.test_hook_installer.TestHookInstaller::test_update_claude_settings_new_file`
- **file_hint**: `tests/test_hook_installer.py`

```
Message: TypeError: Object of type PosixPath is not JSON serializable

tests/test_hook_installer.py:254: in test_update_claude_settings_new_file
    self.installer._update_claude_settings(script_path)
src/claude_mpm/hooks/claude_hooks/installer.py:824: in _update_claude_settings
    json.dump(settings, f, indent=2)
../../.asdf/installs/python/3.12.11/lib/python3.12/json/__init__.py:179: in dump
    ... (truncated) ...
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

### Subpattern: `TypeError: TypeError: unsupported operand type(s) for /: 'TestAgentLoaderFormats' and 'str'`
- **Count**: 4
- **Exception**: `TypeError`

**Example 1**:
- **nodeid**: `tests.test_agent_loader_format.TestAgentLoaderFormats::test_narrative_fields_format`
- **file_hint**: `tests/test_agent_loader_format.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestAgentLoaderFormats' and 'str'

tests/test_agent_loader_format.py:28: in test_narrative_fields_format
    agent_file = self / "test_agent.json"
                 ^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestAgentLoaderFormats' and 'str'
```

**Example 2**:
- **nodeid**: `tests.test_agent_loader_format.TestAgentLoaderFormats::test_old_content_format`
- **file_hint**: `tests/test_agent_loader_format.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestAgentLoaderFormats' and 'str'

tests/test_agent_loader_format.py:66: in test_old_content_format
    agent_file = self / "test_old_agent.json"
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestAgentLoaderFormats' and 'str'
```

**Example 3**:
- **nodeid**: `tests.test_agent_loader_format.TestAgentLoaderFormats::test_instructions_field_format`
- **file_hint**: `tests/test_agent_loader_format.py`

```
Message: TypeError: unsupported operand type(s) for /: 'TestAgentLoaderFormats' and 'str'

tests/test_agent_loader_format.py:104: in test_instructions_field_format
    agent_file = self / "test_instructions_agent.json"
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: unsupported operand type(s) for /: 'TestAgentLoaderFormats' and 'str'
```

## C. Hypotheses

- API signature changes not reflected in callers or test mocks.
- Passing wrong argument types after refactoring.
- Missing or extra keyword arguments after function signature updates.
- Mock objects returning unexpected types.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Check function signatures for recent changes
- [ ] Review mock configurations for type correctness
- [ ] Search for deprecated parameter names
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/cli/test_base_command/TestAgentCommand.py`
  - `tests/cli/test_base_command/TestBaseCommand.py`
  - `tests/cli/test_base_command/TestCommandResult.py`
  - `tests/cli/test_base_command/TestServiceCommand.py`
  - `tests/cli/test_shared_utilities/TestArgumentPatterns.py`
  - `tests/cli/test_shared_utilities/TestCommonArguments.py`
  - `tests/cli/test_shared_utilities/TestOutputFormatter.py`
  - `tests/eval/test_cases/test_pm_behavioral_compliance.py`
  - `tests/integration/test_schema_integration.py`
  - `tests/integration/test_schema_integration/TestSchemaIntegration.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where TypeError is raised in source code
rg 'raise TypeError' src/ --type py

# Key test files to inspect
# tests/cli/test_base_command/TestBaseCommand.py
# tests/cli/test_base_command/TestCommandResult.py
# tests/cli/test_shared_utilities/TestCommonArguments.py
# tests/eval/test_cases/test_pm_behavioral_compliance.py
# tests/integration/test_schema_integration.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/test_frontmatter_format/TestFrontmatterFormat.py::test_frontmatter_structure_valid' -x --tb=short
pytest 'tests/test_frontmatter_format/TestFrontmatterFormat.py::test_frontmatter_required_fields' -x --tb=short
pytest 'tests/test_instruction_synthesis/TestInstructionSynthesis.py::test_instruction_file_loading' -x --tb=short
pytest 'tests/test_instruction_synthesis/TestInstructionSynthesis.py::test_todowrite_loading' -x --tb=short
pytest 'tests/test_schema_standardization/TestSchemaStandardization.py::test_agent_loader_with_new_schema' -x --tb=short
pytest 'tests/test_schema_standardization/TestSchemaStandardization.py::test_agent_loader_rejects_old_format' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_frontmatter_structure_valid or test_instruction_file_loading or test_agent_loader_with_new_schema' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **425 test failures** in the `type_errors` category (Type Errors).

**Top patterns**:
  - `TypeError: TypeError: unsupported operand type(s) for /: 'TestFrontmatterFormat' and 'str'` (9 occurrences)
  - `TypeError: TypeError: unsupported operand type(s) for /: 'TestInstructionSynthesis' and 'str'` (9 occurrences)
  - `TypeError: TypeError: unsupported operand type(s) for /: 'TestSchemaStandardization' and 'str'` (5 occurrences)

**Sample failing tests**:
  - `tests.test_frontmatter_format.TestFrontmatterFormat::test_frontmatter_structure_valid`
  - `tests.test_frontmatter_format.TestFrontmatterFormat::test_frontmatter_required_fields`
  - `tests.test_instruction_synthesis.TestInstructionSynthesis::test_instruction_file_loading`
  - `tests.test_instruction_synthesis.TestInstructionSynthesis::test_todowrite_loading`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/type_errors.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
