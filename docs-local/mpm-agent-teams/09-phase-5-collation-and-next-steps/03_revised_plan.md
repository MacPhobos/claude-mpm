# Revised Plan: Phase 2 Completion

**Date:** 2026-03-21
**Branch:** `mpm-teams`
**Predecessor docs:** `00_collation.md`, `01_worktree_research.md`, `02_devils_advocate.md`
**Status:** EXPERIMENT COMPLETE — Outcome A confirmed. Proceeding with Outcome A action plan.

---

## 1. Current Status

Phase 2 implementation is code-complete and provably correct: 262 deterministic tests pass in 0.68s, protocol routing works for all roles, token budgets are within limits, backward compatibility is preserved, and the scoring pipeline runs end-to-end. Gate A is PASSED. Gate B is 2/6 observed (B1 spawn with worktree: PASS, B3 run tests after merge: PASS). The four remaining Gate B items split into two categories: B4/B6 are testable now (pipeline sequencing, sub-threshold rejection), while B2/B5 (merge delegation, worktree cleanup) depend on resolving a single question -- what happens when an agent commits inside a worktree? Binary analysis confirms Claude Code creates real git worktrees and preserves them when HEAD changes (agent committed), but Session 1 agents never committed, so worktrees were cleaned up and changes appeared as unstaged modifications in the parent tree. A 15-minute experiment will determine whether instructing agents to commit fixes the entire merge protocol.

---

## 2. The Worktree Question -- Resolved

### What we know (confirmed from 3 independent sources)

1. `isolation: "worktree"` creates **real git worktrees** via `git worktree add` equivalent code (binary implementation + documentation + system prompt injection)
2. The cleanup function checks whether HEAD changed in the worktree:
   - HEAD unchanged (no commits) -> worktree removed, returns `{}`
   - HEAD changed (agent committed) -> worktree preserved, returns `{ worktreePath, worktreeBranch }`
3. A telemetry event `worktree_resolved_to_main_repo` (3 occurrences in binary) suggests a deliberate copy-back mechanism for uncommitted worktree changes

### What we hypothesize

Session 1 agents never committed their changes. The cleanup function saw HEAD unchanged, removed the worktrees, and the `worktree_resolved_to_main_repo` mechanism copied unstaged changes back to the parent working tree. This is why 6 modified files appeared in the parent as unstaged modifications.

If agents had committed, the cleanup function would have preserved the worktrees with their branches, and the PM's merge protocol would have found real branches to merge.

### Experiment Result: OUTCOME A CONFIRMED (2026-03-21)

An agent that commits inside a worktree **does** produce a persistent worktree and branch:

```
Worktree path:   .claude/worktrees/agent-aa50b991
Branch:          worktree-agent-aa50b991
Commit:          48499226 test: worktree commit persistence experiment
Parent tree:     Clean (no unstaged changes, marker file NOT in parent)
git worktree list: 2 entries (main + agent worktree)
```

**The merge protocol works as designed.** Session 1 failed because agents didn't commit, not because worktrees don't work. The fix is a one-line addition to TEAMMATE_PROTOCOL_ENGINEER: instruct agents to commit before reporting completion.

---

## 3. Controlled Experiment Design (15 minutes)

### Setup

Ensure a clean working tree before starting:

```bash
git status  # verify clean
git stash list  # note stash@{0} from Session 1 still exists
```

### The Experiment

Spawn ONE agent with `isolation: "worktree"`. The agent's task: create a trivial file AND commit it. No `team_name`, no `run_in_background` -- keep it simple.

**Exact prompt to use (copy-paste into Claude Code):**

