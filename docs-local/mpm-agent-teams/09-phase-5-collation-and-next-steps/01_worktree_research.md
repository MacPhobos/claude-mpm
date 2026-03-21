# How `isolation: worktree` Actually Works in Claude Code

**Date:** 2026-03-21
**Researcher:** Research Agent
**Session:** Phase 5 deep-dive
**Status:** Complete

---

## 1. What the Documentation Says

### 1.1 Agent Tool Definition (Claude Code System Prompt)

The Agent tool's `isolation` parameter is defined as:

> **isolation** (enum, optional): `["worktree"]`
> Isolation mode. `"worktree"` creates a temporary git worktree so the agent works on an isolated copy of the repo.

Usage notes in the same system prompt state (verbatim):

> You can optionally set `isolation: "worktree"` to run the agent in a temporary git worktree, giving it an isolated copy of the repository. The worktree is automatically cleaned up if the agent makes no changes; if changes are made, the worktree path and branch are returned in the result.

Key claims from the documentation:
1. It creates a **temporary git worktree** (not just process isolation)
2. It gives the agent an **isolated copy of the repository**
3. Auto-cleanup: **no changes → worktree removed**; **changes → worktree path and branch returned in result**

### 1.2 Claude Code Binary (v2.1.81) — Implementation Evidence

The Python Engineer agent extracted implementation details from the Claude Code binary (`/Users/mac/.local/share/claude/versions/2.1.81`, 193MB Mach-O arm64):

**Zod schema definition:**
```
isolation: enum? ["worktree"] - 'Isolation mode. "worktree" creates a temporary
                                git worktree so the agent works on an isolated copy of the repo.'
```

**System prompt injection when agent runs in worktree:**
> This is a git worktree -- an isolated copy of the repository. Run all commands from this directory. Do NOT `cd` to the original repository root.

**Worktree creation logic (minified JS from binary):**
```javascript
if (E === "worktree") {
    let A_ = `agent-${t.slice(0,8)}`;
    T_ = await gn_(A_);  // creates the worktree
}
```

**Worktree cleanup logic (minified JS from binary):**
```javascript
Y_ = async () => {
    if (H_) {  // headCommit exists
        if (!await fdq(A_, H_))  // check if changes were made
            // No changes: clean up worktree
            return await Tq_(A_, G_, l), /* clear metadata */, {};
    }
    // Changes exist: keep worktree, return info
    return { worktreePath: A_, worktreeBranch: G_ };
};
```

**Conclusion from binary:** Claude Code **does** create real git worktrees via `git worktree add`. The cleanup function checks whether the HEAD commit changed; if no changes, it removes the worktree; if changes exist, it returns `{ worktreePath, worktreeBranch }` to the caller.

### 1.3 PM_INSTRUCTIONS.md (Lines 142-148)

```
### EnterWorktree vs. isolation: "worktree"

These are different and complementary tools:
- **`EnterWorktree` tool**: The PM itself enters a worktree (user-requested,
  for PM's own isolated work environment)
- **`isolation: "worktree"` on Agent tool**: A subagent runs in its own
  isolated worktree (for parallel agent work without file conflicts)

Use `EnterWorktree` only when the user explicitly asks the PM to work in a
worktree. Use `isolation: "worktree"` on Agent calls when spawning parallel
agents that need isolated file access.
```

### 1.4 PM_INSTRUCTIONS.md — Merge Protocol (Lines 1207-1258)

The PM instructions include a detailed merge protocol that assumes:
- Agents create commits on separate branches in their worktrees
- PM delegates merge of each branch back to the main branch
- Worktrees persist after agent completion and must be manually cleaned up
- 8-11 git commands are needed for the merge sequence

### 1.5 BASE_AGENT.md (Lines 148-163)

```
Request worktree isolation via the `isolation` parameter on the Agent tool call.

Use `isolation: "worktree"` when:
- Multiple agents will write to the same files simultaneously (prevents conflicts)
- Running truly parallel work that modifies the codebase
- Each agent needs a clean, independent working state
```

---

## 2. What Session 1 Showed

### 2.1 Agent Tool Calls

Session 1 (`f2a8e7f9-48dd-4596-8f50-79fbfe609e5c`) spawned two agents at L37-L38:

