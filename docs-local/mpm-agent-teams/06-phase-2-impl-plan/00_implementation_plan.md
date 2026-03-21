# Phase 2 Implementation Plan: Parallel Engineering & Mixed Teams

**Issue:** #290
**Branch:** mpm-teams
**Date:** 2026-03-20
**Recommendation:** GO
**Estimated Effort:** 3-5 days (~70% instruction text, ~30% Python code)
**Prerequisite:** Phase 1.5 checkpoint gate passes (compliance CI lower bound > 0.70)

---

## 1. Executive Summary

Phase 2 extends MPM Agent Teams from parallel Research (read-only, conflict-free) to parallel Engineering (file writes, merge conflicts, integration testing) and multi-phase pipelines (Research-then-Engineer, Engineer-then-QA). The key finding across all research is that this is primarily an INSTRUCTION problem, not a CODE problem. Git worktree mechanics already work. The merge workflow is PM-directed. The code change is a ~30-line refactor of `teammate_context_injector.py` to route role-specific protocol addenda. The bulk of the work is ~68 lines of new PM behavioral instructions covering compositions, merge delegation, recovery, and cleanup. PM behavioral instructions cannot be unit-tested; validation depends on the compliance battery and live observation.

---

## 2. Scope

### Supported Compositions

| Composition | Use Case (Issue #290) | Roles | Phases | Max Simultaneous |
|---|---|---|---|---|
| **All-Engineer Parallel** | Large Refactoring: multiple engineers on different subsystems | 2-3 Engineers | 1 parallel + merge gate | 3 |
| **Engineer-then-QA Pipeline** | Complex Features: frontend + backend + test coordinating | 2-3 Engineers + 1 QA | 2 (Engineer parallel, then QA sequential) | 3 Engineers, then 1 QA |
| **Research-then-Engineer Pipeline** | Security Audit: research + implementation + verification | 2-3 Research + 2-3 Engineers (+optional QA) | 2-3 sequential | 3 per phase |

**Team size distinction:** Research teams have no size limit (Phase 1.5 finding: "no ceiling -- constrained by decomposition quality"). Engineering teams are capped at 3 per parallel phase due to combinatorial merge complexity.

### Explicitly Excluded Anti-Patterns

| Anti-Pattern | Why Excluded |
|---|---|
| Mixed Research + Engineer in a single parallel phase | Engineer depends on Research findings; must be sequential phases |
| QA running parallel with Engineers | QA must test MERGED code, not in-flight code |
| More than 3 Engineers in a single parallel phase | Merge complexity grows combinatorially; PM context degrades |
| Peer-to-peer coordination via SendMessage | Rule 5 maintained; SendMessage not hookable; deferred to Phase 3 |
| Automated merge conflict resolution | PM escalates conflicts to user; automated resolution deferred to Phase 3 |
| Teams for tasks a single Engineer completes in <15 minutes | Orchestration overhead exceeds parallelism benefit |

---

## 3. Work Packages

### WP-A: TEAMMATE_PROTOCOL Role Extensions (0.5 days)

**File:** `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py`

**Objective:** Refactor the monolithic `TEAMMATE_PROTOCOL` constant into a base protocol plus role-specific addenda (Option C from RQ6). Remove Rule 3 from base. Add Engineer, QA, and Research addendum constants. Add role-routing logic to `inject_context()`.

**Dependencies:** None (can start immediately).

#### 3.1 New Constants

Insert after the current `TEAMMATE_PROTOCOL` constant (line 55). The existing `TEAMMATE_PROTOCOL` is kept as a backward-compatibility alias.

**TEAMMATE_PROTOCOL_BASE** (~330 tokens, 4 rules -- Rule 3 "QA Scope Honesty" removed from base):

```python
TEAMMATE_PROTOCOL_BASE = """\
## MPM Teammate Protocol

You are operating as a teammate in an MPM-managed Agent Teams session. The team lead (PM) assigned you this task. Follow these rules strictly.

### Rule 1: Evidence-Based Completion (CB#3)
When reporting task completion, you MUST include:
- Specific commands you executed and their actual output
- File paths and line numbers of all changes made
- Test results with pass/fail counts (if applicable)
FORBIDDEN phrases: "should work", "appears to be working", "looks correct", "I believe this fixes". Use only verified facts.

### Rule 2: File Change Manifest (CB#4)
Before reporting completion, list ALL files you created, modified, or deleted:
- File path
- Action: created / modified / deleted
- One-line summary of the change
Omit nothing. The team lead will cross-reference against git status.

### Rule 3: Self-Execution (CB#9)
Execute all work yourself using available tools. Never instruct the user or any teammate to run commands on your behalf.

### Rule 4: No Peer Delegation
Do NOT delegate your assigned task to another teammate via SendMessage. Do NOT orchestrate multi-step workflows with other teammates. If you cannot complete your task, report the blocker to the team lead -- do not ask a peer to do it. You have ONE task. Complete it and report results to the team lead."""
```

**TEAMMATE_PROTOCOL_ENGINEER** (~112 tokens):

```python
TEAMMATE_PROTOCOL_ENGINEER = """\
### Engineer Rules
- You MUST state "QA verification has not been performed" when reporting completion. Do NOT claim your work is fully verified.
- Declare intended file scope BEFORE starting work. Do not modify files outside that scope.
- Run linting/formatting checks before reporting completion.
- Include git diff summary (files changed, insertions, deletions) in your completion report.
- You are working in an isolated worktree. Do not reference or modify files in the main working tree."""
```

**TEAMMATE_PROTOCOL_QA** (~108 tokens):

```python
TEAMMATE_PROTOCOL_QA = """\
### QA Rules
- You ARE the QA verification layer. Your evidence must be independent of the Engineer's claims.
- Run tests in a clean state (no uncommitted changes from your own edits).
- Report the full test command AND its complete output, not just pass/fail counts.
- When verifying an Engineer's work, explicitly state which Engineer and which files you are verifying.
- Test against the MERGED code when verifying work from multiple Engineers."""
```

**TEAMMATE_PROTOCOL_RESEARCH** (~46 tokens):

```python
TEAMMATE_PROTOCOL_RESEARCH = """\
### Research Rules
- Do not modify source code files. Your deliverable is analysis, not implementation.
- Cite specific file paths and line numbers for every claim about the codebase."""
```

**_ROLE_ADDENDA mapping:**

```python
_ROLE_ADDENDA = {
    "engineer": TEAMMATE_PROTOCOL_ENGINEER,
    "qa": TEAMMATE_PROTOCOL_QA,
    "qa-agent": TEAMMATE_PROTOCOL_QA,
    "research": TEAMMATE_PROTOCOL_RESEARCH,
    "research-agent": TEAMMATE_PROTOCOL_RESEARCH,
}
```

**Backward-compatibility alias:**

```python
# Backward-compat alias: TEAMMATE_PROTOCOL still importable.
# Phase 2 changed: this now points to the base (Rule 3 removed, renumbered).
TEAMMATE_PROTOCOL = TEAMMATE_PROTOCOL_BASE
```

#### 3.2 Token Budget Table

| Role | Base Tokens | Addendum Tokens | Total | Within 500? | Margin |
|---|---|---|---|---|---|
| Engineer | ~330 | ~112 | ~442 | Yes | 58 |
| QA | ~330 | ~108 | ~438 | Yes | 62 |
| Research | ~330 | ~46 | ~376 | Yes | 124 |
| Unknown/missing | ~330 | 0 | ~330 | Yes | 170 |

#### 3.3 Modified inject_context()

Replace the current `inject_context()` method (lines 119-157) with:

```python
def inject_context(self, tool_input: dict) -> dict:
    """Prepend role-appropriate TEAMMATE_PROTOCOL to the prompt in tool_input.

    Creates a shallow copy of tool_input and modifies the prompt field.
    The original dict is NOT mutated.

    Assembles protocol from TEAMMATE_PROTOCOL_BASE plus the role-specific
    addendum determined by subagent_type. Unknown roles get base only.

    Args:
        tool_input: The Agent tool's input parameters.

    Returns:
        A new dict with the protocol prepended to prompt.
    """
    modified = copy.copy(tool_input)

    team_name = tool_input.get("team_name", "")
    subagent_type = tool_input.get("subagent_type", "unknown")

    # Build role-appropriate protocol
    protocol = TEAMMATE_PROTOCOL_BASE
    addendum = _ROLE_ADDENDA.get(subagent_type.lower(), "")
    if addendum:
        protocol += "\n\n" + addendum

    # Log injection details
    _log(
        f"TeammateContextInjector: Injected protocol "
        f"(team_name={team_name}, subagent_type={subagent_type}, "
        f"addendum={'yes' if addendum else 'none'})"
    )

    original_prompt = tool_input.get("prompt") or ""
    modified["prompt"] = protocol + "\n\n---\n\n" + original_prompt
    return modified
```

#### 3.4 Lines Removed

Remove the Phase 1 non-research warning log (lines 141-146 of current file). Non-research subagent_type values are now expected, not warnings.

---

### WP-B: PM_INSTRUCTIONS.md Expansion (1 day, depends on WP-A)

**File:** `src/claude_mpm/agents/PM_INSTRUCTIONS.md`

**Objective:** Rename "Agent Teams: Parallel Research" to "Agent Teams". Add compositions, Engineering spawning, merge delegation, recovery, cleanup, and anti-patterns. Keep existing Research rules intact.

**Current section:** Lines 1135-1184 (~50 lines).
**Target section:** ~113 lines total (~68 new lines, ~5 lines modified/removed).

#### 3.5 Exact New/Modified Text

The entire Agent Teams section, showing new content inline. Lines marked `[EXISTING]` are unchanged from Phase 1. Lines marked `[NEW]` are Phase 2 additions. Lines marked `[MODIFIED]` replace Phase 1 text.

```markdown
## Agent Teams                                                    [MODIFIED: was "Agent Teams: Parallel Research"]

When `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is active, you can spawn parallel
teammates for complex tasks. Supported patterns: parallel Research (Phase 1),
parallel Engineering, and multi-phase pipelines.                  [MODIFIED: was Research-only]

### When to Use Teams

Spawn a Research team when ALL conditions are met:                [EXISTING]
- The task decomposes into >= 2 **independent** research questions
- Research questions target **different** subsystems (< 20% file overlap)
- No sequential dependency between questions

Spawn an Engineering team when ALL conditions are met:            [NEW - 4 lines]
- The task involves writing code across >= 2 independent subsystems
- Subsystems have < 20% file overlap (estimate before spawning)
- Each subsystem can be modified independently (no cascading interface changes)
- A single Engineer would take >= 15 minutes (teams have orchestration overhead)

Do NOT use teams when:                                            [EXISTING]
- The task is a single linear investigation
- Research questions depend on each other's results
- Scope is small (< 3 files to examine)
- Agent Teams env var is not set (fall back to `run_in_background`)

### Compositions                                                  [NEW - 15 lines]

| Composition | When | Roles | Phases |
|---|---|---|---|
| All-Engineer Parallel | Refactoring spanning 2-3 independent subsystems | 2-3 Engineers | 1 parallel + merge |
| Engineer-then-QA Pipeline | Feature implementation requiring verification | 2-3 Engineers + 1 QA | Engineer parallel, then QA |
| Research-then-Engineer Pipeline | Investigation-driven implementation | 2-3 Research + 2-3 Engineers | Research parallel, then Engineer parallel |

Selection flow:
- Task involves writing code? No -> Research team (existing pattern).
- Can implementation decompose into 2+ independent subsystems (<20% overlap)? No -> sequential delegation.
- Does task require investigation first? Yes -> Research-then-Engineer Pipeline.
- Does task require verification beyond `make test`? Yes -> Engineer-then-QA Pipeline.
- Otherwise -> All-Engineer Parallel.

### Spawning Protocol                                             [EXISTING header, expanded]

**Research teammates** (existing, unchanged):                     [EXISTING]
1. Decompose into independent research questions
2. Spawn all teammates in a **single message** using the Agent tool
3. Wait for all teammates to report via SendMessage
4. Validate each result (evidence block, file paths, no forbidden phrases)
5. Synthesize findings with attribution

**Engineering teammates:**                                        [NEW - 8 lines]
1. Decompose into independent subsystem tasks with explicit file scope boundaries
2. Spawn all Engineers in a **single message**:
   - `subagent_type`: "engineer"
   - `isolation`: "worktree" (REQUIRED for all parallel Engineers)
   - `prompt`: Include explicit file scope ("Modify ONLY files in <path>")
3. Wait for all Engineers to report completion
4. Validate each result (evidence, file manifest, diff summary, scope respected)
5. Delegate merge to a Version Control or Local Ops agent (see Merge Protocol)
6. Run `make test` directly after merge (timeout: 300000)

**Pipeline teammates:**                                           [NEW - 4 lines]
1. Complete Phase 1 (Research or Engineering) fully before starting Phase 2
2. Synthesize Phase 1 results into Phase 2 task descriptions
3. Spawn Phase 2 teammates with Phase 1 findings as context in the prompt
4. Each phase follows its own spawning protocol above

### Merge Protocol                                                [NEW - 15 lines]

**IMPORTANT:** The merge sequence requires 8-11 git commands, which exceeds the
PM's 2-3 bash command limit (Circuit Breaker #7). The PM MUST delegate merge
operations to a Version Control or Local Ops agent.

PM delegation template for the merge agent:
> Merge the following worktree branches into the current branch in this order:
> 1. `git merge <engineer-A-branch>` (first merge: fast-forward)
> 2. `git merge --no-commit <engineer-B-branch>` -- if clean, `git commit`; if conflict, `git merge --abort` and report which files conflict
> 3. Repeat for each additional branch
> 4. After all merges, run `git worktree list` and report the result
> Report: merge success/failure, any conflicts, list of merged branches.

After the merge agent reports success, PM runs `make test` directly (permitted as
single documented test command). Use Bash timeout: 300000 (5 minutes).

If merge agent reports conflicts: PM escalates to user with conflict details.

### Build Verification (After Merge)                              [NEW - 10 lines]

After merge succeeds and PM runs `make test`:
- All tests pass: proceed to report and cleanup.
- Tests fail with NEW failures: correlate failing tests with each Engineer's
  change scope using `git log --name-only <branch>`. Classify as single-branch
  fault, interaction fault, or pre-existing.
  - Single-branch fault: revert that branch, re-test, report.
  - Interaction fault: spawn a fix-up Engineer with BOTH branches' context.
  - Unattributable: revert all, fall back to sequential execution.
- Do NOT delegate integration testing to a QA agent. PM runs tests directly.
  QA delegation is for complex verification (browser testing, API contracts).

### Recovery Protocol                                             [NEW - 8 lines]

- Teammate timeout/crash with no useful commits: discard worktree, proceed without.
- Teammate produces wrong output: send back ONCE; if retry fails, accept partial.
- Merge conflict: delegate resolution to Version Control agent or escalate to user.
- Integration test failure: see Build Verification above.
- 3 total failures in a team session: ABORT team, fall back to sequential execution.
  Report to user what succeeded and what failed.
- Same-scope fails twice: escalate that scope to user, continue team for other scopes.

### Worktree Cleanup                                              [NEW - 5 lines]

After EVERY team session with worktree-isolated Engineers:
1. Run `git worktree list` to enumerate all worktrees.
2. Merged branches: `git worktree remove <path>` + `git branch -d <branch>`.
3. Failed/discarded branches: `git worktree remove --force <path>` + `git branch -D <branch>`.
4. Verify: `git worktree list` shows only the main worktree.
NEVER leave stale worktrees from a previous team session.

### Anti-Patterns                                                 [EXISTING header, expanded]

- **Never** spawn teams for single-question research              [EXISTING]
- **Never** use teams when subtasks have sequential dependencies  [EXISTING]
- **Never** resolve conflicting teammate findings yourself        [EXISTING]
- **Never** spawn two Engineers on overlapping files without `isolation: "worktree"` [NEW]
- **Never** spawn QA parallel with Engineers (QA tests MERGED code only) [NEW]
- **Never** mix Research + Engineer in the same parallel phase    [NEW]
- **Never** spawn > 3 Engineers in a single parallel phase        [NEW]
- **Never** use teams for tasks a single Engineer completes in < 15 minutes [NEW]

### Fallback                                                      [EXISTING]

If Agent Teams is unavailable (no `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`), use
standard `run_in_background: true` delegation with multiple Agent tool calls.
Same decomposition, same synthesis -- different mechanism, transparent to user.
```

#### 3.6 Line Budget Verification

| Sub-section | New Lines |
|---|---|
| Composition decision table | 15 |
| Engineering spawning protocol | 8 |
| Pipeline spawning protocol | 4 |
| Merge protocol (delegation) | 15 |
| Build verification | 10 |
| Recovery protocol | 8 |
| Worktree cleanup | 5 |
| New anti-patterns | 5 |
| Header/intro modifications | -2 |
| **Total net new lines** | **~68** |
| **Projected section size** | **~113 lines** |

---

### WP-C: Unit Tests (0.5 days, parallel with WP-A)

**File:** `tests/hooks/test_teammate_context_injector.py` (extend existing)

**Dependencies:** WP-A (protocol refactor must exist before tests can validate it).

#### 3.7 New Test Cases (12 tests)

Add a new test class `TestPhase2RoleAddenda` after the existing `TestPreToolUseIntegration` class.

```python
class TestPhase2RoleAddenda:
    """Phase 2: Role-specific protocol addenda tests."""

    def test_engineer_addendum_injected(self):
        """Engineer subagent_type gets base + engineer addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "engineer",
            "prompt": "Refactor the auth module",
            "team_name": "refactor-team",
        }
        result = injector.inject_context(tool_input)
        assert "MPM Teammate Protocol" in result["prompt"]
        assert "Engineer Rules" in result["prompt"]
        assert "QA Rules" not in result["prompt"]
        assert "Research Rules" not in result["prompt"]

    def test_qa_addendum_injected(self):
        """QA subagent_type gets base + QA addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "qa",
            "prompt": "Verify the auth module changes",
            "team_name": "feature-team",
        }
        result = injector.inject_context(tool_input)
        assert "MPM Teammate Protocol" in result["prompt"]
        assert "QA Rules" in result["prompt"]
        assert "Engineer Rules" not in result["prompt"]

    def test_research_addendum_injected(self):
        """Research subagent_type gets base + research addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "research",
            "prompt": "Investigate the auth module",
            "team_name": "research-team",
        }
        result = injector.inject_context(tool_input)
        assert "MPM Teammate Protocol" in result["prompt"]
        assert "Research Rules" in result["prompt"]
        assert "Engineer Rules" not in result["prompt"]
        assert "QA Rules" not in result["prompt"]

    def test_unknown_role_gets_base_only(self):
        """Unknown subagent_type gets base protocol without any addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "ops",
            "prompt": "Deploy the service",
            "team_name": "ops-team",
        }
        result = injector.inject_context(tool_input)
        assert "MPM Teammate Protocol" in result["prompt"]
        assert "Engineer Rules" not in result["prompt"]
        assert "QA Rules" not in result["prompt"]
        assert "Research Rules" not in result["prompt"]

    def test_role_routing_case_insensitive(self):
        """'Engineer' and 'engineer' both route to engineer addendum."""
        injector = TeammateContextInjector(enabled=True)
        for role in ["engineer", "Engineer", "ENGINEER"]:
            tool_input = {
                "subagent_type": role,
                "prompt": "Build it",
                "team_name": "test-team",
            }
            result = injector.inject_context(tool_input)
            assert "Engineer Rules" in result["prompt"], (
                f"Engineer addendum not injected for subagent_type='{role}'"
            )

    def test_backward_compat_alias(self):
        """TEAMMATE_PROTOCOL constant still importable and contains base text."""
        from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
            TEAMMATE_PROTOCOL,
            TEAMMATE_PROTOCOL_BASE,
        )
        assert TEAMMATE_PROTOCOL is TEAMMATE_PROTOCOL_BASE
        assert "MPM Teammate Protocol" in TEAMMATE_PROTOCOL

    def test_token_budget_engineer(self):
        """Base + engineer addendum stays under 2000 chars (~500 tokens)."""
        from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
            TEAMMATE_PROTOCOL_BASE,
            TEAMMATE_PROTOCOL_ENGINEER,
        )
        combined = TEAMMATE_PROTOCOL_BASE + "\n\n" + TEAMMATE_PROTOCOL_ENGINEER
        assert len(combined) < 2000, (
            f"Engineer protocol too long: {len(combined)} chars (max 2000)"
        )

    def test_token_budget_qa(self):
        """Base + QA addendum stays under 2000 chars (~500 tokens)."""
        from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
            TEAMMATE_PROTOCOL_BASE,
            TEAMMATE_PROTOCOL_QA,
        )
        combined = TEAMMATE_PROTOCOL_BASE + "\n\n" + TEAMMATE_PROTOCOL_QA
        assert len(combined) < 2000, (
            f"QA protocol too long: {len(combined)} chars (max 2000)"
        )

    def test_token_budget_research(self):
        """Base + research addendum stays under 2000 chars (~500 tokens)."""
        from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
            TEAMMATE_PROTOCOL_BASE,
            TEAMMATE_PROTOCOL_RESEARCH,
        )
        combined = TEAMMATE_PROTOCOL_BASE + "\n\n" + TEAMMATE_PROTOCOL_RESEARCH
        assert len(combined) < 2000, (
            f"Research protocol too long: {len(combined)} chars (max 2000)"
        )

    def test_base_does_not_contain_qa_scope_rule(self):
        """Rule 3 (QA Scope Honesty) removed from base protocol."""
        from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
            TEAMMATE_PROTOCOL_BASE,
        )
        assert "QA Scope Honesty" not in TEAMMATE_PROTOCOL_BASE
        assert "QA verification has not been performed" not in TEAMMATE_PROTOCOL_BASE

    def test_engineer_contains_qa_not_performed(self):
        """Engineer addendum includes QA-not-performed declaration."""
        from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
            TEAMMATE_PROTOCOL_ENGINEER,
        )
        assert "QA verification has not been performed" in TEAMMATE_PROTOCOL_ENGINEER

    def test_qa_contains_verification_layer(self):
        """QA addendum includes 'you ARE the QA verification layer'."""
        from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
            TEAMMATE_PROTOCOL_QA,
        )
        assert "You ARE the QA verification layer" in TEAMMATE_PROTOCOL_QA
