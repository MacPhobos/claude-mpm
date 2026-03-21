# RQ3: Build Verification Across Parallel Changes

**Phase:** 2 Research
**Date:** 2026-03-20
**Branch:** mpm-teams
**Method:** Codebase analysis of PM_INSTRUCTIONS.md, agent metadata, Makefile, test infrastructure, and integration with RQ1+RQ2 merge findings
**Status:** Complete
**Dependencies:** RQ1+RQ2 (01_worktree_and_merge.md), RQ5 (05_pm_orchestration.md), RQ8 (08_rollback_recovery.md)

---

## Executive Summary

When Engineers A and B each produce working code in isolated worktrees, the merged result can still fail. Git merge success is a necessary but insufficient condition for correctness -- semantic conflicts (incompatible API changes across files, renamed functions, changed signatures) pass git merge cleanly but break at runtime or compile time. This document establishes the complete build verification workflow: who runs integration tests, when they run, how failures are diagnosed, and what happens when merged code breaks.

**Key findings:**

1. **PM should run integration tests directly** after merge, not delegate to a QA agent. This is the simplest, cheapest, and fastest approach for Phase 2.
2. **Incremental merge-then-test is not recommended.** Batch merge all branches first, then run tests once. The ~90-second test run does not justify N separate test runs.
3. **Semantic conflict detection requires blame attribution** -- the PM must correlate test failures with each Engineer's change scope to determine which branch to revert.
4. **The rollback default should be "revert last merged branch, re-test"** -- a binary search strategy for identifying the breaking change.
5. **A fix-up Engineer (not the original authors) is the best resolution strategy** for interaction faults, because the fixer needs context from both branches simultaneously.

---

## 1. Integration Test Workflow

### 1.1 Who Runs the Integration Test After Merge?

Three options were evaluated against the criteria of cost, isolation, failure attribution clarity, and PM context load.

#### Option A: PM Runs Tests Directly After Merging

```
PM merges all worktree branches (per RQ1+RQ2 protocol)
    |
    v
PM executes: make test  (or: uv run pytest tests/ -n auto)
    |
    v
PM reads test output, determines pass/fail
```

**Cost:** Zero delegation overhead. PM already has Bash access and PM_INSTRUCTIONS.md explicitly permits running "single documented test commands" as a cost-efficiency exception (line 49: "Run single documented test commands (pytest, npm test) and accept green output as evidence").

**Isolation:** Tests run against the merged code in the main working tree. This IS the integration environment -- exactly the code that would be committed.

**Failure attribution:** PM has full context of which branches were merged in which order. PM can correlate test failures with Engineer change scopes because PM received completion reports from all Engineers.

**Context cost:** Test output adds ~500-2000 tokens to PM context (pass: ~500 tokens of summary; fail: ~1000-2000 tokens of failure details).

