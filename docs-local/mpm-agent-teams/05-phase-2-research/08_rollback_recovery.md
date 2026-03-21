# RQ8: Rollback and Recovery

**Phase:** 2 Research
**Date:** 2026-03-20
**Status:** Complete
**Dependencies:** Informed by RQ1 (worktree mechanics), Phase 1 fallback protocol (02_parallel_research_design.md Section 5)

---

## 1. Failure Mode Catalog

### 1.1 Failure Modes by Role

| Failure Mode | Research Impact | Engineer Impact | QA Impact |
|---|---|---|---|
| **Teammate timeout mid-task** | Partial results returned; read-only, no cleanup needed | Partial code in worktree; uncommitted changes may exist; worktree persists on disk | Incomplete test results; no state to clean up (tests are read-only or write to temp) |
| **Teammate crashes (process dies)** | No results; clean state (read-only) | Worktree may have uncommitted edits, partially written files, broken syntax; worktree persists on disk | No results; test artifacts may remain in worktree if QA ran in Engineer's worktree |
| **Teammate produces wrong output** | PM detects via validation (missing evidence, vague claims); send-back once per Phase 1 protocol | Broken code committed to worktree branch; may compile but produce wrong behavior; PM detects via post-merge test failure | False pass (tests pass but wrong assertions) or false fail (tests fail due to test bug, not code bug); PM cannot easily distinguish |
| **Teammate violates protocol** | PM sends back once with specific ask; if second response still non-compliant, PM accepts what is available and notes gap | PM sends back once; if Engineer ignores protocol on retry, PM accepts partial work and flags for manual review | PM sends back once; same pattern |
| **Worktree merge conflict** | N/A (Research is read-only; no worktrees) | Merge fails with git conflict markers; requires resolution before integration test can run; blocks the merge pipeline | N/A (QA reads from merged code, does not produce merge-eligible branches) |
| **Build fails after merge** | N/A | Integration failure: individual worktrees passed their own tests, but merged result does not compile or pass tests | Tests reveal the failure; QA provides the evidence that the merge is broken; QA is not the cause |

### 1.2 Failure Mode Severity Matrix

| Failure Mode | Frequency (est.) | Severity | Detectability | Overall Risk |
|---|:-:|:-:|:-:|:-:|
| Teammate timeout | Low | Medium | HIGH (Claude Code reports timeout) | LOW |
| Teammate crash | Very Low | High | HIGH (process exit detected) | LOW |
| Wrong output | Medium | Medium | MEDIUM (requires PM validation) | MEDIUM |
| Protocol violation | Medium | Low | HIGH (evidence check catches it) | LOW |
| Merge conflict | Medium-High | High | HIGH (git reports conflicts) | HIGH |
| Build fails after merge | Medium | High | HIGH (test suite catches it) | HIGH |

The two highest-risk failure modes are **merge conflict** and **build failure after merge**. Both are unique to Phase 2 parallel Engineering — Phase 1 Research had neither.

---

## 2. Recovery Protocol per Failure Mode

### 2.1 Teammate Timeout Mid-Task

**State left behind:**
- Research: Nothing. Read-only agent leaves no artifacts.
- Engineer: Worktree directory exists on disk at the path where Claude Code created it. May contain uncommitted changes (modified files, new files not yet staged). The worktree's branch exists in git's branch list. No commits from the incomplete work (unless the Engineer committed partway through).
- QA: If QA was running in its own worktree, same as Engineer. If QA was running against merged code in the main worktree, no persistent state.

**Who cleans up:** PM is responsible. PM detects the timeout via Claude Code's task notification (the TaskCompleted event fires with a timeout/failed status, or the teammate simply never responds within the session timeout).

**Can the task be retried?**
- Research: Yes. Spawn a new Research teammate with the same prompt. No state conflict.
- Engineer: Conditionally. The stale worktree must be assessed first:
  - If the worktree has no useful commits: remove the worktree (`git worktree remove <path>`), delete the branch (`git branch -D <branch>`), spawn a new Engineer with a fresh worktree.
  - If the worktree has partial useful commits: PM or user decides whether to build on the partial work (new Engineer starts from that branch) or discard and restart.
- QA: Yes. Spawn a new QA teammate. No state conflict.

**Fallback:** If retry also times out, PM reports the gap to the user. PM synthesizes results from teammates that did complete and notes: "Engineering work on [scope] was not completed due to teammate timeout."