```

**Import updates required at top of test file:**

```python
from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
    TEAMMATE_PROTOCOL,
    TEAMMATE_PROTOCOL_BASE,
    TEAMMATE_PROTOCOL_ENGINEER,
    TEAMMATE_PROTOCOL_QA,
    TEAMMATE_PROTOCOL_RESEARCH,
    TeammateContextInjector,
)
```

**Existing test updates required (devil's advocate amendment):**

- `test_protocol_content_present` (line 187): Replace with 4 role-specific tests:
  - `test_protocol_content_base`: Assert base headings ("Evidence-Based Completion", "File Change Manifest", "Self-Execution", "No Peer Delegation") and assert "QA Scope Honesty" is NOT in base.
  - `test_protocol_content_engineer`: Assert Engineer injection contains base + "Engineer Rules" + "QA verification has not been performed"
  - `test_protocol_content_qa`: Assert QA injection contains base + "QA Rules" + "you ARE the QA verification layer"
  - `test_protocol_content_research`: Assert Research injection contains base + "Research Rules" + "Do not modify source code"

- `test_protocol_matches_source_of_truth` (line 267): Update to check 4-rule base headings (remove "QA Scope Honesty"). Add a companion test `test_qa_scope_in_engineer_addendum` verifying that "QA verification has not been performed" appears in `TEAMMATE_PROTOCOL_ENGINEER`.

**Updated WP-C test count:** 12 new + 5 updated/split = **17 total test changes**

---

### WP-D: Battery Extension (0.5 days, parallel with WP-B)

**Directory:** `tests/manual/agent_teams_battery/scenarios/`

**Objective:** Add scenario files for Engineer, QA, and pipeline compositions.

#### 3.8 New Scenario Files

**`engineer.yaml`** (15 scenarios):

| ID Range | Stratum | Expected Behavior | Tests |
|---|---|---|---|
| eng-01 to eng-05 | engineer-parallel | team_spawn (Engineers) | PM decomposes into 2-3 Engineering tasks, spawns with `isolation: "worktree"` |
| eng-06 to eng-08 | engineer-antipattern | single_agent | PM does NOT spawn team for small tasks (<15 min), overlapping files, or single-subsystem work |
| eng-09 to eng-12 | engineer-merge | team_spawn (Engineers) | PM merge delegation: delegates merge to Version Control agent, runs `make test` after |
| eng-13 to eng-15 | engineer-recovery | team_spawn (Engineers) | PM handles timeout/failure: proceeds without, cleans worktrees, falls back to sequential |

**`qa.yaml`** (10 scenarios):

| ID Range | Stratum | Expected Behavior | Tests |
|---|---|---|---|
| qa-01 to qa-04 | qa-pipeline | team_spawn (Eng+QA) | PM spawns Engineers first, merges, then spawns QA on merged code |
| qa-05 to qa-07 | qa-antipattern | team_spawn (Eng only) | PM does NOT spawn QA parallel with Engineers |
| qa-08 to qa-10 | qa-protocol | team_spawn (QA) | QA teammate provides independent evidence, full output, engineer attribution |

**`pipeline.yaml`** (10 scenarios):

| ID Range | Stratum | Expected Behavior | Tests |
|---|---|---|---|
| pipe-01 to pipe-03 | research-then-eng | team_spawn (Research, then Eng) | PM runs Research phase, synthesizes, then spawns Engineering phase |
| pipe-04 to pipe-06 | eng-then-qa | team_spawn (Eng, then QA) | PM runs Engineering phase, merges, then spawns QA phase |
| pipe-07 to pipe-08 | full-pipeline | team_spawn (Research, Eng, QA) | 3-phase pipeline with phase transitions |
| pipe-09 to pipe-10 | pipeline-antipattern | single_agent or team_spawn (sequential) | PM does NOT mix roles in same parallel phase |

**Scorer update required (devil's advocate amendment):**

Update `tests/manual/agent_teams_battery/scoring/compliance_scorer.py`:
- Add optional `role: str = "research"` parameter to `score_response()`
- Criterion 4 (QA scope declaration) only evaluated when `role == "engineer"`
- QA and Research responses are not penalized for lacking "QA verification has not been performed"
- This is ~5 lines of code change

**Scoring criteria for new role types:**
- Engineer evidence: must include git diff summary, scope declaration
- QA evidence: must include full test command + output, engineer attribution
- Merge delegation: PM must NOT run merge commands directly (delegates to agent)

---

### WP-E: Documentation (0.5 days, after WP-A and WP-B)

**Files to update:**

| File | Change |
|---|---|
| `docs-local/mpm-agent-teams/03-phase-1/02_parallel_research_design.md` | Add note at top: "Phase 2 extends this design to Engineering and Pipeline compositions. See `06-phase-2-impl-plan/00_implementation_plan.md`." |
| `docs-local/mpm-agent-teams/06-phase-2-impl-plan/01_implementation_results.md` | Create after implementation: what was built, test evidence, compliance data, gate status |

---

## 4. File Change Summary

| # | File Path | What Changes | Est. Lines Added | Est. Lines Modified |
|---|---|---|---|---|
| 1 | `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` | Refactor TEAMMATE_PROTOCOL into base + 3 role addenda + `_ROLE_ADDENDA` dict. Modify `inject_context()` for role routing. Remove Phase 1 non-research warning. Add backward-compat alias. | ~45 | ~15 |
| 2 | `src/claude_mpm/agents/PM_INSTRUCTIONS.md` | Rename section. Add compositions, Engineering spawning, merge delegation, build verification, recovery, cleanup, anti-patterns. | ~68 | ~5 |
| 3 | `tests/hooks/test_teammate_context_injector.py` | Add 12 new tests for role-based protocol assembly. Update 2 existing tests. Update imports. | ~120 | ~10 |
| 4 | `tests/manual/agent_teams_battery/scenarios/engineer.yaml` | 15 Engineer team scenarios | ~180 | 0 |
| 5 | `tests/manual/agent_teams_battery/scenarios/qa.yaml` | 10 QA pipeline scenarios | ~120 | 0 |
| 6 | `tests/manual/agent_teams_battery/scenarios/pipeline.yaml` | 10 multi-phase pipeline scenarios | ~120 | 0 |
| 7 | `docs-local/mpm-agent-teams/03-phase-1/02_parallel_research_design.md` | Add Phase 2 cross-reference note | ~3 | 0 |
| 8 | `docs-local/mpm-agent-teams/06-phase-2-impl-plan/01_implementation_results.md` | Post-implementation results document | ~150 | 0 |

**Totals:**

| Category | Lines Added | Lines Modified |
|---|---|---|
| Python code (production) | ~45 | ~15 |
| Python code (test) | ~120 | ~10 |
| Instruction text (PM_INSTRUCTIONS.md) | ~68 | ~5 |
| Battery scenarios (YAML) | ~420 | 0 |
| Documentation (markdown) | ~153 | 0 |
| **Grand total** | **~806** | **~30** |

---

## 5. Testing Strategy

### Fast Tests (`make test`)

| Test File | Existing Tests | New Tests | Total |
|---|---|---|---|
| `tests/hooks/test_teammate_context_injector.py` | 20 (in `TestTeammateContextInjector` + `TestPreToolUseIntegration`) | 12 (in `TestPhase2RoleAddenda`) | 32 |

All 12 new tests are fast, deterministic, no LLM, no network. They exercise the `TeammateContextInjector` class directly with controlled inputs.

**Verification command:**
```bash
cd /Users/mac/workspace/claude-mpm-fork && uv run pytest tests/hooks/test_teammate_context_injector.py -v
```

### Compliance Battery (`make test-agent-teams`)

| Scenario File | Existing Scenarios | New Scenarios | Total |
|---|---|---|---|
| trivial.yaml | ~25 | 0 | ~25 |
| medium.yaml | ~25 | 0 | ~25 |
| complex.yaml | ~25 | 0 | ~25 |
| adversarial.yaml | ~5 | 0 | ~5 |
| engineer.yaml | 0 | 15 | 15 |
| qa.yaml | 0 | 10 | 10 |
| pipeline.yaml | 0 | 10 | 10 |
| **Total** | **~80** | **35** | **~115** |

Battery execution requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and cannot run in CI.

### What Cannot Be Unit-Tested

PM behavioral instructions (WP-B) cannot be unit-tested. The ~68 lines of merge protocol, recovery rules, and composition logic are validated through:
1. Battery scenarios (manual execution, compliance scoring)
2. Live observation during implementation
3. Compliance data accumulated passively during battery runs

---

## 6. Merge Protocol (Detailed Step-by-Step)

This is the workflow the PM follows after all Engineers report completion. The critical point is that **PM delegates merge commands to a Version Control or Local Ops agent** because the 8-11 command sequence exceeds PM's 2-3 bash command limit (Circuit Breaker #7).

### Step 1: Validate All Engineer Results

For each Engineer:
- Evidence block present (commands + output)?
- File manifest complete (every modified file listed)?
- Git diff summary included?
- Scope respected (no files outside declared scope)?
- If validation fails: send back ONCE with specific ask.
- All validations must pass before proceeding.

### Step 2: Delegate Merge to Version Control Agent

PM spawns or delegates to a Version Control / Local Ops agent with this prompt template:

> Merge the following worktree branches into the current branch. Merge them in this exact order:
> 1. Branch `<engineer-A-branch>` -- first merge (should fast-forward)
> 2. Branch `<engineer-B-branch>` -- use `git merge --no-commit`; if clean, commit; if conflict, `git merge --abort` and report which files conflict
> 3. Branch `<engineer-C-branch>` -- same as step 2
> After all merges, run `git worktree list` and report: success/failure, any conflict details, list of branches merged.

### Step 3: Evaluate Merge Result

- Merge agent reports success: proceed to Step 4.
- Merge agent reports conflict: PM escalates to user with conflict file list.

### Step 4: PM Runs Integration Tests

PM executes directly (single documented test command, permitted per cost-efficiency exception):

```
Bash tool: command="cd /Users/mac/workspace/claude-mpm-fork && make test", timeout=300000
```

### Step 5: Evaluate Test Results

- All tests pass: proceed to Step 6.
- Tests fail with pre-existing failures (same as base branch): proceed.
- Tests fail with NEW failures:
  - PM examines test output, identifies failing test files.
  - PM runs `git log --name-only <branch>` per Engineer to get change scopes.
  - PM classifies: single-branch fault, interaction fault, or unattributable.
  - Single-branch fault: delegate revert of that branch to Version Control agent, re-run `make test`.
  - Interaction fault: spawn fix-up Engineer with both branches' context.
  - Unattributable: delegate `git reset --hard <pre-merge-commit>` to Version Control agent, fall back to sequential.

### Step 6: Cleanup

PM delegates to Version Control agent (or runs directly if only 2-3 commands):

```
For each merged branch: git worktree remove <path> && git branch -d <branch>
For each failed branch: git worktree remove --force <path> && git branch -D <branch>
Verify: git worktree list (should show only main worktree)
```

### Step 7: Report

PM reports to user with:
- What was implemented (per-Engineer attribution)
- Test results
- Any branches reverted and why
- Any remaining worktrees (for user review)

---

## 7. Timeline

| Day | Work Package | Deliverable | Verification |
|---|---|---|---|
| 1 | WP-A (protocol refactor) + WP-C (tests, first 6) | `teammate_context_injector.py` refactored with base + 3 role addenda + routing logic. 6 role-assembly tests passing. | `uv run pytest tests/hooks/test_teammate_context_injector.py -v` |
| 2 | WP-B (PM instructions) + WP-C (tests, remaining 6) | PM_INSTRUCTIONS.md expanded with compositions, merge delegation, recovery, cleanup. All 12 new tests passing. | `uv run pytest tests/hooks/test_teammate_context_injector.py -v` + manual review of PM_INSTRUCTIONS.md section |
| 3 | WP-D (battery scenarios) + WP-E (documentation) | 35 new battery scenarios in 3 YAML files. Cross-reference note in Phase 1 design doc. | Scenario YAML lint check. Doc review. |
| 4 | Battery execution + checkpoint gate | `make test-agent-teams` with Phase 2 scenarios. `audit_agent_teams_compliance.py --gate` on combined data. | Gate evaluation output. |
| 5 | Results document + final review | `01_implementation_results.md` written. All fast tests green. PR ready for review. | `make test` full suite. PR created. |

**Critical path:** WP-A (Day 1) -> WP-B (Day 2) -> Battery execution (Day 4) -> Gate evaluation (Day 4)

**Parallelization:**
- Day 1: WP-A and WP-C first 6 tests run in parallel (write tests as code lands)
- Day 2: WP-B and WP-C remaining 6 tests run in parallel
- Day 3: WP-D and WP-E are independent of each other

---

## 8. Checkpoint Gate

### Data Collection

Compliance data accumulates passively during implementation and battery runs. The `_compliance_log()` function in `event_handlers.py` produces JSONL entries recording:
- `injection_event`: which protocol variant was injected (base + which addendum)
- `completion_event`: teammate response, evidence presence, role match

### When to Run `--gate`

Run gate evaluation after:
- All WPs (A through E) are complete
- At least 15 Phase 2 battery scenarios have been executed
- Combined battery has >= 30 data points per stratum (Research, Engineer, QA)

**Command:**
```bash
cd /Users/mac/workspace/claude-mpm-fork && python scripts/audit_agent_teams_compliance.py --gate
```

### What Blocks Merge

| Gate | Criterion | Blocks Merge? |
|---|---|---|
| All fast tests pass | `make test` exits 0 | YES |
| Protocol token budget | All role variants < 2000 chars (~500 tokens) | YES |
| Engineer injection routing | Engineer subagent_type receives engineer addendum | YES |
| QA injection routing | QA subagent_type receives QA addendum | YES |
| Research injection routing | Research subagent_type receives research addendum | YES |
| Backward compatibility | `TEAMMATE_PROTOCOL` alias still importable and points to base | YES |
| Base does not contain Rule 3 | `TEAMMATE_PROTOCOL_BASE` does not contain "QA Scope Honesty" | YES |
| Compliance CI (if battery data exists) | 95% CI lower bound > 0.70 per stratum | YES |
| PM_INSTRUCTIONS.md section size | Agent Teams section < 120 lines | Advisory (not blocking) |

---

## 9. Risks

| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| 1 | PM context degrades with 5+ teammate results | MEDIUM | Medium | Hard limit: 3 teammates per phase, 7 total per pipeline. Progressive summarization at phase transitions. |
| 2 | Merge conflicts in parallel Engineering | MEDIUM | Medium | Pre-flight file overlap check (<20%). `git merge --no-commit` for safe detection. PM escalates to user. |
| 3 | Semantic conflicts (clean merge, broken code) | MEDIUM | Medium | Mandatory `make test` after every merge sequence. Blame attribution via `git log --name-only`. |
| 4 | Stale worktrees accumulate on disk | LOW | High | PM cleanup obligation in PM_INSTRUCTIONS.md. `git worktree list` + remove after every session. |
| 5 | Engineer teammates ignore scope declaration | LOW | Medium | Rule is short and imperative. PM cross-references diff summary against declared scope. |
| 6 | QA teammate produces false pass | MEDIUM | Low | QA rules require full command + output. PM spot-checks. Battery adversarial scenarios test this. |
| 7 | PM cannot translate Research findings into Engineering tasks | MEDIUM | Medium | PM instructions include phase transition protocol. Fallback: sequential delegation. |
| 8 | Claude Code platform changes break Agent Teams API | HIGH | Low | 6-month sunset clause from Phase 1. Fallback: `run_in_background` + `isolation: "worktree"`. |
| 9 | Token budget exceeded by future protocol additions | LOW | Low | Current margin: 58-124 tokens per role. Drop Rule 2 for Research (saves 66 tokens) if needed. |
| 10 | SendMessage peer coordination emerges despite Rule 5 | MEDIUM | Low | Rule 5 maintained. PostToolUse logging detects SendMessage events post-hoc. Phase 3 scope. |

---

## 10. Prior Work Reference

All Phase 0-1.5 documents that inform this plan, listed in dependency order:

### Phase 0 (Experiments)
| File | Key Finding Used |
|---|---|
| `docs-local/mpm-agent-teams/02-phase-0/00_phase0_overview.md` | Experiment framework and decision gates |
| `docs-local/mpm-agent-teams/02-phase-0/01_experiment_context_injection.md` | Context injection mechanism design |
| `docs-local/mpm-agent-teams/02-phase-0/02_experiment_circuit_breaker_protocol.md` | Circuit breaker protocol design, token budget (500 max) |
| `docs-local/mpm-agent-teams/02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` | Source of truth for TEAMMATE_PROTOCOL text, enforcement tiers |
| `docs-local/mpm-agent-teams/02-phase-0/05_decision_gate.md` | Phase 0 GO decision |

### Phase 1 (Production)
| File | Key Finding Used |
|---|---|
| `docs-local/mpm-agent-teams/03-phase-1/00_phase1_plan.md` | Phase 1 implementation plan structure |
| `docs-local/mpm-agent-teams/03-phase-1/01_context_injection_production.md` | TeammateContextInjector production design |
| `docs-local/mpm-agent-teams/03-phase-1/02_parallel_research_design.md` | Parallel Research protocol, PM orchestration, fallback |
| `docs-local/mpm-agent-teams/03-phase-1/03_pm_instructions_changes.md` | PM_INSTRUCTIONS.md Agent Teams section (lines 1135-1184) |
| `docs-local/mpm-agent-teams/03-phase-1/results/phase1_implementation_results.md` | Phase 1 test evidence and gate results |

### Phase 1.5 (Compliance Measurement)
| File | Key Finding Used |
|---|---|
| `docs-local/mpm-agent-teams/04-phase-1.5/investigation/00_phase1.5_plan.md` | Compliance gate design, passive data collection |
| `docs-local/mpm-agent-teams/04-phase-1.5/investigation/01_wp2_parallel_research.md` | Hook API limitations (inject/log only, cannot block) |
| `docs-local/mpm-agent-teams/04-phase-1.5/02-testcase-plan/00_testcase_plan.md` | Battery scenario format and scoring criteria |

### Phase 2 Research
| File | Key Finding Used |
|---|---|
| `docs-local/mpm-agent-teams/05-phase-2-research/00_research_plan.md` | Research questions and methodology |
| `docs-local/mpm-agent-teams/05-phase-2-research/01_worktree_and_merge.md` | RQ0+RQ1+RQ2: worktree mechanics, merge protocol, conflict detection |
| `docs-local/mpm-agent-teams/05-phase-2-research/03_build_verification.md` | RQ3: batch merge, PM runs tests directly, 300000ms timeout, blame attribution, fix-up Engineer |
| `docs-local/mpm-agent-teams/05-phase-2-research/04_team_compositions.md` | RQ4: 3 compositions, 5 anti-patterns, 3-Engineer cap, selection flow |
| `docs-local/mpm-agent-teams/05-phase-2-research/05_pm_orchestration.md` | RQ5: orchestration flows, context budget, blocking gates |
| `docs-local/mpm-agent-teams/05-phase-2-research/06_protocol_extensions.md` | RQ6: Option C (base + addendum), draft protocol texts, inject_context() code |
| `docs-local/mpm-agent-teams/05-phase-2-research/07_sendmessage_coordination.md` | RQ7: Rule 5 maintained, SendMessage deferred to Phase 3 |
| `docs-local/mpm-agent-teams/05-phase-2-research/08_rollback_recovery.md` | RQ8: 6 failure modes, 3-failure abort, worktree cleanup obligation |
| `docs-local/mpm-agent-teams/05-phase-2-research/09_phase2_implementation_plan.md` | Initial synthesis (pre-devil's-advocate) |
| `docs-local/mpm-agent-teams/05-phase-2-research/10_devils_advocate_implementation.md` | Must-fixes: PM delegates merge, RQ3 findings, batch merge strategy |

### Source Files (Current State)
| File | Relevance |
|---|---|
| `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` | Production code to modify (WP-A) |
| `src/claude_mpm/agents/PM_INSTRUCTIONS.md` (lines 1135-1184) | PM behavioral instructions to expand (WP-B) |
| `tests/hooks/test_teammate_context_injector.py` | Test file to extend (WP-C) |
| `tests/manual/agent_teams_battery/scenarios/*.yaml` | Battery scenarios to extend (WP-D) |
