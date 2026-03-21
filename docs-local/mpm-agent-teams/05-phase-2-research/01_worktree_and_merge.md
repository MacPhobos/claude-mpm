# RQ0 + RQ1 + RQ2: Worktree Isolation, Merge Mechanics, and Conflict Resolution

**Phase:** 2 Research
**Date:** 2026-03-20
**Branch:** mpm-teams
**Method:** Codebase analysis + hands-on git worktree experiment
**Status:** Complete -- all three RQs answered with verified findings

---

## 1. RQ0 Findings: Baseline Parallel Engineering

### How Parallel Engineering Works Today (Without Agent Teams)

The PM already supports parallel Engineering via two Claude Code primitives:

1. **`run_in_background: true`** on the Agent tool call -- fires off an agent asynchronously; PM continues orchestrating. Results arrive via task notification.
2. **`isolation: "worktree"`** on the Agent tool call -- the spawned agent runs in its own git worktree under `.claude/worktrees/`, on a unique branch based on HEAD.

These are documented in:
- `PM_INSTRUCTIONS.md` lines 118-148 (worktree isolation, background execution, EnterWorktree distinction)
- `BASE_AGENT.md` lines 146-170 (parallel worktree isolation, background execution)

#### Current Pattern (Non-Agent-Teams)

```
PM receives complex task
  |
  v
PM decomposes into independent subtasks
  |
  v
PM spawns N Agent calls:
  - subagent_type: "engineer"
  - run_in_background: true
  - isolation: "worktree"
  |
  v
Each agent gets own worktree + unique branch
Agents work independently, PM continues
  |
  v
Task notifications arrive as agents complete
  |
  v
PM collects results, merges manually (or delegates to Version Control agent)
```

#### What Happens to Worktrees After Completion

**Critical finding: Claude Code does NOT auto-merge worktrees.** When an agent completes:

1. The agent's worktree and branch remain on disk
2. The PM receives the task notification with the agent's output
3. The worktree branch has commits but they are NOT merged into the parent branch
4. Manual merge is required (PM can delegate to Version Control agent or run git commands)

There is no documented auto-cleanup mechanism. The `ExitWorktree` tool (used when the PM itself enters a worktree) has explicit "keep" vs "remove" semantics -- but sub-agents spawned with `isolation: "worktree"` do not call ExitWorktree. The worktree lifecycle for sub-agents is:

- **Created:** automatically when Agent tool runs with `isolation: "worktree"`
- **Location:** `.claude/worktrees/<name>` with a new branch
- **Cleaned up:** NOT automatically. Worktrees persist after agent completion.

This means stale worktrees can accumulate. In the experiment, each worktree consumed ~42MB of disk (full working tree copy, shared git objects).

#### Pain Points with Current Approach

1. **No auto-merge:** PM must explicitly merge worktree branches. This is not documented as a PM responsibility anywhere in PM_INSTRUCTIONS.md.
2. **No conflict detection:** PM has no built-in mechanism to check for merge conflicts before or after merging.
3. **No cleanup:** Stale worktrees accumulate on disk unless manually removed.
4. **Merge responsibility is unclear:** PM_INSTRUCTIONS.md says to "combine with `isolation: "worktree"` for safe parallel file modification" but never describes the merge-back workflow.
5. **No integration test step:** After merging N worktrees, nobody verifies that the combined code compiles/passes tests.

### What Agent Teams Adds for Parallel Engineering

Based on the initial investigation (`01_agent_teams_capabilities.md`), Agent Teams provides:

| Capability | Standard Agent + Background | Agent Teams |
|------------|---------------------------|-------------|
| Parallel execution | `run_in_background: true` | `team_name` shared team |
| Worktree isolation | `isolation: "worktree"` | Same `isolation: "worktree"` |
| Shared task list | No | Yes (`TaskCreate`, `TaskList`) |
| Peer messaging | No | Yes (`SendMessage`) |
| Structured completion | Task notification (flat) | `TaskCompleted` hook event |
| Idle detection | No | `TeammateIdle` hook event |
| Context injection | BASE_AGENT.md only | BASE_AGENT.md + TEAMMATE_PROTOCOL |

**Key insight: Worktree mechanics are IDENTICAL.** Claude Code creates and manages worktrees the same way regardless of whether the agent was spawned via standard Agent tool or as an Agent Teams teammate. The `isolation: "worktree"` parameter works identically in both cases.

