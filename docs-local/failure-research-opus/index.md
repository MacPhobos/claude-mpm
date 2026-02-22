# Failure Research Index

## Summary

- **Total tests**: 7,330
- **Passed**: 5,552
- **Failures**: 1,560
- **Errors**: 166
- **Skipped**: 52
- **Pass rate**: 75.7%
- **Failure + Error rate**: 23.5%

## Categories

| Category | Count | % of Failures | Subpatterns | Link |
|---|---|---|---|---|
| [Attribute Errors](categories/attribute_errors.md) | 448 | 26.0% | 171 | [view](categories/attribute_errors.md) |
| [Type Errors](categories/type_errors.md) | 425 | 24.6% | 382 | [view](categories/type_errors.md) |
| [Assertion Failures](categories/assertion_failures.md) | 334 | 19.4% | 239 | [view](categories/assertion_failures.md) |
| [Fixture and Setup Errors](categories/fixtures_and_setup.md) | 277 | 16.0% | 45 | [view](categories/fixtures_and_setup.md) |
| [File and Filesystem Errors](categories/file_and_fs.md) | 103 | 6.0% | 10 | [view](categories/file_and_fs.md) |
| [Uncategorized / Unknown Errors](categories/unknown.md) | 56 | 3.2% | 11 | [view](categories/unknown.md) |
| [Database and Migration Errors](categories/db_and_migrations.md) | 37 | 2.1% | 31 | [view](categories/db_and_migrations.md) |
| [Import Errors and Environment Issues](categories/imports_and_env.md) | 13 | 0.8% | 8 | [view](categories/imports_and_env.md) |
| [Value Errors](categories/value_errors.md) | 12 | 0.7% | 3 | [view](categories/value_errors.md) |
| [Timeout Errors](categories/timeouts.md) | 7 | 0.4% | 7 | [view](categories/timeouts.md) |
| [Network and HTTP Errors](categories/network_and_http.md) | 6 | 0.3% | 3 | [view](categories/network_and_http.md) |
| [Key Errors](categories/key_errors.md) | 4 | 0.2% | 3 | [view](categories/key_errors.md) |
| [Runtime Errors](categories/runtime_errors.md) | 3 | 0.2% | 1 | [view](categories/runtime_errors.md) |
| [Not Implemented Errors](categories/not_implemented.md) | 1 | 0.1% | 1 | [view](categories/not_implemented.md) |

## Top 10 Exception Types

| Exception Type | Count |
|---|---|
| `AttributeError` | 511 |
| `TypeError` | 450 |
| `AssertionError` | 342 |
| `NameError` | 220 |
| `FileNotFoundError` | 111 |
| `FixtureLookupError` | 38 |
| `ValueError` | 12 |
| `ModuleNotFoundError` | 8 |
| `ImportError` | 4 |
| `KeyError` | 4 |

## Top 10 Failing Modules

| Module | Count |
|---|---|
| `tests.eval.test_cases` | 83 |
| `tests.unit.services` | 75 |
| `tests.services.agents` | 73 |
| `tests.agents.test_mpm_skills_manager` | 70 |
| `tests.services.test_socketio_handlers` | 54 |
| `tests.cli.test_shared_utilities` | 34 |
| `tests.mcp.test_session_server_http` | 33 |
| `tests.hooks.claude_hooks` | 32 |
| `tests.test_agent_configuration_manager.TestAgentConfigurationManager` | 27 |
| `tests.cli.test_base_command` | 26 |

## Recommended Priority: First 3 Buckets to Tackle

### 1. [Fixture and Setup Errors](categories/fixtures_and_setup.md)

- **Count**: 277 failures
- **Subpatterns**: 45
- **Top subpattern covers**: 113/277 (41%)
- **Rationale**: High blast radius + infrastructure issue (fix once, fix many)

### 2. [File and Filesystem Errors](categories/file_and_fs.md)

- **Count**: 103 failures
- **Subpatterns**: 10
- **Top subpattern covers**: 78/103 (76%)
- **Rationale**: High blast radius + likely single root cause

### 3. [Attribute Errors](categories/attribute_errors.md)

- **Count**: 448 failures
- **Subpatterns**: 171
- **Top subpattern covers**: 42/448 (9%)
- **Rationale**: High blast radius
