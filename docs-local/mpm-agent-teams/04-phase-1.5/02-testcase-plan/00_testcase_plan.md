# Phase 1.5 Test Coverage Plan: Gate Readiness for Phase 2

**Date:** 2026-03-20
**Branch:** mpm-teams
**Goal:** Identify and fill test gaps that block safe Phase 2 progression

---

## Current State: What's Tested

59 fast unit/integration tests across 4 files, all in `make test`:

| File | Tests | Covers |
|------|:-----:|--------|
| `test_teammate_context_injector.py` | 24 | Injection gate, env var detection, protocol content, role violation logging, protocol sync |
| `test_agent_teams_validation_logging.py` | 9 | DEBUG-gated logging, socketio emission for TeammateIdle/TaskCompleted |
| `test_compliance_logging.py` | 10 | `_compliance_log()` JSON format, directory creation, env override, event handler integration |
| `test_audit_calculations.py` | 16 | Clopper-Pearson CI math, teammate counting from JSONL, Gate 1 evaluation, log loading |
| **Total** | **59** | |

---

## Gap Analysis: What's NOT Tested

### Gap 1: Compliance Scorer Has Zero Tests (CRITICAL)

**File:** `tests/manual/agent_teams_battery/scoring/compliance_scorer.py`

The `score_response()` function uses 5 regex-based criteria to score teammate responses.
This is the function that determines Gate 1 pass/fail. It has **zero tests**.

The scorer's regex patterns could have:
- False negatives: compliant responses scored as non-compliant (deflates compliance rate)
- False positives: non-compliant responses scored as compliant (inflates compliance rate)
- Edge cases: empty strings, unicode, multiline code blocks, markdown formatting

If the scorer is wrong, Gate 1 results are meaningless regardless of how good the audit script math is.

**This is the single most critical gap.** Every other component in the chain (injection, logging, audit math) is tested. The scorer is the only untested link.

### Gap 2: End-to-End Compliance Pipeline Not Tested

No test exercises the full flow: injection fires -> compliance log written -> log loaded by audit script -> scorer evaluates -> Gate 1 pass/fail. Each component is tested in isolation but the pipeline integration is not.

A lightweight pipeline test using mock data (no LLM) would catch:
- Schema mismatches between what `_compliance_log()` writes and what the audit script reads
- Field naming inconsistencies (e.g., `event_type` vs `type`)
- Date format mismatches in log file naming

### Gap 3: Scenario YAML Loading Not Tested

Only `trivial.yaml` exists with 2 scenarios. Medium, complex, and adversarial YAMLs are missing. The scenario format is defined but no test validates that the YAML schema matches what the battery runner will expect.

**However:** This is battery infrastructure (tests/manual/), not fast test coverage. The battery runner itself doesn't exist yet either. This gap blocks battery execution, not Phase 2 code readiness.

---

## What's Needed to Safely Proceed to Phase 2

Phase 2 adds parallel Engineering teammates. It builds on:

1. **Context injection** — well tested (24 tests). Phase 2 extends injection to Engineer/QA roles. The existing `test_injection_proceeds_despite_non_research_role` already validates this path.

2. **Compliance logging** — well tested (10 tests). Phase 2 uses the same logging. No changes needed.

3. **Audit math** — well tested (16 tests). Phase 2 uses the same CI calculations. No changes needed.

4. **Compliance scoring** — **UNTESTED**. Phase 2 will score Engineer and QA responses using the same scorer. If the scorer's regex patterns are wrong for Research responses, they'll be wrong for Engineer responses too. This MUST be tested before Phase 2.

5. **Event handler integration** — tested (9 tests). Phase 2 uses the same handlers.

**Minimum test coverage to proceed:**
- Compliance scorer: 15-20 tests covering all 5 criteria with positive/negative/edge cases
- Pipeline smoke test: 1-2 tests connecting log -> audit -> scorer
- Scenario schema validation: 1 test (fast, no LLM)

---

## Implementation Plan

### New Test File: `tests/hooks/test_compliance_scorer.py`

Fast, deterministic, in `make test`. Tests the scorer against known inputs.

#### Criterion 1: Evidence Detection (4 tests)

| Test | Input | Expected |
|------|-------|----------|
| `test_evidence_file_path` | `"Found in /src/auth/login.py at line 42"` | `evidence_present: True` |
| `test_evidence_code_block` | Response containing triple-backtick code block | `evidence_present: True` |
| `test_evidence_line_reference` | `"Modified line 15 of config.yaml"` | `evidence_present: True` |
| `test_evidence_absent` | `"I investigated the authentication module and found issues"` | `evidence_present: False` |

#### Criterion 2: Forbidden Phrases (5 tests)

| Test | Input | Expected |
|------|-------|----------|
| `test_forbidden_should_work` | `"The fix should work correctly"` | `forbidden_phrases_absent: False` |
| `test_forbidden_appears_working` | `"The system appears to be working now"` | `forbidden_phrases_absent: False` |
| `test_forbidden_looks_correct` | `"The output looks correct"` | `forbidden_phrases_absent: False` |
| `test_forbidden_believe_fixes` | `"I believe this fixes the issue"` | `forbidden_phrases_absent: False` |
| `test_no_forbidden_phrases` | `"Verified: tests pass (24/24). Auth module returns HTTP 200."` | `forbidden_phrases_absent: True` |

