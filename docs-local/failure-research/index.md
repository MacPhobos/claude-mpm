# Pytest Failure Analysis Report

Generated: 2026-02-22 10:09:34
Source: `/Users/mac/workspace/claude-mpm/reports/junit.xml`

## Summary
- **Total tests**: 7330
- **Failures**: 1560
- **Errors**: 166
- **Pass rate**: 76.5%

## Category Breakdown

| Category | Count | % of Failures | Link |
|---|---|---|---|
| attribute_errors | 512 | 29.7% | [link](categories/attribute_errors.md) |
| type_errors | 448 | 26.0% | [link](categories/type_errors.md) |
| assertion_failures | 372 | 21.6% | [link](categories/assertion_failures.md) |
| unknown | 210 | 12.2% | [link](categories/unknown.md) |
| file_and_fs | 74 | 4.3% | [link](categories/file_and_fs.md) |
| parametrize_and_collection | 39 | 2.3% | [link](categories/parametrize_and_collection.md) |
| fixtures_and_setup | 38 | 2.2% | [link](categories/fixtures_and_setup.md) |
| imports_and_env | 12 | 0.7% | [link](categories/imports_and_env.md) |
| value_errors | 12 | 0.7% | [link](categories/value_errors.md) |
| key_errors | 4 | 0.2% | [link](categories/key_errors.md) |
| network_and_http | 4 | 0.2% | [link](categories/network_and_http.md) |
| db_and_migrations | 1 | 0.1% | [link](categories/db_and_migrations.md) |

## Top 10 Exception Types

| Exception Type | Count |
|---|---|
| `AttributeError` | 457 |
| `TypeError` | 448 |
| `AssertionError` | 275 |
| `(unknown)` | 236 |
| `NameError` | 158 |
| `FileNotFoundError` | 98 |
| `ValueError` | 12 |
| `ModuleNotFoundError` | 6 |
| `KeyError` | 4 |
| `RuntimeError` | 4 |

## Top 10 Failing Modules/Paths

| Module/Path | Count |
|---|---|
| `tests/services/agents/memory/test_agent_memory_manager_comprehensive/TestAgentMemoryManager.py` | 33 |
| `tests/test_agent_configuration_manager/TestAgentConfigurationManager.py` | 27 |
| `tests/test_agent_format_converter/TestAgentFormatConverter.py` | 24 |
| `tests/eval/test_cases/test_pm_behavioral_compliance/TestPMCircuitBreakerBehaviors.py` | 23 |
| `tests/services/test_runner_configuration_service/TestRunnerConfigurationService.py` | 23 |
| `tests/test_agent_version_manager/TestAgentVersionManager.py` | 23 |
| `tests/eval/test_cases/test_pm_behavioral_compliance/TestPMWorkflowBehaviors.py` | 19 |
| `tests/services/test_socketio_handlers/TestGitEventHandler.py` | 19 |
| `tests/test_schema_standardization/TestSchemaStandardization.py` | 17 |
| `tests/test_path_resolver/TestUnifiedPathManager.py` | 17 |

## Recommended Priority Order

### 1. [imports_and_env](categories/imports_and_env.md) (12 failures)
Reason: Infrastructure failure — fixing unblocks all other tests in affected modules.

### 2. [fixtures_and_setup](categories/fixtures_and_setup.md) (38 failures)
Reason: Fixture failures cascade — one broken fixture can fail dozens of tests.

### 3. [parametrize_and_collection](categories/parametrize_and_collection.md) (39 failures)
Reason: Collection failures prevent tests from running at all.

### 4. [db_and_migrations](categories/db_and_migrations.md) (1 failures)
Reason: Database setup issues block all DB-dependent tests simultaneously.

### 5. [network_and_http](categories/network_and_http.md) (4 failures)
Reason: Network failures likely have a single mocking/config root cause.

### 6. [file_and_fs](categories/file_and_fs.md) (74 failures)
Reason: File-system failures often share a single path or permission root cause.

### 7. [type_errors](categories/type_errors.md) (448 failures)
Reason: API contract changes — fix signature mismatches.

### 8. [attribute_errors](categories/attribute_errors.md) (512 failures)
Reason: Attribute renames — usually straightforward refactoring fixes.

### 9. [value_errors](categories/value_errors.md) (12 failures)
Reason: Validation/logic issues — review per test.

### 10. [key_errors](categories/key_errors.md) (4 failures)
Reason: Schema/dict key changes — review per test.

### 11. [assertion_failures](categories/assertion_failures.md) (372 failures)
Reason: Logic drift — product logic tests after infrastructure stable.

### 12. [unknown](categories/unknown.md) (210 failures)
Reason: Investigate individually after other categories are resolved.

## Quick Links
- [failures.jsonl](data/failures.jsonl) — raw structured data
- [categories.json](data/categories.json) — category/subpattern data
