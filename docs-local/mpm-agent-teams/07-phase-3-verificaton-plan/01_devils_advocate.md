# Devil's Advocate: Verification Plan

**Date:** 2026-03-21
**Subject:** Is the verification plan ready? Final review before execution.

---

## Findings Summary

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| 1 | Gate measures injection success, not response compliance | MUST-FIX | Gate may pass trivially (injection is deterministic code) |
| 2 | n>=10 criterion is self-contradictory (n=10 with 100% compliance gives CI=0.6915 < 0.70) | MUST-FIX | Any stratum with exactly n=10 cannot pass even with perfect compliance |
| 3 | Repeated runs of same scenario are not independent samples | MUST-FIX | Inflated n from duplicates makes CI meaningless |
| 4 | Original gate requires 3 strata (Research, Engineer, QA) with n>=30; plan proposes 9 strata with n>=10 | MUST-FIX | Silently redefines gate requirements |
| 5 | PM behavioral compliance (core Phase 2 deliverable) is outside the gate | RETHINK | Gate could pass without proving merge protocol, recovery, or composition selection works |
| 6 | Tier 2 tests Haiku instruction-following, not Phase 2 implementation | SHOULD-FIX | Proves "Haiku follows protocol text" not "Phase 2 system works" |
| 7 | Cost estimates internally inconsistent ($30-65 vs $8-45 vs $5-10) | SHOULD-FIX | Confusing; may discourage approval |
| 8 | Stratum grouping hides sub-stratum failures | SHOULD-FIX | Merge compliance could be 0% while engineer stratum passes |
| 9 | WP-V2 (live runner) timeline of 1-2 days unrealistic for full specification | SHOULD-FIX | Feature creep in a verification tool |
| 10 | Compliance scorer lacks Phase 2-specific criteria (git diff, scope declaration, test output) | SHOULD-FIX | Evaluates Phase 2 strata using Phase 1 scoring rules |
| 11 | 46 existing compliance records dismissed too quickly | NOTE | Prove logging pipeline works in production |
| 12 | Provisional gate pass creates permanent escape hatch | NOTE | Tier 3 may never happen once Tier 2 passes |
| 13 | Clopper-Pearson edge case at k=n handled correctly | NOTE | No issue |

---

## Critical Insight: What Exactly Is Being Verified?

Phase 2 has two distinct deliverables:

**A. Teammate Protocol Extensions (WP-A):** Role-specific protocol addenda injected into teammate prompts. This is verified by unit tests (41 tests, all pass) — injection routing is deterministic code.

**B. PM Behavioral Instructions (WP-B):** ~95 new lines telling the PM when to spawn teams, how to decompose, how to delegate merge, how to handle failures. This CANNOT be verified by injection testing or response scoring. It requires observing actual PM behavior.

The original plan's gate criterion (Clopper-Pearson CI on compliance data) only measures Deliverable A. Deliverable B requires qualitative evidence — structured observation of PM sessions.

**The verification plan tries to apply statistical methods to what is fundamentally a qualitative question.** The result is an overbuilt plan that produces high-confidence answers to the wrong question.

---

## Recommended Adjustments

### 1. Reconcile Gate Requirements

Use the original 3-stratum scheme (Research, Engineer, QA) with n >= 30 each, NOT the 9-stratum scheme. Pool all engineer strata into "Engineer", all QA strata into "QA", all pipeline strata into the stratum of their primary role. This matches the original implementation plan Section 8.

### 2. Fix Minimum n

Change formal threshold from n >= 10 to n >= 15 (practical minimum that allows 1 failure). Document: with n=15, k=15, CI lower = 0.7816 > 0.70. With n=15, k=14, CI lower = 0.6458 < 0.70 (fails). So n=15 requires zero failures, but n=20 tolerates 1 failure.

### 3. Write New Scenarios, Don't Run Duplicates

For strata with insufficient scenarios, write genuinely new scenario YAML entries. Budget 1-2 hours to add 10-15 new scenarios across under-populated strata. Each new scenario is an independent sample; each repeated run is not.

### 4. Score Responses, Not Injections

The gate MUST evaluate scored response data. The audit script needs to consume `response_scored` event records where compliance criteria are evaluated, not `injection` records that only prove the hook fired.

### 5. Separate Statistical and Qualitative Gates

| Gate | What It Measures | Method | Blocking? |
|------|-----------------|--------|-----------|
| **Gate A: Response Compliance** | Do teammate responses follow the protocol? | Clopper-Pearson CI on scored responses, n>=15 per stratum | YES |
| **Gate B: PM Behavioral** | Does the PM follow orchestration instructions? | Structured observation of 3-5 live sessions, narrative checklist | YES (qualitative) |

Both gates must pass. Gate A is statistical. Gate B is qualitative but required.

### 6. Simplify the Tooling

Build a 50-100 line script, not a feature-rich CLI. No resume, no cost tracking, no dry-run. Just a loop that calls Haiku and scores responses.

### 7. Add Phase 2 Scoring Criteria

Add to compliance_scorer.py:
- `git_diff_present` (engineer role): response contains "insertions", "deletions", or diff-like output
- `scope_declared` (engineer role): response declares intended file scope before implementation
- `test_output_present` (QA role): response includes full test command AND output

---

## Simplified 2-Day Path (Recommended)

The plan as written takes 3-5 days, costs $30-65, and builds infrastructure that may not be reused. The simplified path below achieves the same confidence level in 2 days at $5-15:

**Day 1 (4-6 hours):**
1. Update audit script to use 3 dynamic strata and evaluate `response_scored` events (2 hours)
2. Add Phase 2 scoring criteria to compliance_scorer.py (1 hour)
3. Write a minimal Python script (50-100 lines) that loads scenarios, calls Haiku, scores responses, writes JSONL (2 hours)
4. Write 10-15 new scenario YAML entries for under-populated strata (1 hour)
5. Run the script for all scenarios (~$1-2)

**Day 2 (4-6 hours):**
6. Run audit script `--gate` on collected data. Evaluate 3 strata with n >= 30 each.
7. Manually run 3-5 live Claude Code sessions with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`:
   - 1 engineer-parallel scenario (observe: team spawning, worktree isolation)
   - 1 engineer-merge scenario (observe: merge delegation, make test)
   - 1 full-pipeline scenario (observe: phase transitions, synthesis)
   - 1 recovery scenario (observe: failure handling)
8. Document PM behavioral evidence narratively (Gate B checklist)
9. Write gate results document

**Cost:** ~$5-15
**What it proves:** (a) Responses comply at >70% CI, (b) PM follows orchestration protocols (narrative)
**Tooling debt:** Near zero (minimal script is disposable)
