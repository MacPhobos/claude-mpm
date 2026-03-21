# Gate B: Manual Verification Scenarios

**Date:** 2026-03-21
**Branch:** mpm-teams
**Prerequisite:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set in environment
**Estimated time:** 3-5 sessions, ~2-4 hours total
**Project:** Run in `claude-mpm-fork` (this repo) — the PM has real code to work with

---

## Overview

Gate B validates that the PM follows Phase 2 orchestration instructions in live Claude
Code sessions. Each scenario below targets one or more checklist items. The operator
presents the prompt, observes PM behavior, and records evidence.

### Gate B Checklist (all 6 must be observed at least once)

| # | Behavior | Minimum Evidence |
|---|----------|------------------|
| B1 | PM spawns 2+ Engineers with `isolation: "worktree"` | Agent tool call with `subagent_type: "engineer"` and `isolation: "worktree"` |
| B2 | PM delegates merge to Version Control / Local Ops agent | Agent tool call to VC/Ops agent with merge instructions |
| B3 | PM runs `make test` after merge (single command, not multi-step) | Single Bash tool call with `make test` or `uv run pytest` |
| B4 | PM sequences Research before Engineer (no mixing in same phase) | Research teammates complete and report BEFORE engineer spawning |
| B5 | PM delegates worktree cleanup (not running 4+ git commands) | Agent tool call to VC/Ops with cleanup instructions |
| B6 | PM does NOT spawn team for sub-15-minute task | PM uses single agent delegation (not Agent Teams) |

---

## Session 1: All-Engineer Parallel (B1, B2, B3, B5)

**Target behaviors:** Engineer spawning with worktree isolation, merge delegation,
post-merge testing, worktree cleanup.

**This is the most important session — it covers 4 of 6 checklist items.**

### Setup

Ensure the branch is clean:
```bash
git stash  # if needed
git status  # should show clean working tree
```

### Prompt

> Add structured logging to the CLI commands in `src/claude_mpm/cli/` and independently
> add a `--verbose` flag to the hook handler in `src/claude_mpm/hooks/claude_hooks/hook_handler.py`.
> These are independent subsystems with no shared code. Use Agent Teams to parallelize.

### What to Observe

**Phase 1 — Decomposition & Spawning (B1)**

The PM should:
- Identify the two independent subsystems (CLI, hooks)
- Explain the decomposition rationale (<20% file overlap)
- Spawn 2 Engineers in a **single message** with multiple Agent tool calls
- Each Agent call should include:
  - `subagent_type: "engineer"` (or a specific engineer type)
  - `isolation: "worktree"` ← **CRITICAL: this must be present**
  - `team_name`: some descriptive name
  - `prompt`: explicit file scope ("Modify ONLY files in src/claude_mpm/cli/")

✅ **B1 PASS if:** Both Agent calls include `isolation: "worktree"`
❌ **B1 FAIL if:** Engineers spawned without worktree isolation, or spawned sequentially

**Evidence to capture:** Screenshot or copy of the Agent tool calls showing `isolation: "worktree"` parameter.

**Phase 2 — Merge Delegation (B2)**

After both engineers report completion, the PM should:
- NOT run git merge commands directly (that would be 4+ bash commands)
- Delegate to a Version Control or Local Ops agent with merge instructions
- The delegation should include branch names from the worktrees

✅ **B2 PASS if:** PM spawns/delegates to VC/Ops agent for merge
❌ **B2 FAIL if:** PM runs `git merge` directly via Bash tool

**Evidence to capture:** The Agent/Task tool call to the merge agent.

**Phase 3 — Post-Merge Testing (B3)**

After merge agent reports success:
- PM should run `make test` (or `uv run pytest`) as a single Bash command
- Should NOT delegate this to another agent (PM is permitted to run single test commands)
- Bash timeout should be 300000 (5 minutes)

✅ **B3 PASS if:** PM runs a single test command directly
❌ **B3 FAIL if:** PM delegates testing to another agent or skips it

**Evidence to capture:** The Bash tool call with the test command.

**Phase 4 — Worktree Cleanup (B5)**

After testing:
- PM should delegate cleanup to VC/Ops agent (same one that merged)
- Should NOT run `git worktree remove` commands directly

✅ **B5 PASS if:** PM delegates cleanup to an agent
❌ **B5 FAIL if:** PM runs 4+ git commands to clean up worktrees

