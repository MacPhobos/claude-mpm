# Failure Category: key_errors

## A. Snapshot
- **Total failures**: 4
- **Top exception types**:
  - `KeyError`: 4
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `KeyError: <str> \| <unknown>` | 4 |

## B. Representative Examples

### Subpattern: `KeyError: <str> | <unknown>` (4 failures)

**Example 1**
- **nodeid**: `tests/eval/test_cases.py::test_pm_behavioral_compliance::TestPMDelegationBehaviors::test_delegation_behaviors[scenario11]`
- **file_hint**: `tests/eval/test_cases/test_pm_behavioral_compliance/TestPMDelegationBehaviors.py`
- **failure**:
```
exc_type: KeyError
message: KeyError: 'input'
--- relevant traceback (up to 30 lines) ---
tests/eval/test_cases/test_pm_behavioral_compliance.py:229: in test_delegation_behaviors
    user_input = scenario["input"]
                 ^^^^^^^^^^^^^^^^^
E   KeyError: 'input'
```

**Example 2**
- **nodeid**: `tests/services/analysis/test_postmortem_service.py::TestPostmortemService::test_analyze_session`
- **file_hint**: `tests/services/analysis/test_postmortem_service/TestPostmortemService.py`
- **failure**:
```
exc_type: KeyError
message: KeyError: 'by_category'
--- relevant traceback (up to 30 lines) ---
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

**Example 3**
- **nodeid**: `tests/services/analysis/test_postmortem_service.py::TestPostmortemService::test_report_statistics`
- **file_hint**: `tests/services/analysis/test_postmortem_service/TestPostmortemService.py`
- **failure**:
```
exc_type: KeyError
message: KeyError: 'by_category'
--- relevant traceback (up to 30 lines) ---
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

## C. Hypotheses

- Dictionary key removed or renamed in response/config schema.
- Response structure changed in upstream service mock.
- Missing default value for optional configuration key.
- Environment-specific key missing from test fixtures.
- Deserialisation producing different key names than expected.

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
pytest "tests/eval/test_cases.py::test_pm_behavioral_compliance::TestPMDelegationBehaviors::test_delegation_behaviors[scenario11]" -xvs

# Run small set for this bucket
pytest -k 'key' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the key_errors bucket:
  tests/eval/test_cases.py::test_pm_behavioral_compliance::TestPMDelegationBehaviors::test_delegation_behaviors[scenario11]

And these relevant source files:
  tests/eval/test_cases/test_pm_behavioral_compliance/TestPMDelegationBehaviors.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
