# Test Failure Remediation Plan

Generated: 2026-02-22
Based on: [Failure Analysis Report](index.md)

## Overview

- **Total tests**: 7,330
- **Total failing**: 1,726 (1,560 failures + 166 errors)
- **Pass rate**: 76.5%
- **Goal**: Systematic resolution prioritized by leverage and cascade benefit

---

## Phase 1: Infrastructure Fixes (Est. 89 failures → likely 3–5 root causes)

> **Rationale**: Infrastructure failures (imports, fixtures, collection) cascade — a single broken fixture or missing dependency can fail dozens of tests. Fix these first to get a true picture of remaining failures.

### 1a. Imports &amp; Environment (12 failures)

- **Category file**: [imports_and_env.md](categories/imports_and_env.md)
- **Likely root causes**: Missing dependencies in test environment, missing env vars in test harness, conditional imports that changed
- **Action**:
  1. Research agent reads `imports_and_env.md` subpatterns
  2. Identify the specific missing modules/env vars
  3. Fix: add to `pyproject.toml` test deps, update test fixtures/conftest to set env vars
  4. Re-run the 12 failing tests to confirm fix
- **Expected cascade**: May unblock tests that fail later in the stack

### 1b. Fixtures &amp; Setup (38 failures)

- **Category file**: [fixtures_and_setup.md](categories/fixtures_and_setup.md)
- **Likely root causes**: Fixture scope mismatches, missing fixtures after refactor, conftest.py changes
- **Action**:
  1. Research agent reads subpatterns — group by fixture name
  2. For each broken fixture: check scope (function vs session vs module), check if it was renamed/moved
  3. Fix fixture definitions in conftest.py files
  4. Re-run the 38 failing tests
- **Expected cascade**: Fixtures are shared — fixing one may unblock 10–50 tests across other categories

### 1c. Parametrize &amp; Collection (39 failures)

- **Category file**: [parametrize_and_collection.md](categories/parametrize_and_collection.md)
- **Likely root causes**: Invalid parametrize arguments, collection errors from syntax issues, PytestUnraisableExceptionWarning
- **Action**:
  1. Research agent reads subpatterns
  2. Fix parametrize decorators and collection issues
  3. Re-run the 39 failing tests
- **Expected cascade**: Tests that couldn't collect will now run (may pass or reveal real failures)

### Phase 1 Exit Criteria
- [ ] All 89 infrastructure failures resolved or re-categorized
- [ ] Full test suite re-run to measure cascade impact
- [ ] Updated failure counts for Phases 2–4

---

## Phase 2: Interface Drift — AttributeError + TypeError (Est. 960 failures)

> **Rationale**: These two categories alone are 55.7% of all failures. The pattern strongly indicates API/interface changes — objects lost attributes, function signatures changed, return types shifted. A few root causes likely explain hundreds of failures.

### 2a. AttributeError (512 failures)

- **Category file**: [attribute_errors.md](categories/attribute_errors.md)
- **Strategy**: Work top-down through subpatterns by count
- **Action**:
  1. Research agent reads subpatterns — identify the top 5 by count
  2. For each subpattern: identify which class/module changed and what attribute is missing
  3. Determine if the fix is: rename attribute, add backward compat, or update test expectations
  4. Engineer implements fixes, starting with highest-count subpattern
  5. Re-run affected tests after each fix to measure progress
- **Expected leverage**: Top 3 subpatterns likely cover 60–70% of the 512

### 2b. TypeError (448 failures)

- **Category file**: [type_errors.md](categories/type_errors.md)
- **Strategy**: Same as 2a — top-down by subpattern count
- **Action**:
  1. Research agent reads subpatterns — identify the top 5 by count
  2. For each: identify the changed function signature or return type
  3. Fix: update call sites, add type coercion, or update test expectations
  4. Engineer implements, re-run after each fix
- **Expected leverage**: Similar to 2a — a handful of signature changes likely cause most failures

### Phase 2 Exit Criteria
- [ ] AttributeError count reduced by ≥80%
- [ ] TypeError count reduced by ≥80%
- [ ] Full test suite re-run to measure total progress
- [ ] Remaining failures re-categorized if needed

---

## Phase 3: Assertion Failures (Est. 372 failures)

> **Rationale**: These are tests that *ran correctly* but got *wrong results*. They represent actual behavioral changes in the codebase. Tackle after infrastructure and interface fixes are stable.

