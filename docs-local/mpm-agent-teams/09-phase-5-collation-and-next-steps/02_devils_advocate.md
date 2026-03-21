# Devil's Advocate Review: Phase 2 Collation and Worktree Research

**Date:** 2026-03-21
**Reviewer:** Research Agent (Devil's Advocate)
**Documents Reviewed:**
- `00_collation.md` (Single source of truth)
- `01_worktree_research.md` (Worktree mechanics)
- `session1_analysis.md` (Session 1 raw evidence)
- `PM_INSTRUCTIONS.md` lines 1135-1276 (Current PM instructions)

**Additional Evidence Checked:**
- `git stash list` -- Stash still exists
- `~/.claude-mpm/compliance/` -- Compliance logs examined
- Git log vs. collation commit table -- Cross-referenced
- Claude Code binary v2.1.81 (193MB, arm64) -- String searches performed
- YAML scenario files -- Counted per-file
- Battery JSONL -- Pass rates independently verified
- Test collection -- Counts independently verified

---

## Part 1: Finding-by-Finding Analysis

### F1: The "Transient Worktree" Conclusion Is Not Proven -- MUST-FIX

**Claim from `01_worktree_research.md` Section 7 Summary Table:**
> "Worktrees are transient -- gone before PM can observe"

**The problem:** This conclusion conflates two very different scenarios:

**Scenario A -- Agents committed, worktrees cleaned up correctly:**
The binary cleanup function `Y_` (verified in v2.1.81) contains this logic:
```javascript
if (H_) {  // headCommit exists
    if (!await fdq(A_, H_))  // fdq = check if HEAD changed
        // HEAD unchanged: clean up worktree, return {}
        return await Tq_(A_, G_, l), /* clear metadata */, {};
}
// HEAD changed: keep worktree
return { worktreePath: A_, worktreeBranch: G_ };
```

The code also logs: `"Agent worktree has changes, keeping: ${A_}"` when changes are detected.

**If agents committed**, `fdq` would return `true` (HEAD changed), and the cleanup function would return `{ worktreePath, worktreeBranch }` -- meaning the worktree would PERSIST. The PM would then be able to see it.

**If agents did NOT commit** (only unstaged changes), HEAD is unchanged. The cleanup function calls `Tq_` (which removes the worktree) and returns `{}`. This means `git worktree remove` was called. Standard `git worktree remove` **discards all unstaged changes in the worktree**. It does NOT copy them to the parent.

**So how did 6 files with 220 insertions appear in the parent working tree?**

The worktree research document (Section 4.2) proposes three hypotheses but does not resolve them. The collation (Section 3) says the "most likely" explanation is #1 (process-level isolation only). But the binary evidence contradicts this -- the binary DOES call `gn_()` to create real worktrees, and the system prompt injection ("This is a git worktree") is confirmed in the binary strings.

**What we actually don't know:** There is a gap between "worktree was created" and "worktree was cleaned up" during which something transferred the unstaged changes to the parent. Either:

1. Claude Code's cleanup function has a copy-back mechanism not visible in the minified JS (the `Tq_` function may do more than simple `git worktree remove`)
2. The agents used `cwd` override or wrote to the parent path despite being in the worktree
3. The agents' file writes were somehow intercepted at a level below git

**Severity:** MUST-FIX. The entire revised PM instruction strategy depends on understanding this mechanism. If we get it wrong, we write instructions that will fail in future sessions.

**Recommended action:** Run a controlled experiment -- spawn a single agent with `isolation: worktree` and a simple task (create one file), then immediately check `git worktree list` and `git status` in both the parent and worktree directory. This is answerable in 15 minutes.

---

### F2: The Worktree Research Relies on Unreliable Binary Analysis -- SHOULD-FIX

**Claim from `01_worktree_research.md` Section 1.2:**
> "The Python Engineer agent extracted implementation details from the Claude Code binary (v2.1.81, 193MB Mach-O arm64)"

**Problems with this evidence:**

1. **The binary is minified JavaScript bundled into a native executable.** Variable names like `A_`, `G_`, `H_`, `gn_`, `fdq`, `Tq_` are obfuscated. The research document interprets these names by context, but context in minified code is notoriously misleading.

2. **I independently verified** that the binary does contain the strings:
   - `"This is a git worktree"` (confirmed)
   - `"isolated copy of the repository"` (confirmed)
   - `"Agent worktree has changes, keeping:"` (confirmed)
   - `"worktreePath"` and `"worktreeBranch"` (confirmed, 170 and 83 occurrences respectively)
   - `"worktree_resolved_to_main_repo"` (confirmed -- 3 occurrences, a telemetry event name)

3. **However,** the telemetry event `worktree_resolved_to_main_repo` is NOT mentioned in the worktree research document. This event name strongly suggests there IS a code path where worktrees "resolve" back to the main repo -- potentially the exact mechanism that explains Session 1. The research missed this.

4. **The binary version (2.1.81) may differ from the version running during Session 1.** Three binary versions exist in `~/.local/share/claude/versions/`: 2.1.79, 2.1.80, 2.1.81. The research does not confirm which version ran the session.

**Severity:** SHOULD-FIX. The binary analysis is directionally correct (worktrees ARE created) but incomplete. The `worktree_resolved_to_main_repo` event is a critical clue that was missed.

---

### F3: Scenario Counts in the Collation Are Inaccurate -- SHOULD-FIX

**Claim from `00_collation.md` Section 1, WP-D:**
> - `engineer.yaml` (30 scenarios)
> - `adversarial.yaml` (10 scenarios)
> - Total battery: 160 scenarios across 7 YAML files
> - 3 strata: Research 100, Engineer 30, QA 30

**Actual YAML file contents (independently verified):**

| File | Claimed | Actual |
|------|---------|--------|
| adversarial.yaml | 10 | **5** |
| engineer.yaml | 30 | **27** |
| trivial.yaml | 30 | 30 |
| medium.yaml | 30 | 30 |
| complex.yaml | 30 | 30 |
| qa.yaml | 20 | 20 |
| pipeline.yaml | 18 | 18 |
| **Total** | **168 (also claims 160)** | **160** |

The collation contains two inconsistencies: (a) adversarial is 5, not 10; (b) engineer is 27, not 30. The internal inconsistency between "168 total" and "160 across 7 YAML files" reflects sloppy bookkeeping.

**However,** the battery JSONL does contain exactly 160 scored records, and the stratum breakdown (research=100, engineer=30, qa=30) is correct in the JSONL. The difference is that the scoring infrastructure maps some pipeline/adversarial scenarios differently across strata -- for example, `research-then-eng` scenarios with fine_stratum count 5 research, and `eng-then-qa` scenarios count 5 engineer. So the YAML-level counts differ from the stratum-level counts.

**The collation conflates YAML file counts with stratum counts.** The per-file scenario table says "30 scenarios" for engineer.yaml, but the actual file has 27. The battery system augments this to 30 in the engineer stratum by pulling scenarios from pipeline.yaml.

**Severity:** SHOULD-FIX. The numbers are confusing but ultimately the battery is correct at the stratum level (100/30/30). The per-file claims need correction.

---

### F4: The Compliance Log Contains No Session 1 Data -- NOTE

**Finding:** The `~/.claude-mpm/compliance/` directory contains:
- `agent-teams-2026-03-20.jsonl` (2.7KB, test-session synthetic data only)
- `agent-teams-2026-03-21.jsonl` (12.7KB, 28 injection + 24 task_completed events, all synthetic)
- `agent-teams-battery-2026-03-21.jsonl` (95.5KB, 160 battery scored records)

None of these files contain Session 1 (`f2a8e7f9`) live telemetry. The compliance infrastructure logs test runs and battery results, but does NOT log live PM sessions. This means:

1. Gate B evidence comes entirely from manual JSONL analysis, not from the compliance pipeline
2. There is no automated mechanism to capture Gate B evidence
3. Future sessions will also require manual analysis

**Severity:** NOTE. The compliance infrastructure was designed for Gate A (battery), not Gate B (live observation). This is a known architectural gap, not a bug.

---

### F5: The Stash Still Exists and Is Recoverable -- NOTE

**Verified:**
```
stash@{0}: WIP on mpm-teams: cfe2d255 fix: text-only gate criteria...
6 files changed, 220 insertions(+), 11 deletions(-)
```

The stash is intact. The collation correctly reports this. The stash was created on `cfe2d255` which is still HEAD, so `git stash pop` should apply cleanly.

**Decision needed:** This stash contains engineer-generated code (structured logging + verbose flag). Is this code wanted? If yes, it should be popped and committed. If no, it should be dropped. Leaving it indefinitely creates confusion.

**Severity:** NOTE. Accurately reported, but a decision should be forced.

---

### F6: Commit Hashes in the Collation Are Accurate -- NOTE

**Verified:** All commit hashes in Section 6 of the collation match `git log --oneline mpm-teams --not main`. The Phase 2 core commits (`3d3bb251`, `9abd16d0`, `0fc7e23f`, `cfe2d255`) are correct and in the right order.

**Severity:** NOTE. Accurate.

---

### F7: Test Counts Are Slightly Misstated -- NOTE

**Collation Section 7 claims:**
> `test_battery.py`: 162 (160+2) tests

**Actual:** `pytest --collect-only` reports 163 tests (160 scenario tests + 2 gate evaluation tests + 1 live battery test, the live one being skipped).

The collation's "262 passed, 1 skipped in 0.68s" is correct as a test execution result. The collection count of 163 vs. stated 162 is a minor reporting error.

**Severity:** NOTE. Off by 1, does not affect conclusions.

---

### F8: Gate B Criteria B2 and B5 Are Logically Unfalsifiable Under Current Behavior -- RETHINK

**Current gate criteria:**
- B2: "PM delegates merge to Version Control / Local Ops agent"
- B5: "PM delegates worktree cleanup"

**The problem:** These criteria assume worktrees create persistent branches. If the infrastructure always resolves changes to the parent working tree (whether by design or by the agent-not-committing path), then:

- There are no branches to merge -> B2 can never be satisfied
- There are no worktrees to clean up -> B5 can never be satisfied

**These are not "NOT OBSERVED" -- they are "IMPOSSIBLE UNDER CURRENT INFRASTRUCTURE."**

The collation labels them "NOT OBSERVED" which is technically accurate but misleading. It implies they might be observed with a different session. They cannot be observed unless agents commit inside worktrees AND the cleanup function preserves those worktrees -- which requires the agents to know they should commit, which requires the TEAMMATE_PROTOCOL_ENGINEER to instruct them to commit, which it does:

> "Include git diff summary (files changed, insertions, deletions) in your completion report"

But a git diff summary does not require committing. The agents may have produced diffs from unstaged changes and never committed. The TEAMMATE_PROTOCOL_ENGINEER does NOT explicitly say "commit your changes in the worktree."

**This is the deeper problem:** The PM instructions (Merge Protocol) assume agents commit. The TEAMMATE_PROTOCOL does not instruct agents to commit. The cleanup function only preserves worktrees if agents commit. Therefore the Merge Protocol is dead code.

**Severity:** RETHINK. Either:
(a) Add an explicit "commit your changes" instruction to TEAMMATE_PROTOCOL_ENGINEER (which might make worktrees persist and the merge protocol work), OR
(b) Accept that worktrees resolve to parent, remove the merge protocol, and redefine B2/B5.

Option (a) should be tested experimentally before choosing.

---

### F9: PM Session 1 Final Message Contradicts Its Own Evidence -- SHOULD-FIX

**From `session1_analysis.md` Section 2.4, L154:**
> "2 engineers ran in parallel in isolated worktrees"

**From the same PM at L118:**
> "Both agents wrote to the working tree directly"

The PM claimed worktree isolation in its final report AFTER explicitly discovering and stating that agents wrote to the working tree directly. This is a hallucination/inconsistency in the PM's summarization. The PM correctly analyzed the situation but then reverted to the expected narrative in its summary.

**This matters because:** If a user reads the PM's final summary, they would incorrectly believe worktree isolation worked. The PM instructions should include guidance to report the ACTUAL mechanism used, not the expected mechanism.

**Severity:** SHOULD-FIX. Add a PM instruction: "Report the actual isolation mechanism observed, not the one specified in the Agent call."

---

### F10: The "3 Options" Analysis Is Incomplete -- RETHINK

**From `01_worktree_research.md` Section 5.2:**

**Option 1: Fix infrastructure to match documentation.**
- Requires changes to Claude Code binary -- NOT in our control
- Verdict: INFEASIBLE. We cannot change Claude Code's worktree lifecycle.

**Option 2: Fix documentation to match infrastructure.**
- Requires understanding the actual mechanism -- which we have NOT fully proven (see F1)
- Verdict: PREMATURE. We don't have enough evidence to write correct instructions.

**Option 3: Make PM instructions conditional (check, then adapt).**
- This is the safest option but introduces 4+ git commands as boilerplate in every team session
- Verdict: FEASIBLE but adds PM overhead and complexity

**Missing Option 4: Instruct agents to commit in worktree.**
If the cleanup function preserves worktrees when HEAD changes (i.e., when agents commit), then adding "Create a commit with your changes before completing" to TEAMMATE_PROTOCOL_ENGINEER might be sufficient to make the existing merge protocol work as designed.

This is the only option that fixes the root cause without changing either the binary or adding conditional logic. It should be tested.

**Severity:** RETHINK. Option 4 should be evaluated experimentally before committing to Option 3.

---

## Part 2: The Unanswered Question

**What happens to unstaged changes when `Tq_` removes a worktree?**

Standard `git worktree remove` discards uncommitted changes. But in Session 1, uncommitted changes from the worktree appeared in the parent working tree. Either:

1. `Tq_` does something beyond standard `git worktree remove` (copies changes to parent first)
2. Agents wrote to the parent path despite being told they were in a worktree
3. There is a mechanism (`worktree_resolved_to_main_repo` event?) that copies changes back before removal

This is the single most important question because:
- If (1): Worktrees work as designed, the "no commit" path is intentional, and we should write instructions for "verify working tree changes" not "merge branches"
- If (2): Worktree isolation is broken/incomplete, and `isolation: worktree` is not providing real isolation
- If (3): There is a deliberate resolve-to-parent mechanism, and we should document it

**Until this question is answered, any PM instruction changes are speculative.**

The `worktree_resolved_to_main_repo` telemetry event found in the binary is the strongest lead. Its name directly implies a "resolution" of worktree state back to the main repo. This was not investigated in the worktree research document.

---

## Part 3: Recommendation

### Should we merge Phase 2 as-is?

**NO.** Merging PM instructions that describe a merge protocol that cannot work (dead code) is worse than merging no PM instructions at all. The merge protocol (lines 1207-1258) will actively mislead the PM into searching for branches that don't exist, wasting 10+ git commands per session (as demonstrated in Session 1).

### Should we fix instructions first?

**YES, but only after a 15-minute experiment.** The recommended path:

1. **Experiment (15 min):** Spawn a single agent with `isolation: worktree`, have it create a file AND commit, wait for completion, then check `git worktree list`. This determines whether committed changes cause the worktree to persist.

2. **Based on result:**
   - **If worktree persists with committed changes:** Add "commit your changes" to TEAMMATE_PROTOCOL_ENGINEER. The existing merge protocol becomes correct. Fix the TEAMMATE_PROTOCOL, not the PM instructions.
   - **If worktree is still removed even with commits:** The `Tq_` function or background completion handler is overriding the cleanup logic. Replace the merge protocol with Option 3 (conditional check). Also investigate `worktree_resolved_to_main_repo`.
   - **If worktree persists but without the expected branch name:** Adjust the merge protocol to use the actual branch naming convention (`agent-XXXXXXXX`).

3. **After understanding the mechanism:** Revise PM_INSTRUCTIONS.md, revise gate criteria B2/B5, and then merge.

### What about Gate B remaining items (B4, B6)?

B4 (pipeline sequencing) and B6 (sub-threshold rejection) are independent of the worktree question. These CAN and SHOULD be tested in parallel with the worktree experiment.

### What about the code changes (WP-A, WP-C, WP-D, WP-E)?

These are solid. 262 tests passing, protocol routing correct, backward compatibility preserved, battery working. The implementation quality is not in question. Only the PM instructions (WP-B) need revision before merge.

---

## Part 4: Summary of Findings

| # | Finding | Severity | Action Required |
|---|---------|----------|----------------|
| F1 | "Transient worktree" not proven -- mechanism unknown | **MUST-FIX** | Run controlled experiment |
| F2 | Binary analysis unreliable; missed `worktree_resolved_to_main_repo` | **SHOULD-FIX** | Investigate telemetry event |
| F3 | Scenario counts inaccurate (adversarial: 5 not 10, engineer: 27 not 30) | **SHOULD-FIX** | Correct collation numbers |
| F4 | Compliance log has no Session 1 data | NOTE | Known architectural gap |
| F5 | Stash exists and is recoverable | NOTE | Force decision: pop or drop |
| F6 | Commit hashes accurate | NOTE | No action |
| F7 | Test count off by 1 (163 not 162) | NOTE | Minor correction |
| F8 | Gate B2/B5 logically unfalsifiable under current behavior | **RETHINK** | Redefine or enable via agent commit instruction |
| F9 | PM contradicts its own evidence in final summary | **SHOULD-FIX** | Add PM reporting instruction |
| F10 | "3 Options" analysis missing Option 4 (instruct agents to commit) | **RETHINK** | Test Option 4 experimentally |

**MUST-FIX: 1** | **SHOULD-FIX: 3** | **RETHINK: 2** | **NOTE: 4**

---

## Part 5: What Would Change My Mind

I would change my "do not merge as-is" recommendation if:

1. **Someone demonstrates that the merge protocol works.** If a PM session produces agent branches that persist and the merge protocol successfully merges them, the current instructions are correct and my concerns are moot.

2. **Anthropic documents the `isolation: worktree` lifecycle officially.** If there is official documentation saying "changes always resolve to parent working tree," then we know Option 3 is correct and can proceed immediately.

3. **The experiment shows agents are supposed to commit.** If adding "commit your changes" to TEAMMATE_PROTOCOL_ENGINEER makes worktrees persist and the merge protocol work, then the fix is a one-line protocol change, not a PM instruction rewrite.

Any of these would resolve the core uncertainty and allow a confident merge decision.
