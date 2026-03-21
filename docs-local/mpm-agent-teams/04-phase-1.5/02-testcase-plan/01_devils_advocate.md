# Devil's Advocate: Phase 1.5 Test Coverage Plan

**Date:** 2026-03-20

---

## Concern 1: The Scorer Regex Patterns Are Fragile

The compliance scorer uses regex to detect evidence, forbidden phrases, file manifests, QA declarations, and peer delegation. Regex is inherently brittle against LLM output, which is:

- **Inconsistently formatted:** The same model may write "line 42" one time and "L42" or "(42)" another
- **Context-dependent:** "should work" in `"The pagination should work with offset parameters"` is a legitimate technical statement, not a forbidden phrase
- **Multiline:** Evidence may span multiple lines with interleaved markdown

**The test plan tests the PATTERNS, not the REAL-WORLD MATCH RATE.** Tests like `test_forbidden_should_work` with input `"The fix should work correctly"` will pass — but the real question is: what's the false positive/negative rate against actual Claude output?

**Risk:** The scorer passes all unit tests but produces garbage scores against real teammate responses, making Gate 1 results untrustworthy.

**Verdict: PARTIALLY HOLDS.** Unit tests catch regex syntax errors and basic matching, which is their job. The real-world match rate is an empirical question answerable only by running the battery against actual output. The test plan correctly scopes this as a battery concern, not a unit test concern. But the plan should include at least 2 tests with realistic multi-paragraph Claude-style responses (not single-sentence inputs).

**Amendment:** Add the `test_compliant_response` and `test_non_compliant_response` tests (already in the plan under "Edge Cases") with realistic multi-paragraph teammate output, not toy inputs. These are the closest a unit test can get to validating real-world behavior.

---

## Concern 2: The Pipeline Test Is Too Thin

3 pipeline tests are proposed. This is the bare minimum. The pipeline has 4 stages (injection -> logging -> loading -> evaluation), and 3 tests cover 3 specific paths. But:

- What about the scorer stage? The pipeline test `test_scorer_output_compatible_with_gate1` checks key compatibility but doesn't actually feed scorer output into Gate 1 evaluation.
- What about date filtering? The audit script filters by date — does a record written today get loaded when filtered by today's date?

**Verdict: LOW.** 3 pipeline tests are sufficient for a smoke test. The component-level tests (59 existing) cover the individual stages thoroughly. Adding more pipeline tests has diminishing returns. The plan is correctly minimal here.

---

## Concern 3: The Plan Ignores the n>=30 Statistical Problem

Engineer B discovered that Clopper-Pearson at n=10 with perfect compliance yields lower bound 0.6915 — BELOW the 0.70 Gate 1 threshold. The test plan doesn't address this implication:

- Gate 1 requires lower bound > 0.70 at ALL strata
- At n=10 per stratum, even 100% compliance fails
- At n=30 per stratum, you need ~27/30 (90%) to pass
- The plan proposes 10 trivial + 10 medium + 10 complex scenarios = 30 total, but only 10 per stratum

**This means the planned battery is statistically INSUFFICIENT for Gate 1 as originally defined.** Either:
a) Increase to 30 per stratum (90 total tasks — expensive, ~15-45 hours of LLM execution)
b) Lower the Gate 1 threshold from 0.70 to 0.60 (lower bound at n=10 k=10 is 0.6915)
c) Accept that Gate 1 is a directional signal, not a statistical proof, at n=10

**Verdict: HOLDS — but this is a Gate 1 design issue, not a test coverage issue.** The testcase plan correctly covers the code. The statistical feasibility of Gate 1 at n=10/stratum is a constraint inherited from the gate definition, not a gap in test implementation. The plan should note this constraint explicitly so whoever runs the battery understands the limitation.

**Amendment (to plan, not tests):** Add a note: "Gate 1 at n=10/stratum may not achieve statistical significance at the 0.70 threshold. Consider n=30/stratum for definitive results, or interpret n=10 results as directional rather than conclusive."

---

## Concern 4: Are 26 More Tests Actually Needed?

The plan adds 26 tests. The existing 59 tests already cover:
- Injection mechanics (24 tests)
- Event handler integration (9 tests)
- Compliance log format (10 tests)
- Audit math (16 tests)

The new 26 tests cover:
- Scorer regex patterns (22 tests)
- Pipeline smoke (3 tests)
- YAML schema (1 test)

**Is 22 tests for a single 80-line function excessive?** The scorer has 5 criteria with 3-5 tests each. That's methodical, not excessive. Each criterion has distinct regex logic that needs positive, negative, and edge case coverage.

**Verdict: DOES NOT HOLD.** 22 tests for the scorer is proportionate. It's the Gate 1 scoring function — it needs to be right. The pipeline and schema tests are minimal additions. The total (85 tests) is reasonable for a feature this critical.

---

## Concern 5: No Test Validates the PM Instructions Work

All 85 tests validate CODE (injector, logger, scorer, audit). Zero tests validate that the PM BEHAVIORAL INSTRUCTIONS actually produce the desired behavior:
- Does the PM actually decompose tasks into independent questions?
- Does the PM actually spawn teammates with scope boundaries?
- Does the PM actually fall back to run_in_background when Agent Teams is unavailable?

**These are behavioral tests requiring LLM execution.** They belong in the battery, not in `make test`.

**Verdict: DOES NOT HOLD for the test plan scope.** The plan explicitly scopes out LLM-required tests. The PM behavioral tests are Phase 1.5 battery concerns, not unit test concerns. The code can be validated without the PM. The PM behavior is validated by the battery.

---

## Summary

| # | Concern | Severity | Amendment needed? |
|---|---------|----------|:-:|
| 1 | Scorer regex fragility | MEDIUM | Add realistic multi-paragraph test cases (already in plan) |
| 2 | Pipeline test is thin | LOW | No — 3 smoke tests are sufficient |
| 3 | n>=30 statistical problem | MEDIUM | Note the limitation in the plan (not a code change) |
| 4 | 26 tests excessive? | NONE | No — proportionate to criticality |
| 5 | PM instructions untested | NONE | Out of scope (battery concern) |

**Amendments needed: None that change the test implementation plan.** The plan should add a note about the n=10/stratum statistical limitation (Concern 3), and the edge case tests should use realistic multi-paragraph responses (Concern 1) — both of which are already contemplated in the plan.

**The test plan is ready for implementation as-is.**