**Evidence to capture:** The cleanup delegation call.

### Fallback Scenarios

If the PM does NOT use Agent Teams (possible — it may judge the task too small):
- Try rephrasing: "This is a large refactoring. Use your Agent Teams capability to
  parallelize with worktree isolation."
- If it still refuses, note this as an observation and try with a larger-scope prompt.

If engineers fail or the merge has conflicts:
- This is actually useful — observe recovery behavior. Does the PM follow the recovery
  protocol? Does it escalate conflicts to the user?

---

## Session 2: Research-then-Engineer Pipeline (B4)

**Target behavior:** PM sequences phases — Research completes before Engineering starts.

### Prompt

> I need to improve error handling across this codebase. First, research the current
> error handling patterns in `src/claude_mpm/hooks/` and `src/claude_mpm/cli/` —
> investigate independently in parallel. Then, based on what you find, have engineers
> implement consistent error handling in both subsystems.

### What to Observe

**Phase 1 — Research Spawning**

The PM should:
- Decompose into 2 independent research questions (hooks error handling, CLI error handling)
- Spawn 2 Research teammates (may or may not use Agent Teams)
- Wait for BOTH research results before proceeding

**Phase 2 — Research Synthesis**

The PM should:
- Synthesize findings from both researchers
- Present findings to formulate engineering tasks

**Phase 3 — Engineer Spawning (B4)**

The PM should:
- Spawn Engineers ONLY AFTER research is complete
- Include research findings as context in the engineer prompts
- NOT mix Research and Engineer in the same parallel phase

✅ **B4 PASS if:** Research teammates finish and report BEFORE any Engineer is spawned
❌ **B4 FAIL if:** Research and Engineer spawned simultaneously, or Engineer spawned
   before research results are available

**Evidence to capture:** Timestamps or sequence showing research completion before
engineering spawn. Look at the conversation flow — research results should appear
in the chat before engineer Agent tool calls.

### Note on Pipeline Realism

The PM may decide this task is better handled sequentially (one research agent, then
one engineer). That's a legitimate PM decision. If so:
- Note the PM's reasoning
- Try the prompt from Session 4 (which is more clearly pipeline-shaped)
- B4 can still pass if the PM explicitly explains why it chose sequential over parallel

---

## Session 3: Anti-Team — Sub-Threshold Task (B6)

**Target behavior:** PM does NOT spawn a team for a trivial task.

### Prompt

> Add a return type annotation `-> dict` to the `score_response` function in
> `tests/manual/agent_teams_battery/scoring/compliance_scorer.py`.

### What to Observe

The PM should:
- Recognize this as a trivial single-file edit
- Handle it with a single agent delegation (or directly per PM cost-efficiency rules)
- NOT spawn a team, NOT use `team_name` parameter, NOT use Agent Teams

✅ **B6 PASS if:** PM handles with single agent or direct edit (no team spawning)
❌ **B6 FAIL if:** PM spawns Agent Teams for this 1-line change

**Evidence to capture:** The PM's delegation decision — should be a simple Agent call
without `team_name`, or a direct Edit tool call.

### If the PM Spawns a Team Anyway

This would be a compliance failure. Note the PM's reasoning. The PM instructions
explicitly say: "Never use teams for tasks a single Engineer completes in < 15 minutes."

### Bonus: Try a Medium Task

After the trivial task, try a medium task that's borderline:

> Rename the `_log` function to `_debug_log` in `hook_handler.py` and update all
> call sites across `event_handlers.py`. This is a single-subsystem rename.

This should also NOT spawn a team (single subsystem, sequential dependency between
the rename and call site updates). The PM should use a single engineer.

---

## Session 4: Full Pipeline — Research → Engineer → QA (B4, and revisit B1-B3)

**Target behavior:** 3-phase pipeline with correct sequencing.

**Only needed if Session 2 did not clearly demonstrate B4, or if you want additional
B1/B2/B3 evidence.**

### Prompt

> I want to add input validation to all CLI commands. Phase 1: Research what inputs
> each CLI command accepts and what validation is currently missing — investigate
> `src/claude_mpm/cli/` commands in parallel. Phase 2: Based on findings, have
> engineers add validation to each command independently. Phase 3: After engineering
> work is merged, have QA run the test suite and verify the validation works.

### What to Observe