- **Category file**: [assertion_failures.md](categories/assertion_failures.md)
- **Strategy**:
  1. After Phases 1–2, re-run full suite — some assertion failures may resolve as side effects
  2. Group remaining assertion failures by module/feature area
  3. For each group: determine if the test expectation or the code behavior is wrong
  4. Fix tests (if behavior change was intentional) or fix code (if regression)
- **Key question per failure**: "Was the behavior change intentional?"
  - If yes → update test expectations
  - If no → this is a real bug, fix the source code

### Phase 3 Exit Criteria
- [ ] All assertion failures triaged as intentional-change or regression
- [ ] Intentional changes: tests updated
- [ ] Regressions: source code fixed
- [ ] Re-run confirms fixes

---

## Phase 4: Mop-up (Est. 284+ remaining failures)

> **Rationale**: Smaller categories and the `unknown` bucket. Some may have already been resolved by earlier phases.

| Bucket | Count | Notes |
|---|---|---|
| `unknown` | 210 | Review for new categorization rules; may shrink after Phases 1–3 |
| `file_and_fs` | 74 | Missing test fixtures/data files, path changes |
| `value_errors` | 12 | Invalid arguments, configuration issues |
| `key_errors` | 4 | Missing dict keys — likely API response changes |
| `network_and_http` | 4 | Mock/stub issues or missing test server |
| `db_and_migrations` | 1 | DB setup in test harness |

- **Action**:
  1. Re-run full suite after Phases 1–3
  2. Re-parse results into updated categories
  3. Fix remaining failures by category
  4. Refine `unknown` bucket — add new regex rules if patterns emerge

### Phase 4 Exit Criteria
- [ ] `unknown` bucket reduced to &lt;20 failures
- [ ] All other buckets at zero or explicitly skipped with justification
- [ ] Final pass rate ≥95%

---

## Execution Model

### Sequential (Conservative)
```
Phase 1 (1a → 1b → 1c) → Re-run → Phase 2 (2a → 2b) → Re-run → Phase 3 → Re-run → Phase 4
```
**Pros**: Clear measurement at each step, no conflicting fixes
**Cons**: Slower

### Parallel (Aggressive)
```
Phase 1 (all parallel) ──┐
Phase 2a (attr errors) ──┼── Merge → Full re-run → Phase 3 → Phase 4
Phase 2b (type errors) ──┘
```
**Pros**: Faster wall-clock time
**Cons**: May have merge conflicts; harder to attribute which fix resolved which tests

### Recommended: **Hybrid**
1. Run Phase 1 sequentially (small, fast, high cascade)
2. Re-run full suite to measure impact
3. Run Phase 2a and 2b in parallel (independent categories)
4. Re-run full suite
5. Phase 3 and 4 sequentially

---

## Progress Tracking

After each phase, regenerate the failure analysis:
```bash
python scripts/analyze_failures.py
```

Compare category counts phase-over-phase:

| Category | Before | After Ph1 | After Ph2 | After Ph3 | Final |
|---|---|---|---|---|---|
| imports_and_env | 12 | | | | |
| fixtures_and_setup | 38 | | | | |
| parametrize_and_collection | 39 | | | | |
| attribute_errors | 512 | | | | |
| type_errors | 448 | | | | |
| assertion_failures | 372 | | | | |
| unknown | 210 | | | | |
| file_and_fs | 74 | | | | |
| value_errors | 12 | | | | |
| key_errors | 4 | | | | |
| network_and_http | 4 | | | | |
| db_and_migrations | 1 | | | | |
| **TOTAL** | **1,726** | | | | |

---

## Success Criteria

| Metric | Target |
|---|---|
| Pass rate | ≥95% (from current 76.5%) |
| Infrastructure failures | 0 |
| Attribute + Type errors | ≤50 (from 960) |
| Unknown bucket | &lt;20 |
| Total failing | &lt;365 (≤5% of 7,330) |

---

## Quick Start

To begin Phase 1, use this Claude prompt:

```
Read the following failure category files and identify the root causes:
- docs-local/failure-research/categories/imports_and_env.md
- docs-local/failure-research/categories/fixtures_and_setup.md
- docs-local/failure-research/categories/parametrize_and_collection.md

For each category:
1. List the distinct root causes from the subpatterns
2. Propose specific fixes (file path + change description)
3. Estimate how many failures each fix resolves

Do not implement yet — just produce the diagnosis.
```