### 2.2 Teammate Crashes (Process Dies)

**State left behind:** Identical to timeout, except:
- The Claude Code process that created the worktree has exited.
- Git worktrees are **not cleaned up automatically when the creating process exits.** A worktree is a directory on disk plus metadata in `.git/worktrees/`. The directory persists until explicitly removed via `git worktree remove` or `git worktree prune` (for directories that have been manually deleted from the filesystem).
- Any in-memory state the teammate had is lost. The hook handler (`hook_handler.py` lines 794-862) shows that each hook invocation is a fresh Python process with singleton-scoped state. There is no cross-process state recovery.

**Who cleans up:** PM must clean up. PM should:
1. Run `git worktree list` to identify worktrees associated with the crashed teammate.
2. Assess the worktree's branch for useful commits (`git log <branch>` to check if anything was committed).
3. If nothing useful: `git worktree remove <path>` followed by `git branch -D <branch>`.
4. If useful commits exist: preserve the branch, remove only the worktree directory.

**Can the task be retried?** Same as timeout — assess the stale worktree, then decide.

**Fallback:** Same as timeout — proceed without, report gap to user.

### 2.3 Teammate Produces Wrong Output

**State left behind:**
- Research: Incorrect findings in the PM's context. No persistent artifacts. PM discards and re-delegates.
- Engineer: Committed code on a worktree branch that is incorrect. The code exists in git history. If already merged, the incorrect code is now in the main branch.
- QA: Incorrect test results in the PM's context. If QA wrote test files, incorrect tests may exist in a worktree.

**Who cleans up:**
- Research: PM discards the finding. No cleanup needed.
- Engineer (pre-merge): PM does not merge the worktree branch. The branch can be discarded (`git branch -D`) or reassigned to a new Engineer.
- Engineer (post-merge): This is the worst case. PM must:
  1. Revert the merge commit: `git revert <merge-commit-hash>` (creates a new commit undoing the merge).
  2. Or, if the merge was not yet pushed: `git reset --hard HEAD~1` to discard the merge commit entirely.
  3. Reassign the task to a new Engineer.
- QA: PM discards the QA result and spawns a new QA teammate. If QA wrote test files, those are in a worktree and can be discarded with the worktree.

**Can the task be retried?** Yes, always. Wrong output does not corrupt irrecoverable state — git provides full history.

**Fallback:** If retry also produces wrong output, PM escalates to user with both attempts' evidence.

### 2.4 Teammate Violates Protocol