```
Spawn a single agent with these EXACT parameters:

Agent tool call:
  subagent_type: "Engineer"
  isolation: "worktree"
  description: "worktree commit test"
  prompt: |
    You are testing worktree commit behavior. Do exactly these steps:
    1. Run: pwd (report the path)
    2. Run: git worktree list (report output)
    3. Run: git branch --show-current (report branch name)
    4. Create file: echo "worktree-test-$(date +%s)" > worktree_test_marker.txt
    5. Run: git add worktree_test_marker.txt
    6. Run: git commit -m "test: worktree commit persistence experiment"
    7. Run: git log --oneline -3 (report output)
    8. Report ALL outputs from steps 1-7.

Do NOT use run_in_background. Do NOT use team_name. Wait for the agent to complete, then report its full output to me.
```

### Post-Experiment Checks

After the agent completes, run these commands **yourself** (not delegated):

```bash
# Check 1: Does the worktree still exist?
git worktree list

# Check 2: Does the agent's branch exist?
git branch --sort=-committerdate | head -10

# Check 3: Is the commit visible?
git log --all --oneline | head -20

# Check 4: Is there a marker file in the parent tree?
ls -la worktree_test_marker.txt 2>/dev/null && echo "EXISTS in parent" || echo "NOT in parent"

# Check 5: Are there unstaged changes?
git status
```

### Expected Outcomes

**Outcome A -- Worktree persists after commit (HYPOTHESIS):**
- `git worktree list` shows 2+ entries (main + agent worktree)
- `git branch` shows an `agent-XXXXXXXX` branch
- `git log --all --oneline` shows the test commit on that branch
- `worktree_test_marker.txt` does NOT exist in parent tree
- `git status` is clean in parent

**Outcome B -- Worktree cleaned up, changes in parent tree:**
- `git worktree list` shows only 1 entry (main)
- No new branches
- `worktree_test_marker.txt` EXISTS in parent tree (staged or unstaged)
- The commit may or may not be in reflog

**Outcome C -- Worktree cleaned up, changes lost:**
- `git worktree list` shows only 1 entry (main)
- No new branches
- `worktree_test_marker.txt` does NOT exist anywhere
- `git status` clean -- changes were discarded

### Cleanup After Experiment

```bash
# If Outcome A: remove the test worktree and branch
git worktree remove <path-from-worktree-list> 2>/dev/null
git branch -D <agent-branch-name> 2>/dev/null

# If Outcome B: remove the test file from parent
git checkout -- worktree_test_marker.txt 2>/dev/null
rm -f worktree_test_marker.txt

# If Outcome C: nothing to clean up
```

---

## 4. Decision Tree: What to Do Based on Experiment Results

### If Outcome A (worktree persists after commit)

The existing merge protocol in PM_INSTRUCTIONS.md is **correct as designed**. The root cause of Session 1 failure was that agents never committed, not that worktrees don't work.

**Action plan:**
1. Add "You MUST commit your changes" to `TEAMMATE_PROTOCOL_ENGINEER` (Section 6 below)
2. Keep the existing merge protocol in PM_INSTRUCTIONS.md lines 1207-1258 as-is
3. Add one PM instruction: "Report actual isolation mechanism observed" (Section 5 below)
4. Add one PM instruction: "Commit integrated result after merge" (Section 5 below)
5. Re-run Gate B Session 1b with commit-instructed agents
6. Expected: B2 (merge delegation) and B5 (worktree cleanup) now pass because branches exist

### If Outcome B (changes in parent tree despite commit)

The `worktree_resolved_to_main_repo` mechanism always copies changes back to parent regardless of commits. The merge protocol is based on a false premise.

**Action plan:**
1. Add "You MUST commit your changes" to `TEAMMATE_PROTOCOL_ENGINEER` (still beneficial for audit trail)
2. Replace the merge protocol with a "verify + test + commit" workflow (Section 5 below)
3. Redefine B2 as "PM verifies parallel changes integrated correctly (git status + file review)"
4. Redefine B5 as "PM commits integrated changes with attribution"
5. Update `extract_gate_b_evidence.py` criteria for B2/B5
6. Re-run Gate B Session 1b with new criteria

### If Outcome C (changes lost)

Worktree isolation is broken -- commits inside worktrees are discarded on cleanup.