1. **Research phase** spawns (parallel research teammates)
2. **Synthesis** — PM summarizes research findings
3. **Engineer phase** spawns AFTER research (B4) with worktree isolation (B1)
4. **Merge** delegation to VC agent (B2)
5. **Test** — PM runs `make test` (B3)
6. **QA phase** spawns AFTER merge — on merged code (not in-flight code)

This session can validate B1, B2, B3, B4 if earlier sessions were inconclusive.

---

## Session 5 (Optional): Recovery & Edge Cases

**Target behavior:** PM handles failures gracefully.

**Only needed if you want to observe recovery behavior.**

### Prompt A: Provoke Merge Conflict

> Two engineers should independently modify `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py`.
> Engineer A: add a docstring to the `inject_context` method.
> Engineer B: rename the `_ROLE_ADDENDA` variable to `ROLE_ADDENDA_MAP`.
> Both touch the same file — this will likely conflict.

**Observe:** Does the PM detect the overlap risk? Does it refuse (correct per anti-patterns:
>20% overlap)? If it proceeds and merge conflicts, does it escalate to the user?

### Prompt B: Provoke Team Refusal (Sequential Dependency)

> First update the `TEAMMATE_PROTOCOL_BASE` constant in `teammate_context_injector.py`,
> then update all tests in `test_teammate_context_injector.py` to match the new constant.
> The test updates depend on the constant change.

**Observe:** The PM should recognize the sequential dependency and refuse to parallelize.
It should use a single engineer handling both changes in sequence.

---

## How to Observe & Collect Evidence

### Where Session Logs Live

Every Claude Code session is recorded as a JSONL file:

```
~/.claude/projects/-Users-mac-workspace-claude-mpm-fork/<session-id>.jsonl
```

Each file contains every message, tool call, and tool result from the session. Tool
calls include the full `input` parameters — so `isolation: "worktree"`, `team_name`,
`subagent_type`, and the complete `prompt` are all preserved.

### Method 1: Automated Evidence Extraction (Recommended)

After completing a session, run the extraction script:

```bash
# List recent sessions
python docs-local/mpm-agent-teams/08-phase-4-manual-verification/extract_gate_b_evidence.py --list

# Extract evidence from the latest session
python docs-local/mpm-agent-teams/08-phase-4-manual-verification/extract_gate_b_evidence.py --latest

# Extract with full tool call details
python docs-local/mpm-agent-teams/08-phase-4-manual-verification/extract_gate_b_evidence.py --latest --verbose

# Extract from a specific session
python docs-local/mpm-agent-teams/08-phase-4-manual-verification/extract_gate_b_evidence.py <session-id>
```

The script automatically:
- Parses the session JSONL
- Finds all Agent tool calls with `team_name` (Agent Teams usage)
- Checks for `isolation: "worktree"` on engineer spawns (B1)
- Detects merge delegation to VC/Ops agents (B2)
- Finds `make test` / `pytest` Bash calls (B3)
- Verifies Research-before-Engineer sequencing (B4)
- Detects cleanup delegation (B5)
- Flags sessions with no team spawning (B6)

**Example output:**

```
======================================================================
GATE B EVIDENCE EXTRACTION REPORT
======================================================================
Session: abc12345-...
Total tool calls: 47
Agent calls: 12 (4 with team_name)
Bash calls: 8

--- Agent Teams Calls ---
  Line 234: Python Engineer | team=refactor-team | isolation=worktree | Implement CLI logging
  Line 235: Python Engineer | team=refactor-team | isolation=worktree | Add verbose flag
  Line 890: Version Control | team=none | isolation=none | Merge worktree branches
  Line 1102: Version Control | team=none | isolation=none | Cleanup worktrees

--- Gate B Checklist ---
  ✅ B1: Engineers spawned with isolation: worktree — PASS
       Line 234: Agent(subagent_type=python engineer, isolation=worktree, team_name=refactor-team)
       Line 235: Agent(subagent_type=python engineer, isolation=worktree, team_name=refactor-team)
  ✅ B2: Merge delegated to VC/Ops agent — PASS
       Line 890: Agent(subagent_type=version control) — merge delegation
  ✅ B3: PM ran make test directly (single command) — PASS
       Line 1050: Bash(command=make test)
  ❌ B4: Research completed before engineering started — FAIL
  ✅ B5: Worktree cleanup delegated — PASS
       Line 1102: Agent(subagent_type=version control) — cleanup delegation
  ❌ B6: Team NOT spawned for trivial task — FAIL

--- Result: 4/6 checklist items passed ---
⚠️  Missing: B4, B6 — run additional sessions
======================================================================
```

