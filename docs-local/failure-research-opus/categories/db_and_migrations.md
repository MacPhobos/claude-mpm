# Database and Migration Errors

**Category**: `db_and_migrations`

## A. Snapshot

- **Total failures in this category**: 37
- **Distinct subpatterns**: 31

### Top Exception Types

| Exception Type | Count |
|---|---|
| `TypeError` | 21 |
| `AttributeError` | 9 |
| `AssertionError` | 5 |
| `NameError` | 1 |
| `FileNotFoundError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `AttributeError: AttributeError: 'AgentMemoryManager' object has no attribute '<LONG_STR>'` | 4 |
| 2 | `AttributeError: AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryM...` | 4 |
| 3 | `AssertionError: AssertionError: assert 'progress_callback' in {'force': False, 'skill_filter': {'api...` | 1 |
| 4 | `AssertionError: AssertionError: Expected 'deploy_skills'<LONG_STR>'<PATH>'), force=False, skill_filt...` | 1 |
| 5 | `AssertionError: AssertionError: assert 'average_deployment_time_ms' in {'agent_type_counts': {}, 'de...` | 1 |
| 6 | `AttributeError: AttributeError: 'TestAgentMetricsCollector' object has no attribute 'update_deployme...` | 1 |
| 7 | `NameError: NameError: name 'Config' is not defined` | 1 |
| 8 | `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '/private<PATH>` | 1 |
| 9 | `AssertionError: Failed: Configuration validation failed: assert 'context_management' in {'skills': {...` | 1 |
| 10 | `TypeError: TypeError: TestRunCommandMigration.test_command_initialization() takes <N> positional arg...` | 1 |
| 11 | `TypeError: TypeError: TestRunCommandMigration.test_validate_args_minimal() takes <N> positional argu...` | 1 |
| 12 | `TypeError: TypeError: TestRunCommandMigration.test_run_success() takes <N> positional argument but <...` | 1 |
| 13 | `TypeError: TypeError: TestRunCommandMigration.test_run_failure() takes <N> positional argument but <...` | 1 |
| 14 | `TypeError: TypeError: TestRunCommandMigration.test_run_keyboard_interrupt() takes <N> positional arg...` | 1 |
| 15 | `TypeError: TypeError: TestRunCommandMigration.test_execute_run_session_delegates_to_legacy() takes <...` | 1 |

## B. Representative Examples

### Subpattern: `AttributeError: AttributeError: 'AgentMemoryManager' object has no attribute '<LONG_STR>'`
- **Count**: 4
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_get_memory_file_with_migration_no_existing_files`
- **file_hint**: `tests/services/agents/memory/test_agent_memory_manager_comprehensive.py`

```
Message: AttributeError: 'AgentMemoryManager' object has no attribute '_get_memory_file_with_migration'

tests/services/agents/memory/test_agent_memory_manager_comprehensive.py:100: in test_get_memory_file_with_migration_no_existing_files
    result = manager._get_memory_file_with_migration(directory, agent_id)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'AgentMemoryManager' object has no attribute '_get_memory_file_with_migration'
```

**Example 2**:
- **nodeid**: `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_get_memory_file_with_migration_from_old_agent_format`
- **file_hint**: `tests/services/agents/memory/test_agent_memory_manager_comprehensive.py`

```
Message: AttributeError: 'AgentMemoryManager' object has no attribute '_get_memory_file_with_migration'

tests/services/agents/memory/test_agent_memory_manager_comprehensive.py:125: in test_get_memory_file_with_migration_from_old_agent_format
    result = manager._get_memory_file_with_migration(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'AgentMemoryManager' object has no attribute '_get_memory_file_with_migration'
```

**Example 3**:
- **nodeid**: `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_get_memory_file_with_migration_from_simple_format`
- **file_hint**: `tests/services/agents/memory/test_agent_memory_manager_comprehensive.py`

```
Message: AttributeError: 'AgentMemoryManager' object has no attribute '_get_memory_file_with_migration'

tests/services/agents/memory/test_agent_memory_manager_comprehensive.py:156: in test_get_memory_file_with_migration_from_simple_format
    result = manager._get_memory_file_with_migration(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'AgentMemoryManager' object has no attribute '_get_memory_file_with_migration'
```

### Subpattern: `AttributeError: AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryManager object at <HE`
- **Count**: 4
- **Exception**: `AttributeError`

**Example 1**:
- **nodeid**: `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_load_memory_existing_file`
- **file_hint**: `tests/services/agents/memory/test_agent_memory_manager_comprehensive.py`

```
Message: AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryManager object at 0x1133e9010> does not have the attribute '_get_memory_file_with_migration'

tests/services/agents/memory/test_agent_memory_manager_comprehensive.py:566: in test_load_memory_existing_file
    with patch.object(manager, "_get_memory_file_with_migration") as mock_get_file:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1467: in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1437: in get_original
    raise AttributeError(
E   AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryManager object at 0x1133e9010> does not have the attribute '_get_memory_file_with_migration'
```

**Example 2**:
- **nodeid**: `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_load_memory_create_default`
- **file_hint**: `tests/services/agents/memory/test_agent_memory_manager_comprehensive.py`

```
Message: AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryManager object at 0x1133afb60> does not have the attribute '_get_memory_file_with_migration'

tests/services/agents/memory/test_agent_memory_manager_comprehensive.py:581: in test_load_memory_create_default
    with patch.object(manager, "_get_memory_file_with_migration") as mock_get_file:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1467: in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1437: in get_original
    raise AttributeError(
E   AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryManager object at 0x1133afb60> does not have the attribute '_get_memory_file_with_migration'
```

**Example 3**:
- **nodeid**: `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_load_memory_read_error`
- **file_hint**: `tests/services/agents/memory/test_agent_memory_manager_comprehensive.py`

```
Message: AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryManager object at 0x113379220> does not have the attribute '_get_memory_file_with_migration'

tests/services/agents/memory/test_agent_memory_manager_comprehensive.py:722: in test_load_memory_read_error
    with patch.object(manager, "_get_memory_file_with_migration") as mock_get_file:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1467: in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1437: in get_original
    raise AttributeError(
E   AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryManager object at 0x113379220> does not have the attribute '_get_memory_file_with_migration'
```

### Subpattern: `AssertionError: AssertionError: assert 'progress_callback' in {'force': False, 'skill_filter': {'api-documentation', 'br`
- **Count**: 1
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.cli.test_skills_startup_sync.TestTwoPhaseProgressBars::test_progress_callback_invoked_during_deploy`
- **file_hint**: `tests/cli/test_skills_startup_sync.py`

```
Message: AssertionError: assert 'progress_callback' in {'force': False, 'skill_filter': {'api-documentation', 'brainstorming', 'condition-based-waiting', 'database-migration...audit', 'dispatching-parallel-agents', ...}, 'target_dir': PosixPath('/Users/mac/workspace/claude-mpm-tests/.claude/skills')}

tests/cli/test_skills_startup_sync.py:322: in test_progress_callback_invoked_during_deploy
    assert "progress_callback" in call_args[1]
E   AssertionError: assert 'progress_callback' in {'force': False, 'skill_filter': {'api-documentation', 'brainstorming', 'condition-based-waiting', 'database-migration...audit', 'dispatching-parallel-agents', ...}, 'target_dir': PosixPath('/Users/mac/workspace/claude-mpm-tests/.claude/skills')}
```

### Subpattern: `AssertionError: AssertionError: Expected 'deploy_skills'<LONG_STR>'<PATH>'), force=False, skill_filter={`
- **Count**: 1
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.cli.test_skills_startup_sync.TestTwoPhaseProgressBars::test_no_deploy_when_no_sync_results`
- **file_hint**: `tests/cli/test_skills_startup_sync.py`

```
Message: AssertionError: Expected 'deploy_skills' to not have been called. Called 1 times.
Calls: [call(target_dir=PosixPath('/Users/mac/workspace/claude-mpm-tests/.claude/skills'), force=False, skill_filter={'mpm-delegation-patterns', 'git-worktrees', 'stacked-prs', 'web-performance-optimization', 'test-dri

tests/cli/test_skills_startup_sync.py:362: in test_no_deploy_when_no_sync_results
    mock_manager.deploy_skills.assert_not_called()
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:910: in assert_not_called
    raise AssertionError(msg)
E   AssertionError: Expected 'deploy_skills' to not have been called. Called 1 times.
E   Calls: [call(target_dir=PosixPath('/Users/mac/workspace/claude-mpm-tests/.claude/skills'), force=False, skill_filter={'mpm-delegation-patterns', 'git-worktrees', 'stacked-prs', 'web-performance-optimization', 'test-driven-development', 'git-workflow', 'internal-comms', 'mpm-bug-reporting', 'mpm-teaching-mode', 'verification-before-completion', 'requesting-code-review', 'github-actions', 'dependency-audit', 'emergency-release-workflow', 'condition-based-waiting', 'writing-plans', 'mpm-circuit-breaker-enforcement', 'netlify', 'env-manager', 'security-scanning', 'dispatching-parallel-agents', 'mpm-git-file-tracking', 'json-data-handling', 'screenshot-verification', 'root-cause-tracing', 'mpm-verification-protocols', 'mpm-pr-workflow', 'api-documentation', 'database-migration', 'test-quality-inspector', 'brainstorming', 'docker', 'mpm-ticketing-integration', 'playwright', 'mpm-tool-usage-guide', 'vercel-overview', 'webapp-testing', 'systematic-debugging', 'testing-anti-patterns', 'mpm-session-management'}),
E    call().get('deployed_count', 0),
E    call().get('skipped_count', 0),
E    call().get('filtered_count', 0),
E    call().get('removed_count', 0),
E    call().get().__add__(<MagicMock name='GitSkillSourceManager().deploy_skills().get()' id='4643712192'>),
E    call().get().__add__().__gt__(0)].
```

### Subpattern: `AssertionError: AssertionError: assert 'average_deployment_time_ms' in {'agent_type_counts': {}, 'deployment_errors': {}`
- **Count**: 1
- **Exception**: `AssertionError`

**Example 1**:
- **nodeid**: `tests.test_agent_deployment_baseline.TestAgentDeploymentServiceBaseline::test_get_deployment_metrics`
- **file_hint**: `tests/test_agent_deployment_baseline.py`

```
Message: AssertionError: assert 'average_deployment_time_ms' in {'agent_type_counts': {}, 'deployment_errors': {}, 'failed_deployments': 0, 'migrations_performed': 0, ...}

tests/test_agent_deployment_baseline.py:181: in test_get_deployment_metrics
    assert "average_deployment_time_ms" in metrics  # Actual field name
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AssertionError: assert 'average_deployment_time_ms' in {'agent_type_counts': {}, 'deployment_errors': {}, 'failed_deployments': 0, 'migrations_performed': 0, ...}
```

## C. Hypotheses

- Database not initialized or migrated before tests run.
- SQLAlchemy session/connection not properly managed in async context.
- Test database schema out of sync with model definitions.
- Missing database fixtures or connection pool exhaustion.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/cli/test_skills_startup_sync.py`
  - `tests/services/agents/memory/test_agent_memory_manager_comprehensive.py`
  - `tests/test_agent_deployment_baseline.py`
  - `tests/test_agent_deployment_system.py`
  - `tests/test_agent_metrics_collector.py`
  - `tests/test_memory_migration.py`
  - `tests/test_resume_log_system.py`
  - `tests/test_run_command_migration/TestRunCommandMigration.py`
  - `tests/test_tickets_command_migration/TestTicketsCommandMigration.py`
  - `tests/test_unified_config.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where AssertionError is raised in source code
rg 'raise AssertionError' src/ --type py

# Find where AttributeError is raised in source code
rg 'raise AttributeError' src/ --type py

# Search for 'has' references
rg 'has' src/ --type py -l

# Search for '_get_memory_file_with_migration' references
rg '_get_memory_file_with_migration' src/ --type py -l

# Search for 'at' references
rg 'at' src/ --type py -l

# Key test files to inspect
# tests/cli/test_skills_startup_sync.py
# tests/services/agents/memory/test_agent_memory_manager_comprehensive.py
# tests/test_agent_deployment_baseline.py
# tests/test_agent_deployment_system.py
# tests/test_agent_metrics_collector.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/services/agents/memory/test_agent_memory_manager_comprehensive/TestAgentMemoryManager.py::test_get_memory_file_with_migration_no_existing_files' -x --tb=short
pytest 'tests/services/agents/memory/test_agent_memory_manager_comprehensive/TestAgentMemoryManager.py::test_get_memory_file_with_migration_from_old_agent_format' -x --tb=short
pytest 'tests/services/agents/memory/test_agent_memory_manager_comprehensive/TestAgentMemoryManager.py::test_load_memory_existing_file' -x --tb=short
pytest 'tests/services/agents/memory/test_agent_memory_manager_comprehensive/TestAgentMemoryManager.py::test_load_memory_create_default' -x --tb=short
pytest 'tests/cli/test_skills_startup_sync/TestTwoPhaseProgressBars.py::test_progress_callback_invoked_during_deploy' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_get_memory_file_with_migration_no_existing_files or test_load_memory_existing_file or test_progress_callback_invoked_during_deploy' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **37 test failures** in the `db_and_migrations` category (Database and Migration Errors).

**Top patterns**:
  - `AttributeError: AttributeError: 'AgentMemoryManager' object has no attribute '<LONG_STR>'` (4 occurrences)
  - `AttributeError: AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryM` (4 occurrences)
  - `AssertionError: AssertionError: assert 'progress_callback' in {'force': False, 'skill_filter': {'api` (1 occurrences)

**Sample failing tests**:
  - `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_get_memory_file_with_migration_no_existing_files`
  - `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_get_memory_file_with_migration_from_old_agent_format`
  - `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_load_memory_existing_file`
  - `tests.services.agents.memory.test_agent_memory_manager_comprehensive.TestAgentMemoryManager::test_load_memory_create_default`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/db_and_migrations.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