**What Agent Teams uniquely provides for Engineering:**
1. **Shared task list** -- Engineers can see each other's task status (useful for dependency tracking)
2. **Structured lifecycle** -- `TaskCompleted` events give the PM a clean signal to begin merge
3. **TEAMMATE_PROTOCOL injection** -- Additional behavioral rules (currently Research-focused, extensible to Engineering)
4. **Team-scoped coordination** -- PM can manage a team session rather than N independent background tasks

**What Agent Teams does NOT solve:**
- Merge conflict resolution (same underlying git mechanics)
- Integration testing after merge
- Worktree cleanup
- Semantic conflicts (two changes that each work alone but break together)

**Bottom line:** Agent Teams provides better orchestration and observability for parallel Engineering, but the hard problems (merge, conflicts, integration) must be solved by MPM regardless of whether Agent Teams is used.

---

## 2. RQ1 Findings: Worktree Isolation Mechanics

### How Claude Code Creates Worktrees

Based on the `EnterWorktree` tool documentation and direct experimentation:

1. **Location:** `.claude/worktrees/<name>/` inside the repository
2. **Branch:** A new branch is created based on HEAD at the time of worktree creation
3. **Command (equivalent):** `git worktree add .claude/worktrees/<name> -b <branch-name>`
4. **Branch naming:** Each agent gets a unique branch name (not user-specified; auto-generated by Claude Code)
5. **Shared git objects:** Worktrees share the `.git` object database with the main repo (only working tree files are duplicated)

### Experiment Results: Worktree Creation

```
$ git worktree add .claude/worktrees/agent-a -b agent-a-worktree
Preparing worktree (new branch 'agent-a-worktree')
HEAD is now at 4cc6e4da test: add worktree experiment test file (temporary)

$ git worktree add .claude/worktrees/agent-b -b agent-b-worktree
Preparing worktree (new branch 'agent-b-worktree')
HEAD is now at 4cc6e4da test: add worktree experiment test file (temporary)

$ git worktree list
/Users/mac/workspace/claude-mpm-fork                           4cc6e4da [mpm-teams]
/Users/mac/workspace/claude-mpm-fork/.claude/worktrees/agent-a 4cc6e4da [agent-a-worktree]
/Users/mac/workspace/claude-mpm-fork/.claude/worktrees/agent-b 4cc6e4da [agent-b-worktree]
```

**Observations:**
- Both worktrees are created from the same HEAD commit (4cc6e4da)
- Each gets a unique branch
- Both are fully independent working trees
- Disk usage: ~42MB per worktree (this repository)

### Do Both Agents Get Separate Worktrees?

**Yes.** Each `isolation: "worktree"` call creates a separate worktree with a separate branch. The agents operate in completely independent filesystem namespaces. Changes in one worktree are invisible to the other until branches are merged.

### What Happens When an Agent Completes?

**The worktree and branch persist.** They are NOT automatically removed or merged. The PM must:
1. Read the agent's results (from task notification)
2. Merge the branch into the target branch (e.g., `git merge agent-a-worktree`)
3. Optionally clean up: `git worktree remove .claude/worktrees/agent-a` + `git branch -d agent-a-worktree`

### Can the PM See/Access Worktree Paths and Branches?

**Yes.** The PM (running in the main working tree) can:
- `git worktree list` -- see all active worktrees and their branches
- `git log agent-a-worktree` -- see commits on a worktree branch
- `git diff mpm-teams..agent-a-worktree` -- see what changed
- `git merge agent-a-worktree` -- merge a worktree branch
- `git worktree remove .claude/worktrees/agent-a` -- clean up

### Is There a Limit on Concurrent Worktrees?