| Agent | `isolation` | `run_in_background` | `team_name` | Scope |
|-------|------------|---------------------|-------------|-------|
| cli-logger | `worktree` | `true` | `parallel-logging` | `src/claude_mpm/cli/` only |
| hook-verbose | `worktree` | `true` | `parallel-logging` | `src/claude_mpm/hooks/claude_hooks/` only |

Both calls included `isolation: "worktree"` explicitly in their input parameters.

### 2.2 What the PM Found After Agents Completed

After both agents completed (L60), the PM attempted the merge protocol:

| Line | Command | Result |
|------|---------|--------|
| L61 | `git worktree list` | Only main worktree exists |
| L66 | `git branch -a \| grep agent/cli-logger/hook-verbose` | No matching branches |
| L71 | `git branch --sort=-committerdate` | Only pre-existing branches |
| L76 | `git log --oneline -10` | No new commits from engineers |
| L87 | `git reflog` | No engineer commits visible |
| L95 | `ls /Users/mac/workspace/ \| grep claude-mpm` | No worktree directories found |
| L105 | `find ... -name ".git"` | No recently modified repos |
| **L113** | **`git status && git diff --stat HEAD`** | **6 files modified, unstaged** |

### 2.3 The PM's Conclusion (L118)

> "Both agents wrote to the working tree directly -- no branch conflicts since they touched completely separate files."

### 2.4 TeamDelete Result (L150)

> "Cleaned up directories and worktrees for team 'parallel-logging'"

This message suggests the infrastructure **believed** worktrees existed (or at minimum, that cleanup was performed).

### 2.5 PM's Final Summary (L154)

> "2 engineers ran in parallel in isolated worktrees"

This statement **contradicts** the evidence the PM itself gathered. The PM found no worktrees, no branches, and no commits — only unstaged changes in the parent working tree.

---

## 3. EnterWorktree vs. `isolation: "worktree"`

Per PM_INSTRUCTIONS.md lines 142-148, these are explicitly documented as **different and complementary** mechanisms:

| Aspect | `EnterWorktree` tool | `isolation: "worktree"` on Agent |
|--------|---------------------|----------------------------------|
| **Who uses it** | The PM itself | A spawned subagent |
| **When to use** | User explicitly requests PM work in worktree | Parallel agents that need file isolation |
| **Mechanism** | PM enters an existing or new worktree | Agent spawned in a temporary worktree |
| **Lifecycle** | PM controls via `ExitWorktree` (keep/remove) | Automatic: cleanup on no changes, persist on changes |
| **Available tools** | `EnterWorktree`, `ExitWorktree` (PM-level) | Not available to agents — `isolation` is on Agent call |

**They are NOT the same mechanism.** `EnterWorktree`/`ExitWorktree` are PM-level tools for the PM's own workspace. `isolation: "worktree"` is infrastructure-level — Claude Code creates the worktree before the agent starts and manages cleanup after the agent finishes.

---

## 4. The Likely Truth

### 4.1 What We Know for Certain

1. **Claude Code DOES create real git worktrees** when `isolation: "worktree"` is specified. This is confirmed by:
   - The Agent tool documentation explicitly stating "creates a temporary git worktree"
   - The system prompt injection telling agents "This is a git worktree"
   - The binary implementation showing `git worktree add` equivalent code
   - The cleanup function that checks for changes and returns `{ worktreePath, worktreeBranch }`

2. **In Session 1, no worktrees were visible after agents completed.** The PM ran `git worktree list` at L61 and found only the main worktree. Both agents had already completed by this point.

3. **Changes appeared as unstaged modifications in the parent working tree.** 6 files were modified, exactly matching what both agents were supposed to produce.

4. **TeamDelete claimed to clean up "directories and worktrees."** This suggests the infrastructure tracked worktree state even though `git worktree list` showed none.

### 4.2 The Most Plausible Explanation

The evidence points to the following lifecycle:

