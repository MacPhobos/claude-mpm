# Assertion Failures

**Category**: `assertion_failures`

## A. Snapshot

- **Total failures in this category**: 334
- **Distinct subpatterns**: 239

### Top Exception Types

| Exception Type | Count |
|---|---|
| `AssertionError` | 333 |
| `NameError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `AssertionError: assert <N> == <N>` | 15 |
| 2 | `AssertionError: assert False` | 10 |
| 3 | `AssertionError: AssertionError: assert <N> == <N> + where <N> = len(['research.md', 'engineer.md', '...` | 7 |
| 4 | `AssertionError: AssertionError: <N> != <N>` | 7 |
| 5 | `AssertionError: assert <N> == <N> + where <N> = len([])` | 6 |
| 6 | `AssertionError: AssertionError: True is not false` | 6 |
| 7 | `AssertionError: assert False + where False = CommandResult(success=False, exit_code=<N>, message="Er...` | 5 |
| 8 | `AssertionError: assert <N> > <N> + where <N> = len([])` | 5 |
| 9 | `AssertionError: assert None is not None` | 5 |
| 10 | `AssertionError: AssertionError: assert <N> == <N> + where <N> = len(['.claude-mpm/', '.claude/agents...` | 5 |
| 11 | `AssertionError: AssertionError: Scenario RG-<N> FAILED Violations: Wrong delegation target: got appr...` | 4 |
| 12 | `AssertionError: AssertionError: Scenario FT-<N> FAILED Violations: Missing required tool: Bash (git)...` | 4 |
| 13 | `AssertionError: AssertionError: Scenario MEM-<N> FAILED Violations: Missing required tool: Read, Mis...` | 4 |
| 14 | `AssertionError: assert <N> > <N>` | 3 |
| 15 | `AssertionError: assert False + where False = CommandResult(success=False, exit_code=<N>, message="Er...` | 3 |

## B. Representative Examples

### Subpattern: `AssertionError: assert <N> == <N>`
- **Count**: 15
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.services.agents.test_agent_selection_service.TestAutoConfiguration::test_deploy_auto_configure_dry_run`
- **file_hint**: `tests/services/agents/test_agent_selection_service.py`

```
Message: assert 1 == 5

tests/services/agents/test_agent_selection_service.py:270: in test_deploy_auto_configure_dry_run
    assert result["deployed_count"] == 5  # python-engineer + 4 core agents
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   assert 1 == 5
```

**Example 2**:
- **nodeid**: `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_get_memory_metrics_all_agents`
- **file_hint**: `tests/services/agents/memory/test_agent_memory_manager_comprehensive.py`

```
Message: assert 100.0 == 50.0

tests/services/agents/memory/test_agent_memory_manager_comprehensive.py:689: in test_get_memory_metrics_all_agents
    assert (
E   assert 100.0 == 50.0
```

**Example 3**:
- **nodeid**: `tests.integration.test_git_sync_deploy_phase3.TestPhase3AgentDeployment::test_end_to_end_sync_and_deploy`
- **file_hint**: `tests/integration/test_git_sync_deploy_phase3.py`

```
Message: assert 0 == 3

tests/integration/test_git_sync_deploy_phase3.py:74: in test_end_to_end_sync_and_deploy
    assert deployed_count == 3
E   assert 0 == 3
```

### Subpattern: `AssertionError: assert False`
- **Count**: 10
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.eval.agents.shared.test_agent_infrastructure.TestInfrastructureIntegration::test_end_to_end_qa_agent`
- **file_hint**: `tests/eval/agents/shared/test_agent_infrastructure.py`

```
Message: assert False

tests/eval/agents/shared/test_agent_infrastructure.py:435: in test_end_to_end_qa_agent
    assert data["ci_mode_used"]
E   assert False
```

**Example 2**:
- **nodeid**: `tests.eval.agents.shared.test_agent_infrastructure.TestAgentResponseParser::test_parse_qa_agent_response`
- **file_hint**: `tests/eval/agents/shared/test_agent_infrastructure.py`

```
Message: assert False

tests/eval/agents/shared/test_agent_infrastructure.py:115: in test_parse_qa_agent_response
    assert data["ci_mode_used"]
E   assert False
```

**Example 3**:
- **nodeid**: `tests.integration.test_socketio_integration.TestEndToEndEventFlow::test_event_flow_hook_to_dashboard`
- **file_hint**: `tests/integration/test_socketio_integration.py`

```
Message: assert False

tests/integration/test_socketio_integration.py:96: in test_event_flow_hook_to_dashboard
    assert await wait_for_condition_async(
E   assert False
```

### Subpattern: `AssertionError: AssertionError: assert <N> == <N> + where <N> = len(['research.md', 'engineer.md', 'qa.md', 'documentati`
- **Count**: 7
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.services.agents.sources.test_git_source_sync_service.TestGitSourceSyncService::test_get_agent_list_via_api`
- **file_hint**: `tests/services/agents/sources/test_git_source_sync_service.py`

```
Message: AssertionError: assert 10 == 3
 +  where 10 = len(['research.md', 'engineer.md', 'qa.md', 'documentation.md', 'security.md', 'ops.md', ...])

tests/services/agents/sources/test_git_source_sync_service.py:435: in test_get_agent_list_via_api
    assert len(agent_list) == 3  # README.md and directory excluded
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AssertionError: assert 10 == 3
E    +  where 10 = len(['research.md', 'engineer.md', 'qa.md', 'documentation.md', 'security.md', 'ops.md', ...])
```

**Example 2**:
- **nodeid**: `tests.services.agents.sources.test_git_source_sync_service.TestGitSourceSyncService::test_get_agent_list_excludes_readme`
- **file_hint**: `tests/services/agents/sources/test_git_source_sync_service.py`

```
Message: AssertionError: assert 10 == 2
 +  where 10 = len(['research.md', 'engineer.md', 'qa.md', 'documentation.md', 'security.md', 'ops.md', ...])

tests/services/agents/sources/test_git_source_sync_service.py:492: in test_get_agent_list_excludes_readme
    assert len(agent_list) == 2
E   AssertionError: assert 10 == 2
E    +  where 10 = len(['research.md', 'engineer.md', 'qa.md', 'documentation.md', 'security.md', 'ops.md', ...])
```

**Example 3**:
- **nodeid**: `tests.services.agents.sources.test_git_source_sync_service.TestGitSourceSyncService::test_get_agent_list_filters_non_md_files`
- **file_hint**: `tests/services/agents/sources/test_git_source_sync_service.py`

```
Message: AssertionError: assert 10 == 1
 +  where 10 = len(['research.md', 'engineer.md', 'qa.md', 'documentation.md', 'security.md', 'ops.md', ...])

tests/services/agents/sources/test_git_source_sync_service.py:522: in test_get_agent_list_filters_non_md_files
    assert len(agent_list) == 1
E   AssertionError: assert 10 == 1
E    +  where 10 = len(['research.md', 'engineer.md', 'qa.md', 'documentation.md', 'security.md', 'ops.md', ...])
```

### Subpattern: `AssertionError: AssertionError: <N> != <N>`
- **Count**: 7
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.test_logging_consolidation.TestLoggerConsolidation::test_dynamic_level_change`
- **file_hint**: `tests/test_logging_consolidation.py`

```
Message: AssertionError: 51 != 20

tests/test_logging_consolidation.py:145: in test_dynamic_level_change
    self.assertEqual(logging.root.level, logging.INFO)
E   AssertionError: 51 != 20
```

**Example 2**:
- **nodeid**: `tests.test_logging_consolidation.TestLoggerConsolidation::test_logger_levels`
- **file_hint**: `tests/test_logging_consolidation.py`

```
Message: AssertionError: 51 != 10

tests/test_logging_consolidation.py:90: in test_logger_levels
    self.assertEqual(logging.root.level, logging.DEBUG)
E   AssertionError: 51 != 10
```

**Example 3**:
- **nodeid**: `tests.integration.test_hook_integration.TestHookToDashboard::test_event_batching`
- **file_hint**: `tests/integration/test_hook_integration.py`

```
Message: AssertionError: 3 != 10

tests/integration/test_hook_integration.py:227: in test_event_batching
    self.assertEqual(mock_post.call_count, 10)
E   AssertionError: 3 != 10
```

### Subpattern: `AssertionError: assert <N> == <N> + where <N> = len([])`
- **Count**: 6
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.services.skills.test_git_skill_source_manager.TestGitSkillSourceManager::test_get_skills_by_source`
- **file_hint**: `tests/services/skills/test_git_skill_source_manager.py`

```
Message: assert 0 == 1
 +  where 0 = len([])

tests/services/skills/test_git_skill_source_manager.py:337: in test_get_skills_by_source
    assert len(skills) == 1
E   assert 0 == 1
E    +  where 0 = len([])
```

**Example 2**:
- **nodeid**: `tests.services.skills.test_skill_discovery_service.TestSkillDiscoveryService::test_discover_skills_ignores_non_markdown_files`
- **file_hint**: `tests/services/skills/test_skill_discovery_service.py`

```
Message: assert 0 == 1
 +  where 0 = len([])

tests/services/skills/test_skill_discovery_service.py:499: in test_discover_skills_ignores_non_markdown_files
    assert len(skills) == 1
E   assert 0 == 1
E    +  where 0 = len([])
```

**Example 3**:
- **nodeid**: `tests.test_git_source_sync_phase1.TestDeploymentFromCache::test_deploy_agents_skip_up_to_date`
- **file_hint**: `tests/test_git_source_sync_phase1.py`

```
Message: assert 0 == 3
 +  where 0 = len([])

tests/test_git_source_sync_phase1.py:193: in test_deploy_agents_skip_up_to_date
    assert len(result1["deployed"]) == 3
E   assert 0 == 3
E    +  where 0 = len([])
```

## C. Hypotheses

- Behavioral changes in production code that tests have not been updated to reflect.
- Flaky assertions depending on order of execution or timing.
- Mock objects not configured to return expected values.
- Test expectations hardcoded for a previous API contract.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Compare test expectations with current API behavior
- [ ] Check for recent code changes that altered return values
- [ ] Look for hardcoded values that should be dynamic
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/agents/test_mpm_skills_manager.py`
  - `tests/cli/commands/test_agents_comprehensive.py`
  - `tests/cli/commands/test_run_comprehensive.py`
  - `tests/cli/test_agent_startup_deployment.py`
  - `tests/eval/agents/research/test_discovery_patterns.py`
  - `tests/eval/agents/research/test_integration.py`
  - `tests/eval/agents/research/test_memory_protocol.py`
  - `tests/eval/agents/research/test_output_requirements.py`
  - `tests/eval/agents/shared/test_agent_infrastructure.py`
  - `tests/eval/test_cases/test_pm_behavioral_compliance.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where AssertionError is raised in source code
rg 'raise AssertionError' src/ --type py

# Key test files to inspect
# tests/agents/test_mpm_skills_manager.py
# tests/cli/commands/test_agents_comprehensive.py
# tests/cli/commands/test_run_comprehensive.py
# tests/cli/test_agent_startup_deployment.py
# tests/eval/agents/research/test_discovery_patterns.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/services/agents/test_agent_selection_service/TestAutoConfiguration.py::test_deploy_auto_configure_dry_run' -x --tb=short
pytest 'tests/services/agents/memory/test_agent_memory_manager_comprehensive/TestAgentMemoryManager.py::test_get_memory_metrics_all_agents' -x --tb=short
pytest 'tests/eval/agents/shared/test_agent_infrastructure/TestInfrastructureIntegration.py::test_end_to_end_qa_agent' -x --tb=short
pytest 'tests/eval/agents/shared/test_agent_infrastructure/TestAgentResponseParser.py::test_parse_qa_agent_response' -x --tb=short
pytest 'tests/services/agents/sources/test_git_source_sync_service/TestGitSourceSyncService.py::test_get_agent_list_via_api' -x --tb=short
pytest 'tests/services/agents/sources/test_git_source_sync_service/TestGitSourceSyncService.py::test_get_agent_list_excludes_readme' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_deploy_auto_configure_dry_run or test_end_to_end_qa_agent or test_get_agent_list_via_api' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **334 test failures** in the `assertion_failures` category (Assertion Failures).

**Top patterns**:
  - `AssertionError: assert <N> == <N>` (15 occurrences)
  - `AssertionError: assert False` (10 occurrences)
  - `AssertionError: AssertionError: assert <N> == <N> + where <N> = len(['research.md', 'engineer.md', '` (7 occurrences)

**Sample failing tests**:
  - `tests.services.agents.test_agent_selection_service.TestAutoConfiguration::test_deploy_auto_configure_dry_run`
  - `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_get_memory_metrics_all_agents`
  - `tests.eval.agents.shared.test_agent_infrastructure.TestInfrastructureIntegration::test_end_to_end_qa_agent`
  - `tests.eval.agents.shared.test_agent_infrastructure.TestAgentResponseParser::test_parse_qa_agent_response`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/assertion_failures.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
