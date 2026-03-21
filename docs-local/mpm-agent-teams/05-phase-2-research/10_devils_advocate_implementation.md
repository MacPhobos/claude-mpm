# Devil's Advocate: Phase 2 Implementation Plan

**Date:** 2026-03-20
**Subject:** Is this plan ready for execution? What will go wrong?

---

## Concern 1: "Primarily an INSTRUCTION Problem" Understates the Testing Challenge

The plan says Phase 2 is ~70% instruction text, ~30% code. This makes it sound easy. But instruction changes are the HARDEST to validate because:

- **Code changes have unit tests.** If `inject_context()` routes the wrong addendum, a test catches it in 0.3 seconds.
- **Instruction changes have no automated validation.** If the PM_INSTRUCTIONS.md merge protocol says "merge A first, then B" but the PM merges in random order, no test catches it. The only validation is the live battery, which takes hours and produces probabilistic results.

The plan allocates 12 unit tests (WP-E) for the code changes but zero automated tests for the ~68 lines of new PM behavioral instructions. The instruction changes are the riskiest part of the plan, and they have the weakest testing.

**Verdict: PARTIALLY HOLDS.** The code testing is solid. The instruction testing gap is real but inherent to prompt-based systems. The battery scenarios (Day 3-4) are the mitigation, and the plan correctly schedules them. But the plan should explicitly note: "PM behavioral instructions cannot be unit-tested. Validation depends on the compliance battery and live observation."

---

## Concern 2: The 3-Teammate-Per-Phase Limit Contradicts Phase 1.5

Phase 1.5 explicitly REMOVED the teammate cap ("no ceiling — constrained by decomposition quality"). Now Phase 2 reintroduces a cap of 3 Engineers per parallel phase (RQ4 Anti-Pattern 4, RQ5 Section 3).

These are different contexts (Research is read-only, Engineering has merge conflicts), so the caps serve different purposes. But the PM will see contradictory guidance:
- Research: "Spawn one teammate per independent question. No ceiling."
- Engineering: "Never spawn > 3 Engineers in a single phase."

**The PM must reconcile these.** The plan doesn't explicitly address the inconsistency.

**Verdict: LOW.** The difference is justified (merge complexity is combinatorial, Research is conflict-free). But WP-B should make the distinction explicit in PM_INSTRUCTIONS.md: "Research teams have no size limit. Engineering teams are capped at 3 per phase due to merge complexity."

---

## Concern 3: The Merge Protocol Assumes PM Can Run Git Commands

The plan says the PM merges worktrees by running `git merge --no-commit branch-a`. But PM_INSTRUCTIONS.md Circuit Breaker #7 prohibits the PM from running "verification commands" and CB #1 limits the PM to "2-3 Bash commands for a task."

A merge sequence for 3 Engineers requires:
1. `git merge --no-commit branch-a` (test merge)
2. `git merge --abort` or `git commit` (accept/reject)
3. `git merge --no-commit branch-b` (test merge)
4. `git merge --abort` or `git commit`
5. `git merge --no-commit branch-c`
6. `git commit`
7. `make test` (integration test)
8. `git worktree remove` x3 (cleanup)

That's 8-11 commands — well beyond the "2-3 Bash commands" limit. The PM would need to delegate to a Version Control agent or Local Ops agent.

**Verdict: HOLDS.** Open Question #1 in the plan asks "PM merge directly or delegate?" but the circuit breaker analysis answers it: the PM MUST delegate. The merge sequence exceeds the bash command limit. The plan should resolve this in WP-B rather than leaving it as an open question. Recommendation: PM delegates the entire merge-test-cleanup sequence to a Version Control agent or Local Ops agent with specific instructions.

---

## Concern 4: RQ3 Is Still Pending

The synthesis notes "RQ3 (build verification protocol) -- not yet written; will be folded in as addendum." But RQ3 HAS been written — `03_build_verification.md` exists (662 lines). The synthesis agent apparently didn't see it because it was written in parallel.