**Action plan:**
1. Remove `isolation: "worktree"` from all PM instructions
2. Replace with standard `run_in_background: true` without isolation
3. Add file-scope enforcement as the primary conflict prevention mechanism
4. Rewrite merge protocol entirely for "shared working tree" model
5. This is the most invasive change -- budget 4-6 hours instead of 1-2

---

## 5. PM Instruction Changes

### Changes for Outcome A (worktree persists)

**PM_INSTRUCTIONS.md line 1198 -- add commit step after merge:**

Before:
```
5. Delegate merge to a Version Control or Local Ops agent (see Merge Protocol)
6. Run `make test` directly after merge (timeout: 300000)
```

After:
```
5. Delegate merge to a Version Control or Local Ops agent (see Merge Protocol)
6. Run `make test` directly after merge (timeout: 300000)
7. If tests pass, commit the merged result with a message attributing each Engineer's contribution
```

**PM_INSTRUCTIONS.md -- add after line 1224 (after "PM escalates to user with conflict details"):**

```
### Post-Completion Reporting

When reporting team session results, describe the ACTUAL mechanism observed, not
the mechanism specified in Agent calls. If agents were spawned with
`isolation: "worktree"` but changes appeared in the parent working tree instead of
on separate branches, report that. Do not claim worktree isolation worked if
evidence shows otherwise.
```

### Changes for Outcome B (changes in parent tree)

**PM_INSTRUCTIONS.md lines 1207-1258 -- replace entire Merge Protocol and Worktree Cleanup sections:**

Before (lines 1207-1258):
```
### Merge Protocol
[... 17 lines of branch-based merge instructions ...]

### Build Verification (After Merge)
[... 12 lines unchanged ...]

### Worktree Cleanup
[... 10 lines of worktree removal instructions ...]
```

After:
```
### Post-Agent Integration

After parallel Engineers with `isolation: "worktree"` complete:

1. Run `git status` to verify expected files are modified
2. Run `git diff --stat HEAD` to confirm change scope matches each Engineer's declared scope
3. If unexpected files are modified, investigate before proceeding
4. Run `make test` directly (timeout: 300000)
5. If tests pass, commit the integrated changes:
   > git add <files-from-engineer-A-scope> <files-from-engineer-B-scope>
   > git commit -m "feat: <description>\n\nEngineers: <A-scope>, <B-scope>"
6. If tests fail, see Build Verification below

NOTE: `isolation: "worktree"` provides process isolation during agent execution.
After agents complete, changes appear as unstaged modifications in the parent
working tree. There are no branches to merge -- verify and commit directly.

### Build Verification (After Integration)

After running `make test`:
- All tests pass: commit and proceed to report and cleanup.
- Tests fail with NEW failures: correlate failing tests with each Engineer's
  change scope using `git diff --stat`. Classify as single-scope fault,
  interaction fault, or pre-existing.
  - Single-scope fault: revert that scope with `git checkout -- <files>`, re-run tests.
  - Interaction fault: spawn a fix-up Engineer with BOTH scopes' context.
  - Unattributable: revert all with `git checkout -- .`, fall back to sequential execution.
- Do NOT delegate integration testing to a QA agent. PM runs tests directly.
```

**PM_INSTRUCTIONS.md -- remove lines 1249-1258 (Worktree Cleanup section) entirely for Outcome B**, since there are no worktrees to clean up.

---

## 6. TEAMMATE_PROTOCOL_ENGINEER Change (either outcome)

Both outcomes benefit from agents committing their work. This change applies regardless of experiment result.

**File:** `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` lines 54-60

Before:
```python
TEAMMATE_PROTOCOL_ENGINEER = """\
### Engineer Rules
- You MUST state "QA verification has not been performed" when reporting completion. Do NOT claim your work is fully verified.
- Declare intended file scope BEFORE starting work. Do not modify files outside that scope.
- Run linting/formatting checks before reporting completion.
- Include git diff summary (files changed, insertions, deletions) in your completion report.
- You are working in an isolated worktree. Do not reference or modify files in the main working tree."""
```