### Method 2: Live Terminal Observation

While the session runs, Claude Code renders each tool call in a formatted box:

```
╭─ Agent ──────────────────────────────────────────────╮
│ Description: Implement CLI logging                    │
│ Subagent type: Python Engineer                        │
│ Model: opus                                           │
│ Team: cli-hooks-refactor                              │
│ Isolation: worktree                                   │
│ Prompt: Modify ONLY files in src/claude_mpm/cli/...   │
╰──────────────────────────────────────────────────────╯
```

Look for:
- **`Team:`** field present → Agent Teams is being used
- **`Isolation: worktree`** → B1 (engineer worktree isolation)
- Agent call to Version Control with merge instructions → B2
- Bash call with `make test` → B3
- Research agents complete before engineer agents appear → B4
- Agent call to Version Control with cleanup instructions → B5
- No `Team:` field for trivial tasks → B6

### Method 3: Record Full Session

For archival purposes, wrap the session in `script`:

```bash
script -q session1_gate_b.log
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
# ... run the session ...
exit  # stops recording
```

---

## Recording Results

For each session, record:

```markdown
### Session N: [Title]

**Date/time:**
**Session ID:** [from `--list` output or session file name]
**Model:** (sonnet/opus)
**Agent Teams env:** CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

**Prompt given:** [exact prompt]

**PM behavior observed:**
- [What the PM decided to do]
- [How it decomposed the task]

**Extraction script output:**
[Paste the output of: python extract_gate_b_evidence.py <session-id>]

**Checklist items verified:**
- [ ] B1: Engineers spawned with isolation: "worktree"
- [ ] B2: Merge delegated to VC/Ops agent
- [ ] B3: PM ran make test directly (single command)
- [ ] B4: Research completed before engineering started
- [ ] B5: Cleanup delegated to VC/Ops agent
- [ ] B6: Team NOT spawned for trivial task

**Unexpected behavior:**
[Anything the PM did that wasn't expected — positive or negative]
```

---

## Workflow: Running a Gate B Session

**Step-by-step for each session:**

1. **Ensure prerequisites:**
   ```bash
   cd /Users/mac/workspace/claude-mpm-fork
   git checkout mpm-teams
   git stash  # clean working tree
   export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
   ```

2. **Start Claude Code:**
   ```bash
   claude
   ```

3. **Present the prompt** from the session description below

4. **Watch the terminal** — tool call boxes show parameters in real time

5. **After session completes**, note the session ID:
   ```bash
   python docs-local/mpm-agent-teams/08-phase-4-manual-verification/extract_gate_b_evidence.py --list
   # The most recent session is your Gate B session
   ```

6. **Extract evidence:**
   ```bash
   python docs-local/mpm-agent-teams/08-phase-4-manual-verification/extract_gate_b_evidence.py --latest --verbose
   ```

7. **Copy the output** into the recording template above

8. **Update gate results** in `07-phase-3-verificaton-plan/03_gate_results.md`

---

## Completion Criteria

Gate B passes when:

1. **All 6 checklist items observed at least once** across sessions 1-5
2. **Evidence documented** for each item (extraction script output or transcript)
3. **No critical anti-pattern violations** (e.g., PM mixing phases, running 10+ git
   commands directly, spawning 4+ engineers)

Gate B results should be appended to `07-phase-3-verificaton-plan/03_gate_results.md`
by filling in the Gate B checklist table with session IDs and evidence.

---

## Quick Reference: Session → Checklist Mapping

| Session | Primary Behaviors | Estimated Time | Required? |
|---------|-------------------|---------------|-----------|
| **Session 1** | B1, B2, B3, B5 | 30-60 min | YES — covers 4 of 6 |
| **Session 2** | B4 | 20-40 min | YES — covers pipeline sequencing |
| **Session 3** | B6 | 10-15 min | YES — covers anti-team |
| **Session 4** | B1-B4 (backup) | 30-60 min | Only if sessions 1-2 inconclusive |
| **Session 5** | Recovery, edge cases | 20-30 min | Optional — for confidence |

**Minimum required: Sessions 1, 2, and 3 (60-115 minutes, covers all 6 items)**
