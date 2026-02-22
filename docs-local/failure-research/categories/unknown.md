# Failure Category: unknown

## A. Snapshot
- **Total failures**: 210
- **Top exception types**:
  - `NameError`: 155
  - `(unknown)`: 37
  - `RuntimeError`: 4
  - `BadNamespaceError`: 3
  - `GitOperationError`: 3
  - `OSError`: 2
  - `Exception`: 2
  - `NotImplementedError`: 1
  - `JSONDecodeError`: 1
  - `SystemExit`: 1
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `NameError: name <str> is not defined \| <unknown>` | 155 |
  | `assert False \| <unknown>` | 20 |
  | `assert N > N \| <unknown>` | 8 |
  | `RuntimeError: There is no current event loop in thread <str>. \| <unknown>` | 3 |
  | `assert N >= N \| <unknown>` | 3 |
  | `socketio.exceptions.BadNamespaceError: / is not a connected namespace. \| <unknown>` | 3 |
  | `assert <str> in '\n\x1b[36m╭─── Claude MPM v4.N.N ────────────────────────────────────────────────────────────────────── \| <unknown>` | 3 |
  | `claude_mpm.services.version_control.git_operations.GitOperationError: Error running Git command: \| <unknown>` | 3 |
  | `OSError: [Errno N] Directory not empty: <str> \| <unknown>` | 2 |
  | `assert N < -N \| <unknown>` | 1 |

## B. Representative Examples

### Subpattern: `NameError: name <str> is not defined | <unknown>` (155 failures)

**Example 1**
- **nodeid**: `tests/integration/agents/test_agent_deployment.py::test_claude_runner`
- **file_hint**: `tests/integration/agents/test_agent_deployment.py`
- **failure**:
```
exc_type: NameError
message: NameError: name 'tmp_path' is not defined
--- relevant traceback (up to 30 lines) ---
tests/integration/agents/test_agent_deployment.py:87: in test_claude_runner
    with tmp_path as tmpdir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 2**
- **nodeid**: `tests/integration/agents/test_agent_deployment_fix.py::test_deployment_with_user_directory`
- **file_hint**: `tests/integration/agents/test_agent_deployment_fix.py`
- **failure**:
```
exc_type: NameError
message: NameError: name 'tmp_path' is not defined
--- relevant traceback (up to 30 lines) ---
tests/integration/agents/test_agent_deployment_fix.py:30: in test_deployment_with_user_directory
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 3**
- **nodeid**: `tests/integration/agents/test_agent_deployment_fix.py::test_deployment_with_explicit_working_dir`
- **file_hint**: `tests/integration/agents/test_agent_deployment_fix.py`
- **failure**:
```
exc_type: NameError
message: NameError: name 'tmp_path' is not defined
--- relevant traceback (up to 30 lines) ---
tests/integration/agents/test_agent_deployment_fix.py:113: in test_deployment_with_explicit_working_dir
    with tmp_path as temp_dir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

### Subpattern: `assert False | <unknown>` (20 failures)

**Example 1**
- **nodeid**: `tests/eval/agents/shared/test_agent_infrastructure.py::TestInfrastructureIntegration::test_end_to_end_qa_agent`
- **file_hint**: `tests/eval/agents/shared/test_agent_infrastructure/TestInfrastructureIntegration.py`
- **failure**:
```
exc_type: 
message: assert False
--- relevant traceback (up to 30 lines) ---
tests/eval/agents/shared/test_agent_infrastructure.py:435: in test_end_to_end_qa_agent
    assert data["ci_mode_used"]
E   assert False
```

**Example 2**
- **nodeid**: `tests/cli/commands/test_agents_comprehensive.py::TestIntegrationScenarios::test_deploy_then_list_workflow`
- **file_hint**: `tests/cli/commands/test_agents_comprehensive/TestIntegrationScenarios.py`
- **failure**:
```
exc_type: 
message: assert False
--- relevant traceback (up to 30 lines) ---
tests/cli/commands/test_agents_comprehensive.py:1481: in test_deploy_then_list_workflow
    assert list_result.success
E   assert False
E    +  where False = CommandResult(success=False, exit_code=1, message="Error listing deployed agents: 'in <string>' requires string as left operand, not MagicMock", data=None).success
```

**Example 3**
- **nodeid**: `tests/eval/agents/shared/test_agent_infrastructure.py::TestAgentResponseParser::test_parse_qa_agent_response`
- **file_hint**: `tests/eval/agents/shared/test_agent_infrastructure/TestAgentResponseParser.py`
- **failure**:
```
exc_type: 
message: assert False
--- relevant traceback (up to 30 lines) ---
tests/eval/agents/shared/test_agent_infrastructure.py:115: in test_parse_qa_agent_response
    assert data["ci_mode_used"]
E   assert False
```

### Subpattern: `assert N > N | <unknown>` (8 failures)

**Example 1**
- **nodeid**: `tests/eval/agents/shared/test_agent_infrastructure.py::TestInfrastructureIntegration::test_end_to_end_engineer_agent`
- **file_hint**: `tests/eval/agents/shared/test_agent_infrastructure/TestInfrastructureIntegration.py`
- **failure**:
```
exc_type: 
message: assert 0 > 0
--- relevant traceback (up to 30 lines) ---
tests/eval/agents/shared/test_agent_infrastructure.py:425: in test_end_to_end_engineer_agent
    assert data["search_tools_used"] > 0
E   assert 0 > 0
```

**Example 2**
- **nodeid**: `tests/eval/agents/shared/test_agent_infrastructure.py::TestAgentResponseParser::test_parse_engineer_agent_response`
- **file_hint**: `tests/eval/agents/shared/test_agent_infrastructure/TestAgentResponseParser.py`
- **failure**:
```
exc_type: 
message: assert 0 > 0
--- relevant traceback (up to 30 lines) ---
tests/eval/agents/shared/test_agent_infrastructure.py:102: in test_parse_engineer_agent_response
    assert data["search_tools_used"] > 0
E   assert 0 > 0
```

**Example 3**
- **nodeid**: `tests/services/agents/test_git_source_manager.py::TestGitSourceManagerListCachedAgents::test_list_cached_agents_from_repository`
- **file_hint**: `tests/services/agents/test_git_source_manager/TestGitSourceManagerListCachedAgents.py`
- **failure**:
```
exc_type: 
message: assert 0 > 0
--- relevant traceback (up to 30 lines) ---
tests/services/agents/test_git_source_manager.py:263: in test_list_cached_agents_from_repository
    assert len(agents) > 0
E   assert 0 > 0
E    +  where 0 = len([])
```

## C. Hypotheses

- Root cause unclear from available information.
- May be a combination of multiple failure modes.
- Requires manual investigation with full logs.
- Possibly environment-specific issue not reproducible locally.
- May be a transient failure; check if consistently reproducible.

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
pytest "tests/integration/agents/test_agent_deployment.py::test_claude_runner" -xvs

# Run small set for this bucket
pytest -k 'unknown' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the unknown bucket:
  tests/integration/agents/test_agent_deployment.py::test_claude_runner
  tests/eval/agents/shared/test_agent_infrastructure.py::TestInfrastructureIntegration::test_end_to_end_qa_agent
  tests/eval/agents/shared/test_agent_infrastructure.py::TestInfrastructureIntegration::test_end_to_end_engineer_agent

And these relevant source files:
  tests/integration/agents/test_agent_deployment.py
  tests/eval/agents/shared/test_agent_infrastructure/TestInfrastructureIntegration.py
  tests/eval/agents/shared/test_agent_infrastructure/TestInfrastructureIntegration.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