```
Agent spawned with isolation: "worktree"
    │
    ▼
Claude Code creates git worktree (agent-XXXXXXXX branch)
Agent runs in worktree directory
Agent makes file changes (may or may not commit)
    │
    ▼
Agent completes (background task finishes)
    │
    ▼
Claude Code runs cleanup function:
    ├── If agent committed changes → return { worktreePath, worktreeBranch }
    │   (worktree persists, PM expected to merge)
    │
    └── If agent did NOT commit (only unstaged changes) →
        Cleanup sees HEAD unchanged → removes worktree
        Unstaged changes... ???
```

**The critical question is what happens to unstaged changes when the worktree is removed.** Standard `git worktree remove` would discard them. Yet in Session 1, the changes appeared in the parent working tree. This suggests one of:

**Hypothesis A — Changes were applied to parent before cleanup:**
Claude Code's Agent tool wrapper may copy unstaged changes from the worktree back to the parent working tree before removing the worktree. This would explain why changes appear as unstaged modifications in the parent.

**Hypothesis B — Agents committed, but worktrees were still cleaned up:**
The agents may have committed their changes in the worktree. The cleanup function returned `{ worktreePath, worktreeBranch }`, but some other part of the infrastructure (perhaps `run_in_background` completion handling or Agent Teams' team management) applied those commits to the parent as unstaged changes and cleaned up the worktree. This would make the "worktree path and branch returned in result" behavior a transient internal state rather than something the PM sees.

**Hypothesis C — Agent Teams overrides standard worktree lifecycle:**
When agents are spawned with a `team_name`, the Agent Teams infrastructure may manage worktree lifecycle differently than standalone `isolation: "worktree"` agents. Team-managed agents may have their changes applied back to the parent tree as part of team coordination, making the standard "worktree persists with changes" behavior inapplicable.

### 4.3 Confidence Assessment

| Claim | Confidence | Evidence |
|-------|-----------|----------|
| `isolation: worktree` creates real git worktrees | **HIGH** | Binary code, documentation, system prompt injection |
| Worktrees existed during agent execution in Session 1 | **MEDIUM** | TeamDelete cleanup message; documentation says they're created |
| Worktrees were gone before PM could observe them | **HIGH** | `git worktree list` at L61 showed only main; PM found no branches |
| Changes were applied to parent as unstaged modifications | **HIGH** | `git status` at L113 showed exactly the expected 6 files |
| The PM_INSTRUCTIONS.md merge protocol is based on wrong assumptions | **HIGH** | The protocol assumes worktrees and branches persist; they didn't |

---

## 5. Implications for PM Instructions

### 5.1 The Merge Protocol Is Wrong (or Incomplete)

PM_INSTRUCTIONS.md lines 1207-1258 describe a merge protocol that assumes:
- Worktree branches persist after agent completion
- PM delegates `git merge --no-commit <branch>` for each agent
- PM runs `git worktree list` to verify cleanup

**In practice (Session 1):** No branches existed. No worktrees existed. Changes appeared as unstaged modifications. There was nothing to merge. The PM spent 10+ exploratory git commands discovering this.

### 5.2 What Needs to Change

**Option 1: Fix the infrastructure to match the documentation.**
If `isolation: worktree` is supposed to leave worktrees with branches for the PM to merge, then the Agent Teams or background agent mechanism needs to stop applying changes back to the parent. The merge protocol would then work as documented.

**Option 2: Fix the documentation to match the infrastructure.**
If the current behavior (changes applied to parent as unstaged modifications) is intentional, then PM_INSTRUCTIONS.md needs:

```
### Post-Agent Worktree Integration

After agents with `isolation: worktree` complete:

1. Run `git worktree list` to check if worktree branches persist
2. IF branches exist:
   a. Delegate merge to Version Control agent (8-11 commands)
   b. Clean up worktrees after merge
3. IF no branches exist (changes in parent working tree):
   a. Run `git status` to verify expected changes are present
   b. Run tests to verify integration
   c. Stage and commit the changes
4. EITHER WAY: Verify all expected files are modified
```

**Option 3: Add a post-completion check step.**
Rather than assuming one behavior, teach the PM to check and adapt:

```
After parallel agents with isolation: worktree complete:
1. `git worktree list` — Do agent worktrees still exist?
2. `git branch --sort=-committerdate | head -10` — Were branches created?
3. `git status` — Are there unstaged changes in the parent tree?
4. Based on what you find, either merge branches OR verify working tree changes
```

### 5.3 The Session 1 PM Behavior Was Actually Correct

Despite the merge protocol not matching reality, the PM in Session 1 behaved well:
- Planned to follow the merge protocol
- Discovered the actual state through exploration
- Adapted gracefully (verified changes, ran tests, reported success)
- Did NOT panic or error out

The problem was not PM behavior but **PM efficiency** — it took 10+ exploratory git commands to discover what a single `git status` would have revealed. Better instructions would have the PM check `git status` early.

---

## 6. Open Questions

### 6.1 Questions That Require Claude Code Source Access

1. **Does `run_in_background: true` change worktree lifecycle?**
   Does the background completion handler apply changes to the parent tree? Would a foreground (synchronous) agent leave its worktree intact?

2. **Does Agent Teams (`team_name`) change worktree lifecycle?**
   Does the team infrastructure manage worktrees differently than standalone agents?

3. **What does the Agent tool result actually contain?**
   The documentation says "worktree path and branch are returned in the result." Session 1's JSONL was not granular enough to confirm whether this information was in the tool results. We need to examine the raw tool_result content for Agent calls.

4. **Does `cwd` parameter interact with `isolation`?**
   The binary shows `cwd` is defined in the internal schema but `.omit({cwd: true})` removes it from the exposed API. The schema notes `cwd` is "mutually exclusive with isolation: 'worktree'."

### 6.2 Questions Answerable by Experiment

5. **Does a synchronous (non-background) agent with `isolation: worktree` leave its worktree intact?**
   Test: Spawn a single agent with `isolation: worktree` (no `run_in_background`), have it make a change and commit, then check `git worktree list`.

6. **Does a background agent WITHOUT `team_name` behave differently?**
   Test: Spawn agents with `isolation: worktree` + `run_in_background: true` but NO `team_name`. Check if worktrees persist.

7. **Does the agent need to commit for worktrees to persist?**
   Test: Have an agent make changes but NOT commit them in the worktree. Does the cleanup function remove the worktree (HEAD unchanged) and lose the changes?

### 6.3 Questions for PM Instruction Design

8. **Should the PM always check `git status` first (before `git worktree list`)?**
   In Session 1, `git status` at L113 was the command that revealed the actual state. Making this the first post-completion check would save 10+ wasted commands.

9. **Should the PM commit engineer work automatically?**
   Session 1 left changes as unstaged modifications, which were later stashed (and potentially lost). Should the PM create a commit as a standard final step?

10. **Should the merge protocol be conditional or removed?**
    If worktrees never persist in practice (due to Agent Teams or background execution), the merge protocol is dead code in the instructions. It should either be made conditional or replaced with a working-tree verification protocol.

---

## 7. Summary of Key Findings

| Finding | Source | Implication |
|---------|--------|-------------|
| `isolation: worktree` creates real git worktrees | Binary code + docs | The mechanism is not "fake" or process-only |
| Worktrees are transient — gone before PM can observe | Session 1 evidence | PM cannot rely on worktrees persisting |
| Changes appear as unstaged modifications in parent tree | Session 1 L113 | No merge needed; verify + commit instead |
| PM_INSTRUCTIONS.md merge protocol assumes persistent worktrees | Lines 1207-1258 | Protocol does not match observed behavior |
| EnterWorktree and isolation: worktree are distinct mechanisms | PM_INSTRUCTIONS.md L142-148 | Correct — no confusion here |
| PM adapted correctly despite wrong instructions | Session 1 L61-L118 | PM behavior was resilient but inefficient |
| TeamDelete claimed "Cleaned up worktrees" | Session 1 L150 | Infrastructure tracked worktree state internally |

**Bottom line:** `isolation: worktree` works at the infrastructure level (real git worktrees are created), but by the time the PM receives agent completion notifications, the worktrees have already been resolved — changes applied to the parent working tree, worktrees removed. The PM_INSTRUCTIONS.md merge protocol is based on the assumption that worktrees persist, which does not match observed behavior. The instructions need to be updated to reflect the actual post-completion state: unstaged changes in the parent tree that need verification and committing.
