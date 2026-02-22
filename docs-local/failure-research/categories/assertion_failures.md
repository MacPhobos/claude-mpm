# Failure Category: assertion_failures

## A. Snapshot
- **Total failures**: 372
- **Top exception types**:
  - `AssertionError`: 275
  - `(unknown)`: 95
  - `NameError`: 1
  - `Exception`: 1
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `failed on setup with <str> \| <unknown>` | 62 |
  | `AssertionError: assert N == N \| <unknown>` | 23 |
  | `assert N == N \| <unknown>` | 20 |
  | `AssertionError: assert False \| <unknown>` | 12 |
  | `AssertionError: Expected <str> to have been called once. Called N times. \| <unknown>` | 11 |
  | `AssertionError: assert <str> == <str> \| <unknown>` | 9 |
  | `AssertionError: Scenario WF-N FAILED \| <unknown>` | 8 |
  | `AssertionError: Scenario EV-N FAILED \| <unknown>` | 7 |
  | `AssertionError: N != N \| <unknown>` | 7 |
  | `AssertionError: Scenario FT-N FAILED \| <unknown>` | 6 |

## B. Representative Examples

### Subpattern: `failed on setup with <str> | <unknown>` (62 failures)

**Example 1**
- **nodeid**: `tests/test_agent_template_builder.py::TestAgentTemplateBuilder::test_build_agent_markdown_basic`
- **file_hint**: `tests/test_agent_template_builder/TestAgentTemplateBuilder.py`
- **failure**:
```
exc_type: 
message: failed on setup with "NameError: name 'tmp_path' is not defined"
--- relevant traceback (up to 30 lines) ---
tests/test_agent_template_builder.py:35: in temp_dir
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 2**
- **nodeid**: `tests/test_agent_template_builder.py::TestAgentTemplateBuilder::test_build_agent_markdown_invalid_name`
- **file_hint**: `tests/test_agent_template_builder/TestAgentTemplateBuilder.py`
- **failure**:
```
exc_type: 
message: failed on setup with "NameError: name 'tmp_path' is not defined"
--- relevant traceback (up to 30 lines) ---
tests/test_agent_template_builder.py:35: in temp_dir
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 3**
- **nodeid**: `tests/test_agent_template_builder.py::TestAgentTemplateBuilder::test_build_agent_markdown_tools_with_spaces`
- **file_hint**: `tests/test_agent_template_builder/TestAgentTemplateBuilder.py`
- **failure**:
```
exc_type: 
message: failed on setup with "NameError: name 'tmp_path' is not defined"
--- relevant traceback (up to 30 lines) ---
tests/test_agent_template_builder.py:35: in temp_dir
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

### Subpattern: `AssertionError: assert N == N | <unknown>` (23 failures)

**Example 1**
- **nodeid**: `tests/hooks/claude_hooks/test_hook_handler_connections.py::TestStateManagement::test_git_branch_caching`
- **file_hint**: `tests/hooks/claude_hooks/test_hook_handler_connections/TestStateManagement.py`
- **failure**:
```
exc_type: AssertionError
message: AssertionError: assert 1 == 2
--- relevant traceback (up to 30 lines) ---
tests/hooks/claude_hooks/test_hook_handler_connections.py:212: in test_git_branch_caching
    assert mock_run.call_count == 2
E   AssertionError: assert 1 == 2
E    +  where 1 = <MagicMock name='run' id='4648985200'>.call_count
```

**Example 2**
- **nodeid**: `tests/socketio/test_event_handler_registry.py::TestEventHandlerRegistry::test_register_all_events_success`
- **file_hint**: `tests/socketio/test_event_handler_registry/TestEventHandlerRegistry.py`
- **failure**:
```
exc_type: AssertionError
message: AssertionError: assert 1 == 7
--- relevant traceback (up to 30 lines) ---
tests/socketio/test_event_handler_registry.py:191: in test_register_all_events_success
    assert len(self.mock_sio.handlers) == expected_total