**Verdict: RECOMMENDED for Phase 2.** Simplest approach with lowest overhead. The PM is the only entity that has the full picture (all Engineers' change scopes + merge order + test results).

#### Option B: PM Delegates to a QA Agent After Merge

```
PM merges all worktree branches
    |
    v
PM spawns QA agent with prompt: "Run make test, report results"
    |
    v
QA agent runs tests, reports back
    |
    v
PM receives QA results, determines next action
```

**Cost:** One additional agent spawn (~$0.10-0.30). QA agent context includes loading agent definition + test output.

**Isolation:** Same as Option A -- QA runs in the merged working tree.

**Failure attribution:** QA reports test results but does NOT know which Engineers changed which files. PM must still do the attribution. This means QA adds latency without adding analytical value for the integration test use case.

**Context cost:** Higher than Option A. PM receives QA's full response (~1000-3000 tokens) instead of raw test output (~500-2000 tokens), because the QA agent wraps results in its own analysis.

**Verdict: NOT RECOMMENDED for Phase 2 integration testing.** QA delegation is valuable for complex verification tasks (browser testing, API contract testing, manual test plan execution) but not for running `make test` and reading the output. The PM can do this directly per its documented cost-efficiency exception.

**When QA IS appropriate:** The Engineer-then-QA Pipeline (documented in 05_pm_orchestration.md Section 2.2) is appropriate when the user requests verification beyond test suite execution -- e.g., "verify the feature works in the browser" or "test the API endpoints manually." This is a separate concern from the integration test gate.

#### Option C: PM Delegates to an Engineer to Merge + Test in One Step

```
PM spawns Engineer agent with prompt: "Merge branches A and B, run tests, report"
    |
    v
Engineer does all merge + test work
    |
    v
PM receives results
```

**Cost:** One Engineer agent spawn (~$0.30-0.50). Higher than Option A or B.

**Isolation:** Engineer would need to operate in the main working tree (not a worktree) to perform the merge. This creates a risk: the merge Engineer shares the filesystem with the PM.

**Failure attribution:** The merge Engineer could perform attribution, but this overloads a single agent with merge mechanics, test execution, blame analysis, and rollback decisions. These are PM-level orchestration concerns.

**Verdict: NOT RECOMMENDED.** Merging is a PM orchestration responsibility per RQ1+RQ2 findings. The PM needs to maintain control of the merge pipeline to make rollback decisions.

### 1.2 Recommendation Summary

| Approach | Cost | Attribution Quality | PM Context Load | Recommended? |
|----------|:----:|:-------------------:|:---------------:|:------------:|
| PM runs tests directly | $0.00 | HIGH (PM has full picture) | 500-2000 tokens | YES (Phase 2) |
| Delegate to QA agent | $0.10-0.30 | LOW (QA lacks change context) | 1000-3000 tokens | NO (for integration gate) |
| Delegate to Engineer | $0.30-0.50 | MEDIUM (overloaded agent) | 1500-3000 tokens | NO |

---

## 2. Merge Ordering Strategy

### 2.1 The Two Approaches

**Approach 1: Incremental Merge-Test (merge one, test, merge next, test)**

```
Merge A (fast-forward) -> run tests -> pass?
    |                                    |
    yes                                  no -> revert A, report
    |
    v
Merge B (--no-commit) -> clean? -> commit -> run tests -> pass?
                          |                                |
                          no -> abort, report               no -> revert B, report
                          |
                          v
Merge C (--no-commit) -> clean? -> commit -> run tests -> pass?
                                                           |
                                                           no -> revert C, report
```

**Pros:**
- Immediate identification of which merge broke the build
- No blame attribution needed -- the failing merge is the one that just happened
- Clean rollback at any point

**Cons:**
- N test runs for N Engineers (N x ~90 seconds = ~180-270 seconds for 2-3 Engineers)
- Significant PM blocking time
- Unnecessary if all merges are clean (the common case)

**Approach 2: Batch Merge Then Test Once**

```
Merge A (fast-forward)
    |
    v
Merge B (--no-commit) -> clean? -> commit
    |                     |
    |                     no -> abort, report
    v
Merge C (--no-commit) -> clean? -> commit
    |                     |
    |                     no -> abort, report
    v
Run tests ONCE on fully merged code
    |
    +-- pass -> done
    +-- fail -> blame attribution needed (Section 3)
```

**Pros:**
- Single test run (~90 seconds regardless of N)
- Faster in the common case (all clean, all pass)
- Lower PM blocking time

**Cons:**
- On failure, PM must determine which merge caused the break (blame attribution)
- Blame attribution adds complexity (but only on the failure path)

### 2.2 Analysis: Which Approach is Better?

The key question is: **how often do merged branches cause test failures?**

If Engineers are working on independent subsystems (the expected case for well-decomposed parallel work), the probability of semantic conflict is LOW. The PM's pre-flight scope check (RQ5, Section 4: "estimate file overlap per subsystem pair") further reduces this probability.

**Expected frequency of semantic conflicts:** The common case for well-decomposed parallel tasks is that 0 out of N merges cause test failures. The incremental approach pays N x 90s for a scenario that occurs <10% of the time.

**Cost comparison for 3 Engineers:**

| Scenario | Incremental (3 test runs) | Batch (1 test run) |
|----------|:------------------------:|:-------------------:|
| All pass (common, ~90%) | 270 seconds | 90 seconds |
| One fails (uncommon, ~8%) | 90-180 seconds (fails early) | 90 seconds + attribution |
| Multiple fail (rare, ~2%) | 90 seconds (fails on first) | 90 seconds + complex attribution |

**Recommendation: Batch Merge Then Test Once.**

The 3x time savings in the common case outweigh the additional attribution complexity in the rare failure case. The PM saves ~180 seconds of blocking time per integration cycle, which directly translates to faster user-visible results.

### 2.3 Test Infrastructure Details

From the project's actual test infrastructure:

- **Test command:** `make test` (alias for `uv run pytest tests/ -n auto -v --tb=short --strict-markers`)
- **Test count:** 8,168 tests across 800 test files
- **Parallelization:** `-n auto` uses pytest-xdist across all CPU cores
- **Collection time:** ~36 seconds (test discovery only)
- **Estimated full run:** ~90-120 seconds with parallel execution
- **Bash tool timeout:** Default 120,000ms (2 minutes), max 600,000ms (10 minutes). A 90-second test run fits within the default timeout.

**Critical:** The PM should use `timeout: 300000` (5 minutes) on the Bash call for `make test` to provide headroom for slower machines or test suite growth. The default 2-minute timeout is tight for an 8,168-test suite.

```
PM executes via Bash tool:
  command: "cd /path/to/repo && make test"
  timeout: 300000  (5 minutes)
```

### 2.4 The 90-Second Blocking Question

Is 90 seconds acceptable as a blocking step for the PM?

**Yes, for Phase 2.** The PM's only task during this period is waiting for test results. The PM cannot make merge decisions without knowing if tests pass. This is an inherently sequential gate -- no useful work can be parallelized during the test run.

In Phase 3, if test suites grow significantly or multiple integration cycles occur per session, the PM could:
- Run tests with `run_in_background: true` and continue orchestrating other teams
- Delegate to a QA agent for complex test suites (>5 minutes)
- Use `make test-fast` (unit tests only) as a quick gate, with full suite delegated to QA

For Phase 2, the simple blocking approach is correct.

---

## 3. Semantic Conflict Detection and Resolution

### 3.1 What Is a Semantic Conflict?

A semantic conflict occurs when two changes each work correctly in isolation but produce broken code when combined. Git cannot detect these because they typically involve different files.

**Canonical example:**
- Engineer A adds a parameter to `calculate(a, b, precision=2)` in `math_utils.py`
- Engineer B calls `calculate(a, b)` (old signature) in `report_generator.py`
- Git merge succeeds (different files modified). Tests fail: `TypeError: calculate() missing 1 required positional argument: 'precision'`

**Other semantic conflict patterns:**
- Function/class renamed in one branch, called by old name in another
- Enum value added in one branch, switch/match statement in another missing the new case
- Import path changed in one branch, imported by old path in another
- Configuration key renamed in one branch, read by old key in another
- Shared state (global, singleton) modified incompatibly by both branches

### 3.2 Detection: Tests Are the Only Reliable Mechanism

Git cannot detect semantic conflicts. Static analysis could catch some cases (unused imports, undefined names) but is not available in Claude Code's standard tool set. **Integration tests are the only reliable detection mechanism for semantic conflicts.**

This is why the test gate is mandatory, even when all git merges succeed cleanly.

### 3.3 Blame Attribution Protocol

When tests fail after batch merge, the PM must determine which branch introduced the failure. The attribution protocol:

**Step 1: Examine test failures**
```
PM reads test output, identifies:
  - Which test files failed
  - Which source files the failing tests exercise
  - The error type (ImportError, TypeError, AttributeError, assertion failure, etc.)
```

**Step 2: Correlate with Engineer change scopes**
```
For each failing test file:
  - Which source files does it import/test?
  - Were those source files modified by Engineer A, B, or both?
  - Classification:
    - "A-only files"    -> Branch-A fault
    - "B-only files"    -> Branch-B fault
    - "A+B files"       -> Interaction fault
    - "Neither A nor B" -> Pre-existing failure
```

**Step 3: Verify classification with targeted revert**
```
If classified as Branch-B fault:
  git revert <B-merge-commit> --no-commit
  Run failing tests only (not full suite)
  If tests pass: classification confirmed
  If tests still fail: reclassify (may be interaction fault)
```

**Step 4: Error type heuristics**

| Error Type | Likely Cause | Attribution |
|------------|-------------|-------------|
| `ImportError` / `ModuleNotFoundError` | File renamed or moved by one branch, imported by another | Interaction fault |
| `TypeError` (wrong args) | Function signature changed in one branch, called with old signature in another | Interaction fault |
| `AttributeError` | Class/object interface changed in one branch, used by old interface in another | Interaction fault |
| `AssertionError` (test logic) | Code behavior changed in one branch, test expectations from another branch | Single-branch fault (the branch that changed behavior) |
| `SyntaxError` | Should not occur if each branch passes individually. If it does: merge produced invalid Python (extremely rare) | Merge artifact |

### 3.4 Cost of Attribution

Blame attribution requires the PM to:
1. Read test output (~1000-2000 tokens)
2. Run `git log --name-only <branch>` for each Engineer's branch to get their change scope (~200-500 tokens per branch)
3. Correlate failing files with change scopes (PM reasoning, ~100 tokens)
4. Optionally: targeted revert + re-run failing tests (~500-1000 tokens)

**Total attribution cost:** ~2000-4000 additional PM context tokens. This is acceptable given that it only occurs on the failure path (~10% of cases).

---

## 4. Resolution Strategies for Test Failures

### 4.1 Decision Tree

```
Tests fail after batch merge
    |
    v
PM examines test output
    |
    v
Are these pre-existing failures?
    |
    +-- YES -> Report: "These failures exist on the base branch.
    |          Not caused by team changes." Proceed.
    |
    +-- NO -> PM runs blame attribution (Section 3.3)
              |
              v
         Fault classification?
              |
              +-- Single-branch fault (Branch-X)
              |     |
              |     v
              |   Revert Branch-X merge: git revert <X-merge-commit>
              |   Re-run tests to confirm fix
              |   Report: "Branch-X changes cause test failure.
              |            Reverting. Remaining changes are clean."
              |   Option: Re-delegate X's scope to new Engineer
              |            with instructions to fix the issue
              |
              +-- Interaction fault (both branches)
              |     |
              |     v
              |   Spawn fix-up Engineer (Section 4.2)
              |
              +-- Total failure (cannot attribute)
                    |
                    v
                  Revert ALL merges: git reset --hard <pre-merge-commit>
                  Report: "Integration failed. Manual resolution needed."
                  Fall back to sequential execution
```

### 4.2 The Fix-Up Engineer Pattern

When the failure is an interaction fault (both branches contribute to the failure), neither original Engineer has the full picture. The correct resolution is:

**Spawn a single new Engineer with context from BOTH branches.**

```
PM spawns Engineer with prompt:
  "Two parallel changes were merged and the integration tests fail.

  Engineer A's changes: [summary from A's completion report]
  Files modified by A: [list from git log]

  Engineer B's changes: [summary from B's completion report]
  Files modified by B: [list from git log]

  Test failures: [relevant test output]

  Fix the integration issue so that both changes work together.
  Run make test to verify your fix."
```

**Why not the original Engineers?**
- Engineer A has context about A's changes but not B's
- Engineer B has context about B's changes but not A's
- The fix requires understanding the INTERACTION, which neither original Engineer has
- A fresh Engineer given both contexts is better positioned than either original

**Why not send the fix back to one of the originals?**
- The original Engineers completed in worktrees that may no longer reflect the merged state
- They would need the other Engineer's changes injected into their context
- This is effectively the same as spawning a new Engineer with both contexts

**Cost:** One additional Engineer agent spawn (~$0.30-0.50). This is the cost of parallel work -- interaction faults are the price paid for the time savings of parallelism.

### 4.3 When To Use Each Strategy

| Failure Type | Frequency | Strategy | Cost |
|-------------|:---------:|----------|:----:|
| Pre-existing | ~5% of runs | Ignore, report | $0 |
| Single-branch fault | ~5% of runs | Revert + re-delegate | $0.30-0.50 |
| Interaction fault | ~3% of runs | Fix-up Engineer | $0.30-0.50 |
| Total failure | <1% of runs | Revert all, sequential fallback | Variable |

---

## 5. Rollback Protocol for Integration Failures

### 5.1 Git Mechanics for Rollback

The PM uses standard git operations for rollback. All rollback operations are safe and reversible because git preserves full history.

**Revert a single branch merge:**
```bash
# Find the merge commit for Branch-B
git log --oneline --merges -5

# Revert it (creates a new commit undoing the merge)
git revert -m 1 <merge-commit-hash>
```

**Revert all merges (return to pre-merge state):**
```bash
# If merges have not been pushed (local only):
git reset --hard <pre-merge-commit-hash>

# If merges have been pushed (shared branch):
# Revert each merge in reverse order
git revert -m 1 <merge-C-hash>
git revert -m 1 <merge-B-hash>
git revert -m 1 <merge-A-hash>
```

**Important:** In the Phase 2 workflow, merges happen on a local integration branch before push. `git reset --hard` is safe because no other process or user is reading from this branch at merge time.

### 5.2 The Default Rollback Behavior

The PM's default behavior when tests fail should follow this priority:

**Priority 1: Identify and revert the offending branch (preserve good work)**

If blame attribution identifies a single branch as the cause, revert only that branch. The other Engineers' work remains in the merged codebase. This preserves maximum value.

**Priority 2: Spawn a fix-up Engineer (for interaction faults)**

If both branches are needed and the failure is an interaction issue, spawn a single Engineer to fix the interaction. Do not revert -- the fix-up Engineer works on the merged codebase.

**Priority 3: Revert all and fall back to sequential execution**

If the failure cannot be attributed, or if the fix-up Engineer also fails, revert all merges and re-execute the Engineers' tasks sequentially (one at a time, no parallelism). This eliminates the possibility of interaction faults at the cost of wall-clock time.

### 5.3 Rollback Decision Table

| PM Situation | Default Action | Escalation |
|-------------|---------------|-----------|
| Tests pass after batch merge | Proceed to report | N/A |
| Tests fail, single branch identified | Revert that branch, report remaining work as clean, offer to re-delegate reverted scope | User intervention if re-delegation also fails |
| Tests fail, interaction fault | Spawn fix-up Engineer with both contexts | If fix-up fails: revert all, sequential fallback |
| Tests fail, pre-existing failures | Report but proceed (failures are not caused by team) | N/A |
| Tests fail, cannot attribute | Revert all, sequential fallback | User intervention |
| Test run times out (>5 min) | Report timeout, suggest `make test-fast` as alternative | User intervention |
| Test run crashes (not failures) | Report crash, check if merge produced invalid code | Revert all, investigate |

### 5.4 Post-Rollback Cleanup

After any rollback, the PM must:

1. **Clean up merge state:** Ensure no uncommitted merge state remains (`git status` should be clean)
2. **Preserve worktree branches:** Do NOT delete worktree branches after rollback. They contain the original work and may be needed for re-merge after fixes.
3. **Report clearly to user:** Include which branches were merged, which were reverted, and why.
4. **Track attempt count:** Per RQ8, the abort threshold is 3 failures per team session. After 3 failed integration attempts, the PM should abort the team approach entirely and fall back to sequential execution.

---

## 6. Implications for PM_INSTRUCTIONS.md

### 6.1 New Section: Post-Merge Integration Test Gate

The following guidance should be added to PM_INSTRUCTIONS.md after the worktree merge protocol:

```
### Integration Test Gate (After Worktree Merge)

After merging all worktree branches:

1. Run the project's test suite directly:
   - Use the documented test command (make test, npm test, etc.)
   - Set Bash timeout to 5 minutes (timeout: 300000)
   - Read the FULL output before making pass/fail determination

2. If all tests pass:
   - Proceed to report results
   - Clean up worktrees and branches

3. If tests fail:
   - Check if failures are pre-existing (compare against base branch)
   - If new failures: identify which merged branch caused them
     by correlating failing tests with each Engineer's change scope
   - If single branch at fault: revert that branch's merge,
     report the issue, offer to re-delegate
   - If interaction fault: spawn a fix-up Engineer with both
     branches' context to resolve the integration issue
   - If unattributable: revert all merges, fall back to
     sequential execution

4. Do NOT delegate integration testing to a QA agent.
   The PM runs tests directly as a cost-efficiency measure.
   QA delegation is reserved for complex verification tasks
   (browser testing, API contract testing, etc.)
```

### 6.2 New Section: Semantic Conflict Handling

```
### Semantic Conflicts (Clean Merge, Broken Code)

A "semantic conflict" occurs when git merge succeeds but the
combined code is broken. This happens when two Engineers change
related but different files (e.g., one changes a function
signature, another calls the function with the old signature).

Detection: Only integration tests catch semantic conflicts.
Git cannot detect them. This is why the integration test gate
is MANDATORY, even when all git merges succeed cleanly.

Resolution:
1. Run blame attribution: which files do failing tests exercise?
   Cross-reference with each Engineer's change scope.
2. If one branch is clearly at fault: revert that branch.
3. If both branches contribute (interaction fault): spawn a
   single fix-up Engineer with context from BOTH branches.
4. If cannot determine: revert all, sequential fallback.
```

### 6.3 Modification to Existing Cost-Efficiency Exception

The existing PM_INSTRUCTIONS.md line 49 ("Run single documented test commands (pytest, npm test) and accept green output as evidence") already permits the PM to run tests directly. No modification needed -- the integration test gate is consistent with this existing permission.

However, the existing text says "accept green output as evidence." For the integration test gate, the PM must also read FAILURE output carefully (not just accept green). A clarification could be added:

```
3. Run single documented test commands (pytest, npm test).
   Accept green output as evidence of success.
   On failure: read output to identify failing tests and
   correlate with recent changes for attribution.
```

---

## 7. Complete Integration Test Workflow (Step-by-Step)

This is the definitive step-by-step workflow combining RQ1+RQ2 merge findings with RQ3 build verification.

```
=== PHASE: POST-COMPLETION MERGE AND VERIFICATION ===

Precondition: All Engineers have completed and PM has validated
their completion reports (per RQ5 validation gate).

--- Step 1: Pre-Merge Baseline ---
PM runs: make test (on base branch, before any merge)
  Purpose: Establish baseline. Any failures here are pre-existing.
  Store result: baseline_test_result = pass/fail
  If fail: Note pre-existing failures for later comparison.

--- Step 2: Sequential Branch Merge ---
PM runs: git merge <engineer-A-branch>
  (First merge is always fast-forward from shared base)

PM runs: git merge <engineer-B-branch> --no-commit
  If CONFLICT: git merge --abort -> report to user (per RQ2)
  If CLEAN: git commit -m "Merge engineer-B changes"

PM runs: git merge <engineer-C-branch> --no-commit
  (Repeat for each additional Engineer)
  If CONFLICT at any point: abort, report which branches conflict

--- Step 3: Integration Test ---
PM runs: make test
  timeout: 300000 (5 minutes)

--- Step 4: Evaluate Results ---
If all tests pass:
  -> PROCEED to report and cleanup

If tests fail AND same failures exist in baseline:
  -> PROCEED (pre-existing, not caused by team)

If tests fail with NEW failures:
  -> BLAME ATTRIBUTION:
     1. Read failure output
     2. git log --name-only <each-branch> to get change scopes
     3. Correlate failing test files with change scopes
     4. Classify: single-branch fault / interaction fault / unknown

--- Step 5: Resolution (failure path only) ---
Single-branch fault:
  git revert -m 1 <offending-merge-commit>
  Re-run make test to confirm remaining code is clean
  Report: "Engineer X's changes reverted due to test failure.
           Other changes remain merged and passing."
  Optionally: re-delegate X's scope with fix instructions

Interaction fault:
  Spawn fix-up Engineer with both contexts
  Fix-up Engineer works on merged codebase
  Re-run make test after fix
  If fix succeeds: proceed to report
  If fix fails: revert all, sequential fallback

Unknown/total failure:
  git reset --hard <pre-merge-commit>
  Report: "Integration failed. Falling back to sequential execution."
  Re-execute tasks one Engineer at a time

--- Step 6: Cleanup ---
For each successfully merged branch:
  git worktree remove .claude/worktrees/<agent-name>
  git branch -d <agent-branch-name>

For reverted/failed branches:
  Keep worktrees for debugging
  Inform user of worktree locations
```

---

## 8. Open Questions for Phase 3

### 8.1 Background Test Execution

For Phase 3, when team sizes grow or test suites become longer, the PM should be able to run tests in the background while continuing other orchestration. The pattern would be:

```
PM runs: make test  (with run_in_background: true)
PM continues spawning next team or processing other tasks
PM receives notification when tests complete
PM reads results and applies pass/fail logic
```

This requires the PM to maintain enough context to return to the merge workflow after receiving background test results. Phase 2 avoids this complexity by keeping tests synchronous.

### 8.2 Incremental Testing for Large Suites

If the test suite grows beyond 5 minutes, incremental testing becomes more attractive:
- Run only affected tests: `uv run pytest tests/ -n auto -k "test_file_that_changed"`
- Use test impact analysis to identify which tests exercise which source files
- Run the full suite as a background verification step

This is a Phase 3 optimization. Phase 2 runs the full suite every time.

### 8.3 Pre-Merge Individual Verification

Should each Engineer run `make test` in their worktree before declaring completion? This would catch bugs in individual branches BEFORE merge, reducing the probability of post-merge failures.

**Tradeoff:** Each Engineer running tests adds ~90 seconds to their task duration. For 3 Engineers in parallel, this adds 90 seconds wall-clock (parallel execution) but 270 seconds total compute.

**Recommendation for Phase 2:** Add to Engineer instructions: "Run `make test` before declaring your task complete. If tests fail, fix the issue before reporting completion." This shifts individual bugs left (earlier detection) and reduces the burden on the post-merge integration test.

### 8.4 Snapshot Testing and Merge Determinism

When test suites include snapshot tests (recorded outputs), parallel changes that both update snapshots will always conflict at the git level. This is a known issue with snapshot testing in parallel workflows. Phase 2 should document this as a known limitation and recommend that Engineers coordinate on snapshot updates (or avoid snapshot tests in parallel-modified areas).

---

## References

- **RQ1+RQ2 findings:** `01_worktree_and_merge.md` -- worktree isolation, merge mechanics, conflict detection
- **RQ5 PM orchestration:** `05_pm_orchestration.md` -- integration test gate design, context load analysis
- **RQ8 rollback/recovery:** `08_rollback_recovery.md` -- failure modes, cleanup protocols, abort thresholds
- **Devil's advocate line 418:** "Who runs the final integration test?" -- the question this document answers
- **PM_INSTRUCTIONS.md line 49:** Cost-efficiency exception allowing PM to run test commands directly
- **CLAUDE.md test commands:** `make test`, `uv run pytest tests/ -n auto`
- **Agent metadata:** QA_CONFIG performance target: `full_test_suite: 30m` (designed for complex verification, not simple integration gates)