**State left behind:** The teammate's response is in the PM's context but lacks required evidence (per CB#3) or file manifest (per CB#4). No unique persistent state beyond what the teammate actually did in the worktree.

**Who cleans up:** PM handles via the existing send-back protocol (Phase 1, Section 4 of parallel_research_design.md):
1. PM sends the teammate back once with a specific ask for the missing element.
2. If the second response is still non-compliant, PM accepts what is available and notes the gap.
3. PM does NOT retry more than once per teammate (existing 1-send-back limit).

**Can the task be retried?** The send-back IS the retry. No second retry. PM proceeds with partial information.

**Fallback:** PM synthesizes available evidence, notes compliance gaps, and reports to user with the caveat that verification is incomplete.

### 2.5 Worktree Merge Conflict

**State left behind:** Two or more worktree branches that cannot be auto-merged by git. The conflict is in git's merge state — conflict markers in the affected files, an incomplete merge in progress.

**Who cleans up:** PM must resolve or delegate resolution:

**Option A: PM resolves (simple conflicts)**
1. PM runs `git merge --no-commit <branch-B>` from the main branch (where branch-A was already merged).
2. Git reports conflict files.
3. If conflicts are in non-overlapping sections of the same file, PM can resolve manually (choose one side, or merge sections).
4. PM commits the resolved merge.
5. PM runs integration tests.

**Option B: PM delegates to a Merge Engineer (complex conflicts)**
1. PM spawns a dedicated Engineer teammate with the merge conflict context.
2. Prompt includes: the two branches, the conflict files, and the intended behavior of both changes.
3. Merge Engineer resolves conflicts, commits, and reports.
4. PM validates the resolution via integration tests.

**Option C: PM aborts one branch (irreconcilable conflicts)**
1. PM determines that one Engineer's work is more complete/correct.
2. PM discards the other branch: `git merge --abort`, then proceed with only the accepted branch.
3. PM re-delegates the discarded work scope as a new task that builds on top of the accepted merge.

**Can the task be retried?** The merge itself can be retried after resolution. The underlying branches are not lost — they remain in git. `git merge --abort` cleanly returns to pre-merge state.

**Fallback:** If merge conflict cannot be resolved programmatically, PM reports to user with both branches' descriptions and asks for guidance on which to prioritize.

### 2.6 Build Fails After Merge

**State left behind:** A merged codebase that compiles/runs but fails tests (semantic conflict), or that does not compile at all. The merge commit exists in git history.

**Who cleans up:** PM orchestrates a diagnostic sequence:

1. **Identify the failure source:**
   - PM runs tests with verbose output.
   - PM examines which tests fail and which files they test.
   - PM correlates failed tests with the two Engineers' change scopes.

2. **Assign blame (which branch caused the failure):**
   - If failures are in files only Branch-A touched: Branch-A introduced the bug.
   - If failures are in files only Branch-B touched: Branch-B introduced the bug.
   - If failures are in the intersection of both branches' changes: interaction bug — neither branch is solely at fault.

3. **Resolution paths:**
   - **Single-branch fault:** Revert that branch's merge, fix the bug (new Engineer task), re-merge.
   - **Interaction fault:** Spawn a new Engineer with context from both branches to fix the integration issue.
   - **Total failure:** Revert both merges, fall back to sequential execution.

**Can the task be retried?** Yes. Git revert preserves history. The original branches still exist. Re-merge after fix is straightforward.

**Fallback:** Revert all merges, fall back to sequential execution (one Engineer at a time, no parallelism). This is the nuclear option but always safe.

---

## 3. Worktree Cleanup Investigation

### 3.1 What Happens When the Creating Process Exits?

**Finding: Worktrees persist on disk indefinitely after the creating process exits.**

Git worktrees are filesystem-level constructs, not process-level. When Claude Code creates a worktree via `git worktree add`, the following happens:

1. A new directory is created at the specified path containing the checked-out branch.
2. Metadata is stored in `.git/worktrees/<name>/` within the main repository.
3. The `.git` file in the worktree directory is a text file pointing back to the main repo's `.git/worktrees/<name>/` directory.

When the Claude Code process (or the teammate process running within it) exits — whether normally or via crash — none of these artifacts are removed. The worktree directory, its contents, and the `.git/worktrees/` metadata all remain.

### 3.2 Automatic Cleanup Behavior

Git provides two cleanup mechanisms:

1. **`git worktree prune`**: Removes metadata for worktrees whose directories have been manually deleted from the filesystem (e.g., `rm -rf <worktree-path>`). This cleans up `.git/worktrees/` entries that point to nonexistent directories. It does NOT delete worktree directories.

2. **`gc.worktreePruneExpire`**: A git config option (default: 3 months per `git-config` documentation) that controls when `git gc` automatically prunes stale worktree metadata. This only prunes metadata for directories that no longer exist — it does not delete active worktree directories.

**Neither mechanism automatically deletes worktree directories.** If a teammate crashes and leaves a worktree behind, that worktree will remain on disk until explicitly removed via `git worktree remove <path>` or manual `rm -rf` followed by `git worktree prune`.

### 3.3 Stale Worktree Accumulation

**Current state of this repository:** Running `git worktree list` shows only the main worktree:

```
/Users/mac/workspace/claude-mpm-fork 58639d51 [mpm-teams]
```

No stale worktrees from previous sessions exist. This is expected because Agent Teams has not been used in this repository yet. However, once Phase 2 begins spawning Engineer teammates with `isolation: "worktree"`, stale worktrees will accumulate unless the PM actively cleans them up.

**Accumulation scenario:**
- PM spawns 3 Engineer teammates, each with a worktree.
- Engineer 1 completes, Engineer 2 completes, Engineer 3 times out.
- Claude Code may clean up worktrees for completed teammates (platform behavior — needs experimental verification in RQ1).
- Engineer 3's worktree persists because the timeout does not trigger cleanup.
- Over multiple team sessions, stale worktrees accumulate: `.worktrees/engineer-auth-1`, `.worktrees/engineer-db-2`, `.worktrees/engineer-api-3-STALE`, etc.

### 3.4 Worktree Cleanup Commands

| Command | Effect | When to Use |
|---|---|---|
| `git worktree list` | Lists all worktrees (active and stale) | PM runs after every team session to audit |
| `git worktree remove <path>` | Deletes the worktree directory and removes metadata. Fails if worktree has uncommitted changes (use `--force` to override). | PM runs for completed/discarded teammate worktrees |
| `git worktree remove --force <path>` | Force-removes worktree even with uncommitted changes. Discards all uncommitted work. | PM runs for crashed/timed-out teammates whose partial work is deemed worthless |
| `git worktree prune` | Removes metadata for worktrees whose directories were manually deleted | Cleanup after `rm -rf` of stale worktree directories |
| `git branch -D <branch>` | Deletes the branch associated with a removed worktree | PM runs after worktree removal to clean up the branch namespace |

### 3.5 Implications for PM Protocol

The PM must include worktree cleanup as a mandatory post-team step. Proposed addition to PM_INSTRUCTIONS.md:

```
After every Agent Teams session involving Engineer teammates with worktree isolation:

1. Run `git worktree list` to enumerate all worktrees.
2. For each worktree NOT associated with the main branch:
   a. If the worktree's branch was successfully merged: `git worktree remove <path>` + `git branch -d <branch>`.
   b. If the worktree's branch was discarded (crash/timeout/wrong output): `git worktree remove --force <path>` + `git branch -D <branch>`.
   c. If the worktree's branch contains useful partial work: report to user for decision.
3. Verify cleanup: `git worktree list` should show only the main worktree.
```

---

## 4. Recovery Protocol Design

### 4.1 PM Failure Detection

The PM detects teammate failure through three channels:

1. **TaskCompleted event with failed status:** The `handle_task_completed_fast` handler in `event_handlers.py` fires when a task completes. The `completion_status` field indicates success or failure. PM receives this as a SendMessage from the teammate or a platform notification.

2. **Timeout (no response within session limit):** Claude Code has session-level timeouts. If a teammate does not respond, the PM eventually receives a timeout notification. The PM's orchestration flow (parallel_research_design.md Section 2, Step 3) already accounts for this: "PM does NOT poll or check on teammates — it waits for messages."

3. **Incomplete/invalid response:** PM receives a response that fails the QA gate (Section 4 of parallel_research_design.md) — missing evidence, missing file manifest, forbidden phrases. This is not a crash but is a quality failure.

### 4.2 PM Evaluation: Is Partial Work Useful?

When PM detects a failure, the evaluation protocol is:

```
Teammate failed/timed out
    |
    v
Was the teammate an Engineer with a worktree?
    |
    +-- NO (Research/QA) --> Discard result, note gap, proceed
    |
    +-- YES --> Check worktree state:
                |
                v
            Does the branch have any commits?
                |
                +-- NO --> Worktree has only uncommitted changes
                |          |
                |          v
                |      Are the uncommitted changes substantial?
                |          |
                |          +-- NO (< 10 lines changed) --> Discard: git worktree remove --force
                |          +-- YES --> Report to user: "Engineer [name] timed out with
                |                      uncommitted work in [path]. Review and decide."
                |
                +-- YES --> Branch has commits
                           |
                           v
                       Do committed changes pass syntax/lint check?
                           |
                           +-- NO --> Discard: git worktree remove --force + git branch -D
                           +-- YES --> Preserve branch for possible reuse
                                       Report to user: "Engineer [name] partially completed
                                       [scope]. [N] commits on branch [name]. Merge or discard?"
```

### 4.3 PM Decision: Retry, Proceed, or Abort

After evaluating partial work:

| Situation | Decision | Action |
|---|---|---|
| 1 of N Engineers failed, others succeeded | **Proceed without** | Merge successful worktrees. Note gap. User can request the failed scope as a follow-up. |
| 1 of N Engineers failed, failure scope blocks merge | **Retry** | Spawn a new Engineer for the failed scope. New worktree, fresh start. Include context from successful Engineers' merged work. |
| Multiple Engineers failed (>= 50% of team) | **Abort team** | Fall back to sequential execution. Do not retry as a team. See Section 5 (abort threshold). |
| Engineer failed but left useful partial commits | **Retry from partial** | Spawn a new Engineer on the same branch (new worktree pointing to existing branch). Engineer continues from partial state. |
| QA failed | **Retry QA** | Spawn a new QA teammate. QA is stateless — no worktree cleanup needed. |
| Research failed | **Proceed without** | Synthesize from available research. Note gap. (This is the Phase 1 protocol, unchanged.) |

### 4.4 PM Cleanup Sequence

After the decision is executed, PM performs cleanup:

```
1. For each discarded worktree:
   git worktree remove --force <path>
   git branch -D <branch>

2. For each successfully merged worktree:
   git worktree remove <path>
   git branch -d <branch>      # Safe delete (merged branches only)

3. For each preserved worktree (user decision pending):
   # Do NOT remove. Report path and branch to user.

4. Verify: git worktree list
   # Should show only main worktree + any preserved worktrees.

5. Verify: git branch
   # Should not contain dangling branches from deleted worktrees.
```

---

## 5. Abort Threshold

### 5.1 When Should PM Abort the Entire Team?

The PM should abort the team and fall back to sequential execution when the team is no longer likely to produce a correct, merged result faster than sequential execution would.

### 5.2 Abort Criteria

| Criterion | Threshold | Rationale |
|---|---|---|
| **Total teammate failures** | >= 3 failures across all teammates in the session | Aligned with existing CB#10 (Delegation Failure Limit): "After 3 failures to the same agent, PM stops and requests user guidance." Extended to team-wide failures. |
| **Same-scope retry failures** | >= 2 failures on the same task scope | If the task scope itself is problematic (e.g., ambiguous instructions, impossible constraint), retrying will not help. Escalate to user. |
| **Merge conflict unresolvable** | PM or Merge Engineer cannot resolve after 1 attempt | If the merge is too complex for automated resolution, the parallel approach has failed for this task. Fall back to sequential. |
| **Integration test failure after 2 fix attempts** | Build fails after merge, fix attempted, build fails again | Interaction bugs between parallel branches are inherently hard to fix without seeing the full picture. Sequential execution avoids the interaction. |
| **Team-wide timeout** | > 50% of teammates time out | Platform instability or task overload. Do not retry as a team. |

### 5.3 Abort Decision Flow

```
Failure detected
    |
    v
Increment session failure counter
    |
    v
Check: failure_count >= 3?
    |
    +-- YES --> ABORT TEAM
    |           |
    |           v
    |       1. Clean up all stale worktrees
    |       2. Preserve any successfully merged work
    |       3. Report to user: "Team execution aborted after [N] failures.
    |          [Summary of what succeeded and what failed.]
    |          Falling back to sequential execution."
    |       4. Re-delegate remaining work as standard sequential Agent calls
    |          (no team_name, no Agent Teams)
    |
    +-- NO --> Check: same_scope_failures >= 2?
               |
               +-- YES --> Escalate this specific scope to user
               |           Continue team for other scopes
               |
               +-- NO --> Retry the failed scope (Section 4.3)
                          Continue team
```

### 5.4 Conditions That Make a Team Unrecoverable

A team is unrecoverable when:

1. **The decomposition was wrong.** If the PM split the work incorrectly (overlapping scopes, missing dependencies), no amount of retrying will produce a clean merge. The decomposition must be revised, which requires user input or PM re-planning.

2. **The Engineers' changes are deeply interleaved.** If Engineer A and Engineer B both modified the same core module extensively, the merge will always conflict. This means the task was not suitable for parallel execution in the first place.

3. **Platform instability.** If Claude Code itself is experiencing issues (timeouts, process crashes), team execution amplifies the problem. One flaky agent is manageable; three flaky agents is chaos.

4. **Context window exhaustion.** If the PM has been managing a large team (5+ teammates) with multiple failures and retries, the PM's context window may be saturated with failed results, cleanup logs, and retry context. At this point, PM decision quality degrades. The PM should abort and start fresh.

---

## 6. Implications for PM_INSTRUCTIONS.md Changes

### 6.1 New Section: Team Recovery Protocol

The following should be added to PM_INSTRUCTIONS.md in Phase 2 implementation:

```markdown
### Team Recovery Protocol (Agent Teams)

When a teammate fails during an Agent Teams session:

1. **Detect:** Watch for TaskCompleted with failed status, timeout notifications,
   or invalid responses that fail the QA gate.

2. **Assess:** For Engineer teammates with worktrees:
   - Check `git log <branch>` for useful commits
   - Check uncommitted changes via `git diff` in the worktree
   - Determine if partial work is salvageable

3. **Decide:**
   - Failed Research/QA: discard and proceed (or retry QA)
   - Failed Engineer with no useful work: discard worktree, retry or proceed without
   - Failed Engineer with useful partial work: report to user for decision

4. **Clean up:** Remove stale worktrees and branches after every team session.
   Run `git worktree list` to verify no orphaned worktrees remain.

5. **Abort threshold:** After 3 total failures in a team session, abort the team
   and fall back to sequential execution. Report to user what succeeded and what failed.
```

### 6.2 New Section: Worktree Cleanup Obligation

```markdown
### Worktree Cleanup (Agent Teams with Engineer Teammates)

After completing or aborting a team session with worktree-isolated Engineers:

1. Run `git worktree list` to enumerate all worktrees.
2. Remove worktrees for completed/merged branches: `git worktree remove <path>`.
3. Force-remove worktrees for failed/discarded branches: `git worktree remove --force <path>`.
4. Delete orphaned branches: `git branch -D <branch>` for discarded branches.
5. Verify cleanup: only the main worktree should remain in `git worktree list`.

NEVER leave stale worktrees from a previous team session. They accumulate disk space
and can cause branch name conflicts in future sessions.
```

### 6.3 Extension to Existing Circuit Breaker #10

CB#10 (Delegation Failure Limit) currently reads: "After 3 failures to the same agent, PM stops and requests user guidance."

For Phase 2, extend to: "After 3 failures across all teammates in an Agent Teams session, PM aborts the team and falls back to sequential execution. The 3-failure limit applies to the TEAM, not to individual teammates."

---

## 7. Summary

### Key Findings

1. **Worktrees persist after process exit.** Git worktrees are filesystem artifacts, not process-scoped. Crashed or timed-out teammates leave worktrees behind indefinitely. PM must actively clean them up.

2. **Research/QA failures are low-risk.** These are stateless — discard and retry (or proceed without). This matches Phase 1's existing fallback protocol.

3. **Engineer failures are high-risk.** They leave stateful artifacts (worktrees, branches, partial commits) that must be assessed before cleanup. The PM needs a structured assessment protocol.

4. **Merge conflicts and post-merge build failures are the highest-risk modes.** Both are unique to Phase 2 and require dedicated resolution strategies (PM resolution, delegated Merge Engineer, or abort-and-revert).

5. **The abort threshold should be 3 failures per team session.** This aligns with existing CB#10 and prevents the PM from spending excessive context on a failing team.

6. **Sequential fallback is always available.** If a team fails, the PM can always fall back to sequential Agent execution without Agent Teams. This is the safety net.

### Risk Mitigation Summary

| Risk | Mitigation | Residual Risk |
|---|---|---|
| Stale worktree accumulation | PM cleanup obligation in PM_INSTRUCTIONS.md | LOW (if PM follows protocol) |
| Partial work assessment | Structured evaluation protocol (Section 4.2) | MEDIUM (PM must judge work quality) |
| Merge conflict resolution | Three-option resolution (PM, delegate, abort) | MEDIUM (complex conflicts may require user) |
| Post-merge integration failure | Blame attribution + targeted revert | MEDIUM (interaction bugs hard to diagnose) |
| Context exhaustion from retries | 3-failure abort threshold | LOW (abort prevents context bloat) |

---

## References

- `03-phase-1/02_parallel_research_design.md` Section 5 (Fallback Protocol)
- `src/claude_mpm/hooks/claude_hooks/hook_handler.py` lines 794-862 (process lifecycle — fresh process per hook, singleton-scoped)
- `src/claude_mpm/hooks/claude_hooks/event_handlers.py` lines 1655-1722 (TaskCompleted handler)
- `02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` CB#10 (Delegation Failure Limit — 3-failure threshold)
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md` lines 118-148 (worktree isolation for parallel agents)
- `src/claude_mpm/skills/bundled/collaboration/git-worktrees-superpowers.md` (worktree creation patterns)
- `src/claude_mpm/skills/bundled/collaboration/finishing-a-development-branch.md` (worktree cleanup patterns, Step 5)
- `git-worktree(1)` man page (prune behavior, gc.worktreePruneExpire)