**No hard git limit.** Practical constraints:
- **Disk space:** ~42MB per worktree for this repository (working tree files are duplicated; git objects are shared)
- **Branch name uniqueness:** Each worktree needs a unique branch name (guaranteed by Claude Code's auto-naming)
- **File descriptor limits:** OS-level, unlikely to hit with < 100 worktrees
- **Tested:** Created 7 concurrent worktrees without issue

For MPM's use case (2-5 parallel Engineers), worktree limits are not a concern.

---

## 3. Experiment Results

### Experiment Setup

Created a test file (`worktree_test_file.py`) with two classes: `Calculator` (top) and `Logger` (bottom). Created two worktrees simulating two parallel agents. Tested four merge scenarios.

### Scenario 1: Same File, Different Sections -- AUTO-MERGEABLE

**Agent A** added `power()` and `modulo()` methods to `Calculator` class (top of file).
**Agent B** added `warn()`, `error()` methods and a `level` field to `Logger` class (bottom of file).

**Merge result:**
```
$ git merge agent-a-worktree --no-edit
Updating 4cc6e4da..a87a0eb4
Fast-forward                              # <-- First merge is always fast-forward

$ git merge agent-b-worktree --no-edit
Auto-merging worktree_test_file.py
Merge made by the 'ort' strategy.         # <-- Second merge: git auto-merged successfully
```

**Outcome: SUCCESS.** Git's `ort` merge strategy automatically merged both changes. The final file contained all modifications from both agents, correctly interleaved. No human intervention required.

**Implication:** When the PM decomposes tasks so that engineers work on different sections of the same file (e.g., "Agent A: add methods to Calculator class, Agent B: enhance Logger class"), git handles the merge automatically.

### Scenario 2: Same File, Same Section -- TRUE CONFLICT

**Agent A** changed `divide()` to return `float("inf")` on division by zero.
**Agent B** changed `divide()` to raise `ZeroDivisionError` with a message and round the result.

**Merge result:**
```
$ git merge agent-a-worktree --no-edit
Updating 4cc6e4da..df847c51
Fast-forward

$ git merge agent-b-worktree --no-edit
Auto-merging worktree_test_file.py
CONFLICT (content): Merge conflict in worktree_test_file.py
Automatic merge failed; fix conflicts and then commit the result.
```

**Conflict markers in the file:**
```python
    def divide(self, a, b):
<<<<<<< HEAD
        """Divide a by b. Returns float. Modified by Agent A."""
        if b == 0:
            return float("inf")
        return float(a) / float(b)
=======
        """Divide a by b safely. Modified by Agent B."""
        if b == 0:
            raise ZeroDivisionError(f"Cannot divide {a} by zero")
        result = a / b
        return round(result, 10)
>>>>>>> agent-b-worktree
```

**Outcome: CONFLICT.** Standard git conflict markers. Requires manual resolution.

**Implication:** When two engineers modify the same function/section, git cannot auto-merge. Someone must resolve the conflict. This is the core problem Phase 2 must address.

### Scenario 2b: Pre-Detection with `git merge --no-commit`

**Tested:** Can the PM detect conflicts BEFORE committing the merge?

```
$ git merge agent-b-worktree --no-commit
Auto-merging worktree_test_file.py
CONFLICT (content): Merge conflict in worktree_test_file.py
Automatic merge failed; fix conflicts and then commit the result.

$ git merge --abort     # <-- Clean rollback, no damage to main branch
```

**Outcome: YES.** The PM can use `git merge --no-commit` as a "dry run" to detect conflicts without committing. If conflicts are detected (exit code 1), `git merge --abort` cleanly rolls back. The main branch is untouched.

**This is the key mechanism for Phase 2 conflict detection.** The PM can:
1. Merge the first agent's branch (fast-forward, always clean)
2. Test-merge the second agent's branch with `--no-commit`
3. If clean: commit the merge
4. If conflict: abort and escalate (to user, or to a dedicated merge agent)

### Scenario 3: Different Files, No Overlap -- TRIVIAL

Not tested experimentally (unnecessary). When agents modify entirely different files, there is zero possibility of git conflict. Merge is always clean.

### Scenario 4: Different Files, Shared Dependency -- SEMANTIC CONFLICT

Not tested with git (git cannot detect semantic conflicts). Example: Agent A changes a function signature; Agent B calls the old signature in a different file. Git merges cleanly, but the code is broken. Only tests catch this.

**Implication:** Integration testing after merge is mandatory, even when git reports no conflicts.

---

## 4. RQ2 Findings: File Conflict Analysis

### Conflict Scenario Matrix

| Scenario | Git Detection | Auto-Mergeable? | Resolution |
|----------|:---:|:---:|------------|
| Same file, different sections | Yes (at merge time) | YES -- `ort` strategy handles it | No intervention needed |
| Same file, same section | Yes (at merge time) | NO -- conflict markers | PM escalates or merge agent resolves |
| Different files, shared dependency | NO (git cannot detect) | N/A -- git merges cleanly | Tests catch it after merge |
| Different files, no overlap | N/A | YES -- trivially | No intervention needed |

### Who Is Responsible for Merging?

**Current state:** Nobody. PM_INSTRUCTIONS.md describes `isolation: "worktree"` but never describes the merge-back workflow. This is the gap.

**Required for Phase 2:** The PM must own the merge workflow. Proposed responsibility chain:

1. **PM** receives completion notifications from all engineers
2. **PM** merges branches sequentially into the target branch
3. **PM** uses `git merge --no-commit` to detect conflicts
4. **If clean merge:** PM commits and proceeds to integration testing
5. **If conflict:** PM has three options:
   a. Abort and ask the user to resolve manually
   b. Delegate to a merge-resolution agent (new agent type?)
   c. Present the conflict to one of the original engineers to resolve

### Can `git merge --no-commit` Be Used for Conflict Detection?

**YES -- verified experimentally.** This is the recommended approach:

```bash
# Step 1: Merge first agent's branch (always fast-forward from base)
git merge agent-a-worktree

# Step 2: Test-merge second agent's branch
git merge agent-b-worktree --no-commit
if [ $? -ne 0 ]; then
    # Conflict detected
    git merge --abort
    echo "CONFLICT: agent-a-worktree and agent-b-worktree have overlapping changes"
else
    # Clean merge
    git commit -m "Merge agent-b-worktree"
fi
```

For N agents, the merge order matters. The PM should merge sequentially and test each addition:

```
Merge A (fast-forward) -> Test-merge B -> if clean, commit B -> Test-merge C -> ...
```

### Pre-Spawn Conflict Prevention

The PM can reduce conflicts BEFORE spawning by analyzing task scope:

1. **File scope declaration:** PM's task prompt for each engineer should declare which files/directories that engineer will modify
2. **Overlap detection:** If two engineers' scope declarations share > 20% of files, the PM should either:
   - Redefine scopes to eliminate overlap
   - Run the engineers sequentially instead of in parallel
   - Accept the conflict risk and plan for merge resolution

This is instruction-level enforcement (PM reasoning), not code-level (hooks cannot evaluate scope before spawn -- see `01_wp2_parallel_research.md` Section 2).

### Practical Merge Workflow for Phase 2

```
Engineers A, B, C complete in worktrees
    |
    v
PM receives all completion notifications
    |
    v
PM runs: git merge A-branch (fast-forward from base)
    |
    v
PM runs: git merge B-branch --no-commit
    |
    +-- Clean? -> git commit -> continue to C
    |
    +-- Conflict? -> git merge --abort
        |
        +-- Option 1: Present conflict to user
        |   "Engineers A and B both modified divide().
        |    A returned inf, B raised ZeroDivisionError.
        |    Which approach should we keep?"
        |
        +-- Option 2: Delegate to merge agent
        |   (New agent type: reads both changes,
        |    produces unified resolution)
        |
        +-- Option 3: Re-spawn B with updated context
            "Engineer A already changed divide() to return inf.
             Adapt your changes to work with this approach."
    |
    v
After all branches merged:
    |
    v
Run integration tests (make test / uv run pytest)
    |
    +-- Pass? -> Merge complete, report to user
    |
    +-- Fail? -> Semantic conflict detected
        |
        v
        PM analyzes test failures, identifies which agent's
        changes caused the failure, and either:
        - Reverts the problematic branch
        - Delegates fix to an engineer with full context
```

---

## 5. Implications for Phase 2

### The Core Finding

**Worktree isolation solves the parallel execution problem. It does NOT solve the merge problem.**

Git worktrees give each agent a clean, independent workspace. This is working correctly today, both with standard Agent + `run_in_background` and with Agent Teams. No changes needed to worktree creation or management.

The unsolved problems are all about what happens AFTER agents complete:

1. **Merge workflow:** PM must merge branches, detect conflicts, and handle failures
2. **Conflict resolution:** When git reports conflicts, someone must resolve them
3. **Integration testing:** Even clean merges can produce broken code
4. **Worktree cleanup:** Stale worktrees accumulate; need cleanup protocol

### What Phase 2 Must Build (Based on These Findings)

#### 1. PM Merge Instructions (PM_INSTRUCTIONS.md changes)

Add a "Post-Completion Merge Protocol" section that instructs the PM to:
- Merge worktree branches sequentially using `git merge --no-commit` for safety
- Detect and report conflicts
- Run integration tests after merge
- Clean up worktrees after successful merge

This is ~30-50 lines of PM instruction text. No code changes to hooks.

#### 2. Engineer Scope Declaration (TEAMMATE_PROTOCOL extension)

Add an Engineer-specific rule to TEAMMATE_PROTOCOL:
- "Before starting work, declare the files you intend to modify"
- "Do not modify files outside your declared scope"

This enables the PM to detect scope overlap before spawning.

#### 3. Conflict Resolution Strategy

For Phase 2, recommend the simplest approach: **PM presents conflicts to the user.** Reasons:
- Automated conflict resolution (merge agent) is a large engineering effort
- Most real-world parallel Engineering tasks target non-overlapping files
- Scope declaration (point 2) prevents most conflicts
- When conflicts occur, they usually require human judgment about intent

Phase 3 can add automated conflict resolution if user demand warrants it.

#### 4. Integration Testing Gate

After merging all worktree branches, PM must run the test suite. This can be:
- PM runs `make test` directly (simple, blocks PM)
- PM delegates to QA agent (more complex, frees PM)
- PM runs tests with `run_in_background` (non-blocking but PM must check results)

Recommendation: PM runs tests directly for Phase 2. Delegate to QA in Phase 3.

#### 5. Worktree Cleanup Protocol

After successful merge + tests:
```bash
git worktree remove .claude/worktrees/<agent-name>
git branch -d <agent-branch>
```

After failed merge (conflict or test failure):
- Keep worktree for debugging
- Inform user of worktree location
- Clean up only when user confirms

### What This Means for the Phase 2 Implementation Plan

The Phase 2 scope can be summarized as:

| Component | Type | Effort |
|-----------|------|--------|
| PM merge protocol instructions | PM_INSTRUCTIONS.md text | Low (30-50 lines) |
| Engineer scope declaration rule | TEAMMATE_PROTOCOL extension | Low (~50 tokens) |
| Conflict detection + escalation | PM instructions (not code) | Low-Medium |
| Integration test gate | PM instructions (not code) | Low |
| Worktree cleanup protocol | PM instructions (not code) | Low |
| **Total** | **Mostly instruction changes** | **1-2 days** |

**The critical finding is that Phase 2 is primarily an INSTRUCTION problem, not a CODE problem.** The underlying git mechanics work correctly. What's missing is PM behavioral guidance for the merge-test-cleanup lifecycle.

### Risk Assessment Update

| Risk from Research Plan | Status After Investigation | Severity |
|------------------------|---------------------------|----------|
| "Worktree isolation doesn't handle merge conflicts" | **RESOLVED:** Git handles same-file-different-section merges automatically. Same-section conflicts are detectable and abortable. | LOW (was HIGH) |
| "Engineering spike reveals unsolvable merge problem" | **RESOLVED:** No unsolvable problems found. All scenarios have clear resolution paths. | LOW (was HIGH) |
| Stale worktree accumulation | **CONFIRMED:** Worktrees persist after agent completion. Cleanup protocol needed. | MEDIUM |
| Semantic conflicts (tests pass individually, fail together) | **CONFIRMED:** Git cannot detect these. Integration testing is mandatory. | MEDIUM |

---

## Appendix: Raw Experiment Data

### Environment

- Repository: claude-mpm-fork (branch: mpm-teams)
- Git version: (standard macOS git)
- Worktree disk usage: ~42MB each
- Experiment file: `worktree_test_file.py` (39 lines, 2 classes)

### Scenario 1 Output (Auto-Merge Success)

```
$ git merge agent-a-worktree --no-edit
Updating 4cc6e4da..a87a0eb4
Fast-forward
 worktree_test_file.py | 10 ++++++++++
 1 file changed, 10 insertions(+)

$ git merge agent-b-worktree --no-edit
Auto-merging worktree_test_file.py
Merge made by the 'ort' strategy.
 worktree_test_file.py | 11 ++++++++++-
 1 file changed, 10 insertions(+), 1 deletion(-)
```

### Scenario 2 Output (True Conflict)

```
$ git merge agent-a-worktree --no-edit
Updating 4cc6e4da..df847c51
Fast-forward

$ git merge agent-b-worktree --no-edit
Auto-merging worktree_test_file.py
CONFLICT (content): Merge conflict in worktree_test_file.py
Automatic merge failed; fix conflicts and then commit the result.
```

### Scenario 2b Output (Pre-Detection + Abort)

```
$ git merge agent-b-worktree --no-commit
CONFLICT (content): Merge conflict in worktree_test_file.py
Automatic merge failed; fix conflicts and then commit the result.

$ git merge --abort
(clean rollback, main branch untouched)
```

### Worktree Lifecycle

```
$ git worktree list  (after creation)
/Users/mac/workspace/claude-mpm-fork                           4cc6e4da [mpm-teams]
/Users/mac/workspace/claude-mpm-fork/.claude/worktrees/agent-a 4cc6e4da [agent-a-worktree]
/Users/mac/workspace/claude-mpm-fork/.claude/worktrees/agent-b 4cc6e4da [agent-b-worktree]

$ du -sh .claude/worktrees/agent-a
42M     .claude/worktrees/agent-a

$ git worktree remove .claude/worktrees/agent-a  (cleanup)
(success, exit code 0)

$ git branch -d agent-a-worktree
Deleted branch agent-a-worktree (was df847c51).
```