E   AssertionError: assert 1 == 7
E    +  where 1 = len({'existing_event': <Mock id='4572099408'>})
E    +    where {'existing_event': <Mock id='4572099408'>} = <Mock name='mock.core.sio' id='4572096816'>.handlers
E    +      where <Mock name='mock.core.sio' id='4572096816'> = <test_event_handler_registry.TestEventHandlerRegistry object at 0x10f245730>.mock_sio
```

**Example 3**
- **nodeid**: `tests/socketio/test_event_handler_registry.py::TestEventHandlerRegistry::test_register_all_events_with_handler_failure`
- **file_hint**: `tests/socketio/test_event_handler_registry/TestEventHandlerRegistry.py`
- **failure**:
```
exc_type: AssertionError
message: AssertionError: assert 0 == 6
--- relevant traceback (up to 30 lines) ---
tests/socketio/test_event_handler_registry.py:213: in test_register_all_events_with_handler_failure
    assert len(self.mock_sio.handlers) == expected_events
E   AssertionError: assert 0 == 6
E    +  where 0 = len({})
E    +    where {} = <Mock name='mock.core.sio' id='4572162016'>.handlers
E    +      where <Mock name='mock.core.sio' id='4572162016'> = <test_event_handler_registry.TestEventHandlerRegistry object at 0x10f245a60>.mock_sio
```

### Subpattern: `assert N == N | <unknown>` (20 failures)

**Example 1**
- **nodeid**: `tests/services/agents/test_agent_selection_service.py::TestAutoConfiguration::test_deploy_auto_configure_dry_run`
- **file_hint**: `tests/services/agents/test_agent_selection_service/TestAutoConfiguration.py`
- **failure**:
```
exc_type: 
message: assert 1 == 5
--- relevant traceback (up to 30 lines) ---
tests/services/agents/test_agent_selection_service.py:270: in test_deploy_auto_configure_dry_run
    assert result["deployed_count"] == 5  # python-engineer + 4 core agents
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   assert 1 == 5
```

**Example 2**
- **nodeid**: `tests/services/skills/test_git_skill_source_manager.py::TestGitSkillSourceManager::test_get_skills_by_source`
- **file_hint**: `tests/services/skills/test_git_skill_source_manager/TestGitSkillSourceManager.py`
- **failure**:
```
exc_type: 
message: assert 0 == 1
--- relevant traceback (up to 30 lines) ---
tests/services/skills/test_git_skill_source_manager.py:337: in test_get_skills_by_source
    assert len(skills) == 1
E   assert 0 == 1
E    +  where 0 = len([])
```

**Example 3**
- **nodeid**: `tests/services/skills/test_skill_discovery_service.py::TestSkillDiscoveryService::test_discover_skills_ignores_non_markdown_files`
- **file_hint**: `tests/services/skills/test_skill_discovery_service/TestSkillDiscoveryService.py`
- **failure**:
```
exc_type: 
message: assert 0 == 1
--- relevant traceback (up to 30 lines) ---
tests/services/skills/test_skill_discovery_service.py:499: in test_discover_skills_ignores_non_markdown_files
    assert len(skills) == 1
E   assert 0 == 1
E    +  where 0 = len([])
```

## C. Hypotheses

- Business logic changed but tests not updated to reflect new behaviour.
- Test expectation based on old API contract.
- Non-deterministic output (ordering, timestamps) causing flaky assertions.
- Side effect from another test altering shared state.
- Feature flag or configuration toggling behaviour in unexpected direction.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Compare expected vs actual values in failure output.
- [ ] Check if business logic changed and assertions need updating.
- [ ] Look for non-deterministic ordering in collections.
- [ ] Verify test isolation (no shared state between tests).

## E. Targeted Repo Queries

```bash
rg "assert " tests/ --include="*.py" | head -50
rg "assertEqual|assertTrue|assertFalse" tests/ --include="*.py"
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/test_agent_template_builder.py::TestAgentTemplateBuilder::test_build_agent_markdown_basic" -xvs

# Run small set for this bucket
pytest -k 'assert' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the assertion_failures bucket:
  tests/test_agent_template_builder.py::TestAgentTemplateBuilder::test_build_agent_markdown_basic
  tests/hooks/claude_hooks/test_hook_handler_connections.py::TestStateManagement::test_git_branch_caching
  tests/services/agents/test_agent_selection_service.py::TestAutoConfiguration::test_deploy_auto_configure_dry_run

And these relevant source files:
  tests/test_agent_template_builder/TestAgentTemplateBuilder.py
  tests/hooks/claude_hooks/test_hook_handler_connections/TestStateManagement.py
  tests/services/agents/test_agent_selection_service/TestAutoConfiguration.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