After:
```python
TEAMMATE_PROTOCOL_ENGINEER = """\
### Engineer Rules
- You MUST state "QA verification has not been performed" when reporting completion. Do NOT claim your work is fully verified.
- Declare intended file scope BEFORE starting work. Do not modify files outside that scope.
- Run linting/formatting checks before reporting completion.
- You MUST commit your changes with a descriptive message before reporting completion. Use: git add <your-files> && git commit -m "feat: <description>"
- Include git diff summary (files changed, insertions, deletions) in your completion report.
- You are working in an isolated worktree. Do not reference or modify files in the main working tree."""
```

**Change summary:** Replaced bullet 4 ("Include git diff summary") with a commit instruction, moved diff summary to bullet 5. Net: +1 bullet point, ~15 additional tokens.

**Test impact:** Update `tests/hooks/test_teammate_context_injector.py` assertions that check `TEAMMATE_PROTOCOL_ENGINEER` content:
- Any test asserting exact engineer protocol text needs the new "commit your changes" line
- Token budget tests may need threshold adjustment (estimate: ~1850 chars, still under 2000)

---

## 7. Gate B Revised Scenarios

### Session 1b: Re-run Engineer Parallel (B1, B2, B3, B5)

**Purpose:** Test the same parallel engineering scenario as Session 1, but with the commit instruction added to TEAMMATE_PROTOCOL_ENGINEER.

**Prerequisite:** TEAMMATE_PROTOCOL_ENGINEER change from Section 6 is deployed.

**Prompt (copy-paste):**

```
I need you to add structured logging to this project. This requires parallel work:

Engineer A: Add a --verbose flag to the CLI entry point in src/claude_mpm/cli/
Engineer B: Add verbose-mode log statements to the hook handlers in src/claude_mpm/hooks/claude_hooks/

These are non-overlapping file scopes. Use Agent Teams with worktree isolation.
```

**Expected observations (Outcome A):**
- B1: PM spawns 2+ Engineers with `isolation: "worktree"` (re-confirms)
- B2: PM delegates merge to Version Control agent (NOW POSSIBLE -- branches exist)
- B3: PM runs `make test` after merge
- B5: PM delegates worktree cleanup (NOW POSSIBLE -- worktrees exist to clean)

**Expected observations (Outcome B):**
- B1: PM spawns 2+ Engineers with `isolation: "worktree"` (re-confirms)
- B2 (revised): PM runs `git status` + `git diff --stat` to verify changes
- B3: PM runs `make test` after integration
- B5 (revised): PM commits integrated changes with attribution

### Session 2: Research-then-Engineer Pipeline (B4)

**Purpose:** Verify PM sequences Research before Engineer phase.

**Prompt:**

```
I need to improve error handling in the webhook processing pipeline. First, research what error patterns currently exist in the codebase, then have an engineer implement improvements based on the findings.
```

**Expected observation:**
- B4: PM spawns Research agent first, waits for completion, then spawns Engineer with Research findings as context

### Session 3: Sub-Threshold Rejection (B6)

**Purpose:** Verify PM rejects team for trivial task.

**Prompt:**

```
Add a one-line comment to src/claude_mpm/cli/__init__.py explaining what the module does.
```

**Expected observation:**
- B6: PM either delegates to a single agent (no team) or explains why a team is unnecessary

### extract_gate_b_evidence.py Updates

**If Outcome A (no criteria changes):** No updates needed -- B2 and B5 criteria remain as-is.

**If Outcome B (criteria redefined):**

Update the B2 criterion from:
```python
"B2": {"pattern": r"(Version Control|Local Ops).*merge", "description": "PM delegates merge"}
```
To:
```python
"B2": {"pattern": r"git (status|diff --stat)", "description": "PM verifies parallel changes integrated"}
```

Update the B5 criterion from:
```python
"B5": {"pattern": r"(Version Control|Local Ops).*cleanup|worktree remove", "description": "PM delegates cleanup"}
```
To:
```python
"B5": {"pattern": r"git (add|commit).*Engineer|feat:", "description": "PM commits integrated changes"}
```

