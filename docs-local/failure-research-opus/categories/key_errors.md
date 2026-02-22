# Key Errors

**Category**: `key_errors`

## A. Snapshot

- **Total failures in this category**: 4
- **Distinct subpatterns**: 3

### Top Exception Types

| Exception Type | Count |
|---|---|
| `KeyError` | 4 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `KeyError: KeyError: 'by_category'` | 2 |
| 2 | `KeyError: KeyError: 'input'` | 1 |
| 3 | `KeyError: KeyError: 'current_branch'` | 1 |

## B. Representative Examples

### Subpattern: `KeyError: KeyError: 'by_category'`
- **Count**: 2
- **Exception**: `KeyError`

**Example 1**:
- **nodeid**: `tests.services.analysis.test_postmortem_service.TestPostmortemService::test_analyze_session`
- **file_hint**: `tests/services/analysis/test_postmortem_service.py`

```
Message: KeyError: 'by_category'

tests/services/analysis/test_postmortem_service.py:245: in test_analyze_session
    report = service.analyze_session()
             ^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/analysis/postmortem_service.py:226: in analyze_session
    stats = self._calculate_stats(analyses, actions)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/analysis/postmortem_service.py:744: in _calculate_stats
    "by_category": stats["by_category"],
                   ^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'by_category'
```

**Example 2**:
- **nodeid**: `tests.services.analysis.test_postmortem_service.TestPostmortemService::test_report_statistics`
- **file_hint**: `tests/services/analysis/test_postmortem_service.py`

```
Message: KeyError: 'by_category'

tests/services/analysis/test_postmortem_service.py:287: in test_report_statistics
    report = service.analyze_session()
             ^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/analysis/postmortem_service.py:226: in analyze_session
    stats = self._calculate_stats(analyses, actions)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/claude_mpm/services/analysis/postmortem_service.py:744: in _calculate_stats
    "by_category": stats["by_category"],
                   ^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'by_category'
```

### Subpattern: `KeyError: KeyError: 'input'`
- **Count**: 1
- **Exception**: `KeyError`

**Example 1**:
- **nodeid**: `tests.eval.test_cases.test_pm_behavioral_compliance.TestPMDelegationBehaviors::test_delegation_behaviors[scenario11]`
- **file_hint**: `tests/eval/test_cases/test_pm_behavioral_compliance.py`

```
Message: KeyError: 'input'

tests/eval/test_cases/test_pm_behavioral_compliance.py:229: in test_delegation_behaviors
    user_input = scenario["input"]
                 ^^^^^^^^^^^^^^^^^
E   KeyError: 'input'
```

### Subpattern: `KeyError: KeyError: 'current_branch'`
- **Count**: 1
- **Exception**: `KeyError`

**Example 1**:
- **nodeid**: `tests.unit.services.version_control.test_git_operations.TestRepositoryStatus::test_get_repository_status`
- **file_hint**: `tests/unit/services/version_control/test_git_operations.py`

```
Message: KeyError: 'current_branch'

tests/unit/services/version_control/test_git_operations.py:796: in test_get_repository_status
    assert status["current_branch"] == "main"
           ^^^^^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'current_branch'
```

## C. Hypotheses

- Dictionary/JSON schema changes (renamed or removed keys).
- Missing configuration keys expected by tests.
- API response format changes not reflected in test expectations.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/eval/test_cases/test_pm_behavioral_compliance.py`
  - `tests/services/analysis/test_postmortem_service.py`
  - `tests/unit/services/version_control/test_git_operations.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where KeyError is raised in source code
rg 'raise KeyError' src/ --type py

# Key test files to inspect
# tests/eval/test_cases/test_pm_behavioral_compliance.py
# tests/services/analysis/test_postmortem_service.py
# tests/unit/services/version_control/test_git_operations.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/services/analysis/test_postmortem_service/TestPostmortemService.py::test_analyze_session' -x --tb=short
pytest 'tests/services/analysis/test_postmortem_service/TestPostmortemService.py::test_report_statistics' -x --tb=short
pytest 'tests/eval/test_cases/test_pm_behavioral_compliance/TestPMDelegationBehaviors.py::test_delegation_behaviors[scenario11]' -x --tb=short
pytest 'tests/unit/services/version_control/test_git_operations/TestRepositoryStatus.py::test_get_repository_status' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_analyze_session or test_delegation_behaviors[scenario11] or test_get_repository_status' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **4 test failures** in the `key_errors` category (Key Errors).

**Top patterns**:
  - `KeyError: KeyError: 'by_category'` (2 occurrences)
  - `KeyError: KeyError: 'input'` (1 occurrences)
  - `KeyError: KeyError: 'current_branch'` (1 occurrences)

**Sample failing tests**:
  - `tests.services.analysis.test_postmortem_service.TestPostmortemService::test_analyze_session`
  - `tests.services.analysis.test_postmortem_service.TestPostmortemService::test_report_statistics`
  - `tests.eval.test_cases.test_pm_behavioral_compliance.TestPMDelegationBehaviors::test_delegation_behaviors[scenario11]`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/key_errors.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