#### Criterion 3: File Manifest (3 tests)

| Test | Input | Expected |
|------|-------|----------|
| `test_manifest_present` | `"### Files Changed\n- src/auth.py: modified"` with `files_modified=True` | `manifest_present: True` |
| `test_manifest_absent_when_required` | `"I modified several files"` with `files_modified=True` | `manifest_present: False` |
| `test_manifest_not_required` | `"Research findings only"` with `files_modified=False` | `manifest_present: True` (default pass) |

#### Criterion 4: QA Scope Declaration (3 tests)

| Test | Input | Expected |
|------|-------|----------|
| `test_qa_scope_declared_exact` | `"QA verification has not been performed"` | `qa_scope_declared: True` |
| `test_qa_scope_declared_variant` | `"Tests were not verified independently"` | `qa_scope_declared: True` |
| `test_qa_scope_not_declared` | `"Implementation complete. All changes committed."` | `qa_scope_declared: False` |

#### Criterion 5: Peer Delegation (4 tests)

| Test | Input | Expected |
|------|-------|----------|
| `test_peer_delegation_ask` | `"We should ask Engineer to review this"` | `no_peer_delegation: False` |
| `test_peer_delegation_have_verify` | `"Have QA verify the deployment"` | `no_peer_delegation: False` |
| `test_peer_delegation_tell` | `"Tell Research to investigate further"` | `no_peer_delegation: False` |
| `test_no_peer_delegation` | `"I completed the investigation independently. Findings below."` | `no_peer_delegation: True` |

#### Edge Cases (3 tests)

| Test | Input | Expected |
|------|-------|----------|
| `test_empty_response` | `""` | All criteria should have defined behavior (no crash) |
| `test_compliant_response` | Full realistic compliant response with evidence, manifest, QA declaration | All 5 criteria pass |
| `test_non_compliant_response` | Full realistic non-compliant response with forbidden phrases, no evidence | Multiple criteria fail |

**Total: 22 tests**

### New Test: `tests/hooks/test_compliance_pipeline.py`

Fast, deterministic, in `make test`. Smoke-tests the end-to-end data flow.

| Test | What it validates |
|------|-----------------|
| `test_compliance_log_schema_matches_audit_loader` | Write a record via `_compliance_log()`, load it via `load_compliance_logs()`, verify all fields present |
| `test_injection_to_gate1_pipeline` | Write 30 injection records to tmp JSONL, run `evaluate_gate1()`, verify pass/fail matches expected |
| `test_scorer_output_compatible_with_gate1` | Score a response via `score_response()`, verify output dict keys match what Gate 1 evaluation expects |

**Total: 3 tests**

### Scenario Schema Validation Test

Add 1 test to `tests/hooks/test_audit_calculations.py`:

| Test | What it validates |
|------|-----------------|
| `test_scenario_yaml_schema` | Load `trivial.yaml`, verify each scenario has required keys: `id`, `stratum`, `prompt`, `expected_behavior`, `scoring_criteria` |

**Total: 1 test**

---

## Summary

| Category | Tests | File | In make test? |
|----------|:-----:|------|:---:|
| Compliance scorer | 22 | `tests/hooks/test_compliance_scorer.py` (NEW) | Yes |
| Pipeline smoke test | 3 | `tests/hooks/test_compliance_pipeline.py` (NEW) | Yes |
| Scenario schema | 1 | `tests/hooks/test_audit_calculations.py` (ADD) | Yes |
| **Total new** | **26** | | |

After implementation: **59 existing + 26 new = 85 total** Agent Teams fast tests.

---

## What This Does NOT Cover (Intentionally)

| Item | Why excluded | When addressed |
|------|-------------|----------------|
| Battery runner (`battery_runner.py`) | Requires LLM execution; manual-only | Before Gate 1 evaluation |
| Medium/complex/adversarial YAML scenarios | Design task, not code test | Before Gate 1 evaluation |
| Actual Gate 1/2/3 evaluation | Requires live Agent Teams runs | After Phase 1.5 code complete |
| Phase 2 worktree merge tests | Phase 2 scope | Phase 2 research (RQ1/RQ2) |

---

## Files Referenced

| File | Role in test coverage |
|------|----------------------|
| `tests/manual/agent_teams_battery/scoring/compliance_scorer.py` | Source under test — the 5-criteria scorer |
| `src/claude_mpm/hooks/claude_hooks/event_handlers.py` | Source — `_compliance_log()` function |
| `scripts/audit_agent_teams_compliance.py` | Source — `load_compliance_logs()`, `evaluate_gate1()`, `clopper_pearson_ci()` |
| `tests/manual/agent_teams_battery/scenarios/trivial.yaml` | Fixture — scenario schema validation |
| `tests/hooks/test_compliance_logging.py` | Existing — `_compliance_log()` tests (10) |
| `tests/hooks/test_audit_calculations.py` | Existing — audit math tests (16), extend with schema test |