---

## 8. Cleanup Before Experiment

```bash
# 1. Verify stash from Session 1 still exists
git stash list

# 2. Drop the Session 1 stash (engineer-generated code, not needed for experiment)
# NOTE: Only drop if user confirms. The stash contains 220 insertions across 6 files
# (structured logging + verbose flag). If wanted, pop instead of drop.
git stash drop stash@{0}

# 3. Verify clean working tree
git status

# 4. Verify on correct branch
git branch --show-current  # should be mpm-teams
```

**Decision for user:** The stash at `stash@{0}` contains engineer-generated structured logging code (220 insertions, 11 deletions, 6 files). Options:
- **Drop it** (`git stash drop`) -- this was test output, will be regenerated properly in Session 1b
- **Pop it** (`git stash pop`) -- if the code is wanted, pop and commit it now before the experiment
- **Keep it** -- leave stash in place, it won't interfere with the experiment

Recommendation: **Drop it.** Session 1b will regenerate similar work with proper commit behavior.

---

## 9. Timeline

### Day 1 (estimated 3-4 hours active work)

| Step | Time | Description |
|------|------|-------------|
| Cleanup | 5 min | Drop stash, verify clean tree |
| Experiment | 15 min | Run worktree commit test, check results |
| Decision | 5 min | Determine Outcome A, B, or C |
| TEAMMATE_PROTOCOL change | 30 min | Edit injector, update tests, run `make test` |
| PM_INSTRUCTIONS change | 1 hour | Edit based on experiment outcome, review |
| Session 1b | 30 min | Parallel engineering with commit instruction |
| Gate B evidence extraction | 30 min | Run extract script, update gate results |

### Day 2 (estimated 1.5-2 hours active work)

| Step | Time | Description |
|------|------|-------------|
| Session 2 (B4) | 20 min | Research-then-Engineer pipeline |
| Session 3 (B6) | 10 min | Sub-threshold rejection |
| Gate B evidence extraction | 15 min | Extract B4, B6 evidence |
| Gate results update | 30 min | Update `03_gate_results.md` with all 6 criteria |
| Final review | 30 min | Collation update, PR preparation |

**Total: ~5-6 hours of active work across 2 days.**

---

## 10. Definition of Done

Phase 2 is complete and ready for PR merge when ALL of the following are true:

### Code Quality
- [ ] All existing tests pass (`make test` -- 7924+ passed, 0 new failures)
- [ ] TEAMMATE_PROTOCOL_ENGINEER includes commit instruction
- [ ] PM_INSTRUCTIONS.md reflects actual worktree behavior (based on experiment)
- [ ] New/updated tests for protocol changes pass

### Gate A (unchanged)
- [ ] 262 deterministic tests pass in < 2s
- [ ] Protocol token budgets under 2000 chars per role

### Gate B (6/6 observed)
- [ ] B1: PM spawns 2+ Engineers with `isolation: "worktree"` -- PASS (Session 1, confirmed Session 1b)
- [ ] B2: PM handles post-agent integration correctly (merge branches OR verify working tree, per experiment)
- [ ] B3: PM runs `make test` after integration -- PASS (Session 1, confirmed Session 1b)
- [ ] B4: PM sequences Research before Engineer phase (Session 2)
- [ ] B5: PM handles post-session cleanup correctly (cleanup worktrees OR commit changes, per experiment)
- [ ] B6: PM rejects or avoids team for trivial task (Session 3)

### Documentation
- [ ] `03_gate_results.md` updated with all 6 Gate B criteria and evidence
- [ ] Collation document (`00_collation.md`) updated with final status
- [ ] No inaccurate claims about worktree behavior in any committed file

### PR Readiness
- [ ] Single squash-friendly commit history (or clean commit chain)
- [ ] PR description summarizes: what was built, gate results, worktree finding
- [ ] No stale stashes, test marker files, or debug artifacts in working tree
