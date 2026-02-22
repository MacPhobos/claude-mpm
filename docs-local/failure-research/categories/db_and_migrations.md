# Failure Category: db_and_migrations

## A. Snapshot
- **Total failures**: 1
- **Top exception types**:
  - `Failed`: 1
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `Failed: Configuration validation failed: assert <str> in {<str>: {<str>: [<str>, <str>, <str>, <str>, <str>, <str>, ...] \| <unknown>` | 1 |

## B. Representative Examples

### Subpattern: `Failed: Configuration validation failed: assert <str> in {<str>: {<str>: [<str>, <str>, <str>, <str>, <str>, <str>, ...] | <unknown>` (1 failures)

**Example 1**
- **nodeid**: `tests/test_resume_log_system.py::TestConfigurationIntegration::test_load_context_management_config`
- **file_hint**: `tests/test_resume_log_system/TestConfigurationIntegration.py`
- **failure**:
```
exc_type: Failed
message: Failed: Configuration validation failed: assert 'context_management' in {'skills': {'agent_referenced': ['anthropic-sdk', 'api-documentation', 'brainstorming', 'bug-fix-verification', 'condition-based-waiting', 'database-migration', ...], 'user_defined': []}}
--- relevant traceback (up to 30 lines) ---
tests/test_resume_log_system.py:473: in test_load_context_management_config
    assert "context_management" in config
E   AssertionError: assert 'context_management' in {'skills': {'agent_referenced': ['anthropic-sdk', 'api-documentation', 'brainstorming', 'bug-fix-verification', 'condition-based-waiting', 'database-migration', ...], 'user_defined': []}}

During handling of the above exception, another exception occurred:
tests/test_resume_log_system.py:492: in test_load_context_management_config
    pytest.fail(f"Configuration validation failed: {e}")
E   Failed: Configuration validation failed: assert 'context_management' in {'skills': {'agent_referenced': ['anthropic-sdk', 'api-documentation', 'brainstorming', 'bug-fix-verification', 'condition-based-waiting', 'database-migration', ...], 'user_defined': []}}
```

## C. Hypotheses

- Test database not created or migrations not applied before tests run.
- Database connection string not set in test environment.
- Connection pool exhausted due to leaked connections in prior tests.
- Schema drift: model changed but migration not generated.
- Foreign key constraint violated by test data setup.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Verify test DB is created and migrations applied in CI setup script.
- [ ] Check `DATABASE_URL` env var is configured for test environment.
- [ ] Run `alembic history` / `manage.py showmigrations` to verify migration state.
- [ ] Look for connection leaks in test teardown fixtures.

## E. Targeted Repo Queries

```bash
rg "DATABASE_URL|db_session|engine" src/ tests/ --include="*.py"
rg "create_engine|sessionmaker" src/ --include="*.py"
rg "alembic|migrate" . --include="*.py" --include="*.cfg" -l
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/test_resume_log_system.py::TestConfigurationIntegration::test_load_context_management_config" -xvs

# Run small set for this bucket
pytest -k 'db or database or migration' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the db_and_migrations bucket:
  tests/test_resume_log_system.py::TestConfigurationIntegration::test_load_context_management_config

And these relevant source files:
  tests/test_resume_log_system/TestConfigurationIntegration.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
