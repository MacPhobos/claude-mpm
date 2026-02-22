# Fixture and Setup Errors

**Category**: `fixtures_and_setup`

## A. Snapshot

- **Total failures in this category**: 277
- **Distinct subpatterns**: 45

### Top Exception Types

| Exception Type | Count |
|---|---|
| `NameError` | 175 |
| `AttributeError` | 54 |
| `FixtureLookupError` | 38 |
| `FileNotFoundError` | 10 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `NameError: NameError: name 'tmp_path' is not defined` | 113 |
| 2 | `AttributeError: failed on setup with "AttributeError: 'UnifiedPathManager' object has no attribute '...` | 52 |
| 3 | `NameError: failed on setup with "NameError: name 'tmp_path' is not defined"` | 40 |
| 4 | `NameError: failed on setup with "NameError: name 'Config' is not defined"` | 22 |
| 5 | `FileNotFoundError: failed on setup with "FileNotFoundError: [Errno <N>] No such file or directory: '...` | 10 |
| 6 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_list_presets(self, service)...` | 1 |
| 7 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_validate_preset_valid(self,...` | 1 |
| 8 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_validate_preset_invalid(sel...` | 1 |
| 9 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_get_preset_agents(self, ser...` | 1 |
| 10 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_get_preset_agents_invalid(s...` | 1 |
| 11 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_resolve_agents_without_vali...` | 1 |
| 12 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_resolve_agents_all_availabl...` | 1 |
| 13 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_resolve_agents_missing_some...` | 1 |
| 14 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_resolve_agents_with_conflic...` | 1 |
| 15 | `FixtureLookupError: failed on setup with "file <PATH>, line <N> def test_resolve_agents_invalid_pres...` | 1 |

## B. Representative Examples

### Subpattern: `NameError: NameError: name 'tmp_path' is not defined`
- **Count**: 113
- **Exception**: `NameError`

**Example 1**:
- **nodeid**: `tests.integration.agents.test_agent_deployment::test_claude_runner`
- **file_hint**: `tests/integration/agents/test_agent_deployment.py`

```
Message: NameError: name 'tmp_path' is not defined

tests/integration/agents/test_agent_deployment.py:87: in test_claude_runner
    with tmp_path as tmpdir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 2**:
- **nodeid**: `tests.integration.agents.test_agent_deployment_fix::test_deployment_with_user_directory`
- **file_hint**: `tests/integration/agents/test_agent_deployment_fix.py`

```
Message: NameError: name 'tmp_path' is not defined

tests/integration/agents/test_agent_deployment_fix.py:30: in test_deployment_with_user_directory
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 3**:
- **nodeid**: `tests.integration.agents.test_agent_deployment_fix::test_deployment_with_explicit_working_dir`
- **file_hint**: `tests/integration/agents/test_agent_deployment_fix.py`

```
Message: NameError: name 'tmp_path' is not defined

tests/integration/agents/test_agent_deployment_fix.py:113: in test_deployment_with_explicit_working_dir
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

### Subpattern: `AttributeError: failed on setup with "AttributeError: 'UnifiedPathManager' object has no attribute 'CONFIG_DIR'"`
- **Count**: 52
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.unit.services.version_control.test_branch_strategy.TestBranchStrategyManagerInitialization::test_init_creates_predefined_strategies`
- **file_hint**: `tests/unit/services/version_control/test_branch_strategy.py`

```
Message: failed on setup with "AttributeError: 'UnifiedPathManager' object has no attribute 'CONFIG_DIR'"

tests/unit/services/version_control/test_branch_strategy.py:53: in strategy_manager
    return BranchStrategyManager(str(temp_project_dir), mock_logger)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/branch_strategy.py:115: in __init__
    self._load_strategy_configuration()
src/claude_mpm/services/version_control/branch_strategy.py:313: in _load_strategy_configuration
    f"{get_path_manager().CONFIG_DIR}/config.json",
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'UnifiedPathManager' object has no attribute 'CONFIG_DIR'
```

**Example 2**:
- **nodeid**: `tests.unit.services.version_control.test_branch_strategy.TestBranchStrategyManagerInitialization::test_init_sets_default_strategy`
- **file_hint**: `tests/unit/services/version_control/test_branch_strategy.py`

```
Message: failed on setup with "AttributeError: 'UnifiedPathManager' object has no attribute 'CONFIG_DIR'"

tests/unit/services/version_control/test_branch_strategy.py:53: in strategy_manager
    return BranchStrategyManager(str(temp_project_dir), mock_logger)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/branch_strategy.py:115: in __init__
    self._load_strategy_configuration()
src/claude_mpm/services/version_control/branch_strategy.py:313: in _load_strategy_configuration
    f"{get_path_manager().CONFIG_DIR}/config.json",
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'UnifiedPathManager' object has no attribute 'CONFIG_DIR'
```

**Example 3**:
- **nodeid**: `tests.unit.services.version_control.test_branch_strategy.TestIssueDrivenStrategy::test_issue_driven_strategy_has_correct_branches`
- **file_hint**: `tests/unit/services/version_control/test_branch_strategy.py`

```
Message: failed on setup with "AttributeError: 'UnifiedPathManager' object has no attribute 'CONFIG_DIR'"

tests/unit/services/version_control/test_branch_strategy.py:53: in strategy_manager
    return BranchStrategyManager(str(temp_project_dir), mock_logger)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/version_control/branch_strategy.py:115: in __init__
    self._load_strategy_configuration()
src/claude_mpm/services/version_control/branch_strategy.py:313: in _load_strategy_configuration
    f"{get_path_manager().CONFIG_DIR}/config.json",
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'UnifiedPathManager' object has no attribute 'CONFIG_DIR'
```

### Subpattern: `NameError: failed on setup with "NameError: name 'tmp_path' is not defined"`
- **Count**: 40
- **Exception**: `NameError`

**Example 1**:
- **nodeid**: `tests.test_agent_template_builder.TestAgentTemplateBuilder::test_build_agent_markdown_basic`
- **file_hint**: `tests/test_agent_template_builder.py`

```
Message: failed on setup with "NameError: name 'tmp_path' is not defined"

tests/test_agent_template_builder.py:35: in temp_dir
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 2**:
- **nodeid**: `tests.test_agent_template_builder.TestAgentTemplateBuilder::test_build_agent_markdown_invalid_name`
- **file_hint**: `tests/test_agent_template_builder.py`

```
Message: failed on setup with "NameError: name 'tmp_path' is not defined"

tests/test_agent_template_builder.py:35: in temp_dir
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 3**:
- **nodeid**: `tests.test_agent_template_builder.TestAgentTemplateBuilder::test_build_agent_markdown_tools_with_spaces`
- **file_hint**: `tests/test_agent_template_builder.py`

```
Message: failed on setup with "NameError: name 'tmp_path' is not defined"

tests/test_agent_template_builder.py:35: in temp_dir
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

### Subpattern: `NameError: failed on setup with "NameError: name 'Config' is not defined"`
- **Count**: 22
- **Exception**: `NameError`

**Example 1**:
- **nodeid**: `tests.test_memory_fixes_verification.TestMemoryFixesVerification::test_pm_memory_persistence_to_user_directory`
- **file_hint**: `tests/test_memory_fixes_verification.py`

```
Message: failed on setup with "NameError: name 'Config' is not defined"

tests/test_memory_fixes_verification.py:56: in setup_method
    self.config = Config()
                  ^^^^^^
E   NameError: name 'Config' is not defined
```

**Example 2**:
- **nodeid**: `tests.test_memory_fixes_verification.TestMemoryFixesVerification::test_directory_handling_pm_vs_others`
- **file_hint**: `tests/test_memory_fixes_verification.py`

```
Message: failed on setup with "NameError: name 'Config' is not defined"

tests/test_memory_fixes_verification.py:56: in setup_method
    self.config = Config()
                  ^^^^^^
E   NameError: name 'Config' is not defined
```

**Example 3**:
- **nodeid**: `tests.test_memory_fixes_verification.TestMemoryFixesVerification::test_memory_hook_service_functionality`
- **file_hint**: `tests/test_memory_fixes_verification.py`

```
Message: failed on setup with "NameError: name 'Config' is not defined"

tests/test_memory_fixes_verification.py:56: in setup_method
    self.config = Config()
                  ^^^^^^
E   NameError: name 'Config' is not defined
```

### Subpattern: `FileNotFoundError: failed on setup with "FileNotFoundError: [Errno <N>] No such file or directory: '<LONG_STR>'"`
- **Count**: 10
- **Exception**: `FileNotFoundError`

**Example 1**:
- **nodeid**: `tests.hooks.claude_hooks.test_pre_split_verification.TestPreSplitVerification::test_no_shared_fixtures`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification.py`

```
Message: failed on setup with "FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'"

tests/hooks/claude_hooks/test_pre_split_verification.py:34: in test_file_content
    return test_file_path.read_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

**Example 2**:
- **nodeid**: `tests.hooks.claude_hooks.test_pre_split_verification.TestPreSplitVerification::test_count_test_classes`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification.py`

```
Message: failed on setup with "FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'"

tests/hooks/claude_hooks/test_pre_split_verification.py:34: in test_file_content
    return test_file_path.read_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

**Example 3**:
- **nodeid**: `tests.hooks.claude_hooks.test_pre_split_verification.TestPreSplitVerification::test_count_test_functions`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification.py`

```
Message: failed on setup with "FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'"

tests/hooks/claude_hooks/test_pre_split_verification.py:34: in test_file_content
    return test_file_path.read_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

## C. Hypotheses

- Missing pytest plugins (e.g., pytest-mock providing `mocker` fixture).
- Fixture scope mismatches between test classes and conftest definitions.
- Fixture names colliding across conftest files.
- Fixtures depending on environment state (directories, env vars) not present.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Check `conftest.py` files for fixture definitions
- [ ] Verify pytest plugins are installed (`pytest-mock`, etc.)
- [ ] Check fixture scopes for mismatches
- [ ] Inspect the top 3-5 failing test files listed below
  - `/Users/mac/workspace/claude-mpm-tests/tests/services/agents/test_agent_preset_service.py`
  - `/Users/mac/workspace/claude-mpm-tests/tests/test_archive_manager.py`
  - `tests/hooks/claude_hooks/test_pre_split_verification.py`
  - `tests/integration/agents/test_agent_deployment.py`
  - `tests/integration/agents/test_agent_deployment_fix.py`
  - `tests/integration/agents/test_agent_exclusion.py`
  - `tests/integration/agents/test_comprehensive_agent_exclusion.py`
  - `tests/integration/infrastructure/test_response_logging_interactive.py`
  - `tests/services/test_deployed_agent_discovery.py`
  - `tests/test_agent_configuration_manager.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where AttributeError is raised in source code
rg 'raise AttributeError' src/ --type py

# Find where FileNotFoundError is raised in source code
rg 'raise FileNotFoundError' src/ --type py

# Find where NameError is raised in source code
rg 'raise NameError' src/ --type py

# Search for 'has' references
rg 'has' src/ --type py -l

# Search for 'CONFIG_DIR' references
rg 'CONFIG_DIR' src/ --type py -l

# Key test files to inspect
# tests/integration/agents/test_agent_deployment.py
# tests/integration/agents/test_agent_deployment_fix.py
# tests/integration/agents/test_agent_exclusion.py
# tests/integration/agents/test_comprehensive_agent_exclusion.py

# Find all conftest.py files
rg -l '' tests/**/conftest.py

# Search for fixture definitions
rg '@pytest.fixture' tests/ --type py -l

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/integration/agents/test_agent_deployment.py::test_claude_runner' -x --tb=short
pytest 'tests/integration/agents/test_agent_deployment_fix.py::test_deployment_with_user_directory' -x --tb=short
pytest 'tests/unit/services/version_control/test_branch_strategy/TestBranchStrategyManagerInitialization.py::test_init_creates_predefined_strategies' -x --tb=short
pytest 'tests/unit/services/version_control/test_branch_strategy/TestBranchStrategyManagerInitialization.py::test_init_sets_default_strategy' -x --tb=short
pytest 'tests/test_agent_template_builder/TestAgentTemplateBuilder.py::test_build_agent_markdown_basic' -x --tb=short
pytest 'tests/test_agent_template_builder/TestAgentTemplateBuilder.py::test_build_agent_markdown_invalid_name' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_claude_runner or test_init_creates_predefined_strategies or test_build_agent_markdown_basic' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **277 test failures** in the `fixtures_and_setup` category (Fixture and Setup Errors).

**Top patterns**:
  - `NameError: NameError: name 'tmp_path' is not defined` (113 occurrences)
  - `AttributeError: failed on setup with "AttributeError: 'UnifiedPathManager' object has no attribute '` (52 occurrences)
  - `NameError: failed on setup with "NameError: name 'tmp_path' is not defined"` (40 occurrences)

**Sample failing tests**:
  - `tests.integration.agents.test_agent_deployment::test_claude_runner`
  - `tests.integration.agents.test_agent_deployment_fix::test_deployment_with_user_directory`
  - `tests.unit.services.version_control.test_branch_strategy.TestBranchStrategyManagerInitialization::test_init_creates_predefined_strategies`
  - `tests.unit.services.version_control.test_branch_strategy.TestBranchStrategyManagerInitialization::test_init_sets_default_strategy`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/fixtures_and_setup.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