This means the implementation plan is missing RQ3's key findings:
- PM runs `make test` directly (not QA delegation) for All-Engineer teams
- Batch merge all branches, test once
- Fix-up Engineer pattern for semantic conflicts
- Bash timeout must be 300,000ms (5 minutes)

**Verdict: HOLDS — but easily fixed.** The plan needs to incorporate RQ3 findings. The most impactful are: batch merge strategy (contradicts the plan's sequential merge assumption in WP-C) and the 300,000ms timeout requirement.

---

## Concern 5: Token Budget Is Tight for Future Growth

RQ6 shows Engineer addendum at 442/500 tokens (58 margin) and QA at 438/500 (62 margin). The plan notes this is within budget. But consider:

- Phase 3 may add peer coordination rules (relaxing Rule 5 for specific scenarios)
- Future roles (Ops, Security) would need addenda
- Protocol refinements from compliance feedback will add words, not remove them

With 58-token margin, adding ONE sentence to the Engineer addendum ("Before modifying files, declare your intended scope") could push it over budget.

**Verdict: LOW.** The budget constraint is documented (Section 10, Risk 9). The mitigation ("drop Rule 2 for Research") is viable. And the 500-token budget is a design choice, not a hard platform limit — if needed, it can be increased with measured overhead analysis.

---

## Concern 6: The Plan Is Missing a "Simplest Possible Phase 2"

The plan defines 6 work packages across 5 days. But the RQ1+RQ2 finding was: "Phase 2 is primarily an INSTRUCTION problem." If that's true, couldn't Phase 2 be just:

1. WP-A: Role-specific protocol addenda (~0.5 days)
2. WP-B: Add "for parallel Engineering, use `isolation: 'worktree'` and merge branches after" to PM_INSTRUCTIONS.md (~5 lines)
3. Done.

The PM already knows how to spawn parallel agents with worktree isolation. The PM already knows how to delegate merge operations. The PM already follows the TEAMMATE_PROTOCOL. Adding role-specific addenda plus a few lines of Engineering guidance might be sufficient.

The 5-day, 6-WP plan adds comprehensive merge protocols, recovery procedures, cleanup obligations, and orchestration flows. These are GOOD documentation, but are they NECESSARY for the feature to work? Or is Phase 2 overdesigned because the research was thorough?

**Verdict: PARTIALLY HOLDS.** The MVP Phase 2 is probably WP-A + a minimal WP-B (~2 days). The merge protocol, recovery, and cleanup are valuable safeguards but not blocking requirements. Consider phasing: ship the MVP (role addenda + basic Engineering guidance), observe PM behavior in real use, then add merge/recovery protocols based on what actually fails.

---

## Summary

| # | Concern | Severity | Amendment Needed? |
|---|---------|----------|:-:|
| 1 | Instruction changes not unit-testable | MEDIUM | Note the limitation explicitly |
| 2 | 3-Engineer cap contradicts Phase 1.5 cap removal | LOW | Make distinction explicit in WP-B |
| 3 | Merge sequence exceeds PM bash command limit | HIGH | Resolve in WP-B: PM delegates merge to agent |
| 4 | RQ3 findings not incorporated | MEDIUM | Fold `03_build_verification.md` findings into plan |
| 5 | Token budget tight for future growth | LOW | Already mitigated in plan |
| 6 | Plan may be overdesigned vs. MVP | MEDIUM | Consider 2-day MVP + incremental hardening |

### Must-Fix Before Execution

- **Concern 3:** The PM cannot run 8-11 git commands. The merge protocol MUST be delegation-based, not PM-direct. This changes WP-B and WP-C significantly.
- **Concern 4:** Incorporate RQ3 findings (batch merge, fix-up Engineer, timeout). These affect the merge protocol design.

### Should-Consider

- **Concern 6:** A 2-day MVP (WP-A + minimal WP-B) ships the core capability. Merge protocol hardening can follow based on observed behavior.
