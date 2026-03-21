> **Phase 2 Extension:** This design has been extended to support parallel Engineering and multi-phase pipelines. See [`06-phase-2-impl-plan/00_implementation_plan.md`](../06-phase-2-impl-plan/00_implementation_plan.md) for the Phase 2 design, and [`06-phase-2-impl-plan/01_implementation_results.md`](../06-phase-2-impl-plan/01_implementation_results.md) for implementation results.

---

# Parallel Research Pattern: Design Spec

**Phase:** 1
**Status:** Implementation spec
**Scope:** PM spawns 2-3 Research teammates for complex investigations
**Constraint:** Phase 1 supports ONLY parallel Research. No parallel Engineering or QA.

---

## 1. When PM Uses Teams vs Standard Delegation

### Decision Criteria (Explicit)

PM evaluates every Research delegation against these criteria. If **any** criterion in the "Use Teams" column is met AND **none** of the blockers apply, PM spawns a team.

| Criterion | Use Teams | Use Standard | Example |
|-----------|-----------|-------------|---------|
| **Subtask count** | >= 2 independent research questions | 1 research question | "Analyze auth patterns AND evaluate DB options" → Teams |
| **Scope breadth** | Investigation spans >= 2 unrelated subsystems | Single subsystem or file group | "Research hooks AND research CLI commands" → Teams |
| **Time sensitivity** | User explicitly requests speed ("quickly", "in parallel") | No urgency signal | "Quickly research X and Y" → Teams |
| **Estimated overlap** | Subtasks share < 20% of files/components | Subtasks share > 50% of files | Two subsystems with shared models → Standard |

### Blockers (Never Use Teams When)

- Subtasks have **sequential dependency** (research B needs research A's findings)
- The investigation requires **shared mutable state** (writing to same docs/research/ file)
- Research scope is **small** (estimating < 3 files to read, < 2 search queries)
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var is **not set**
- Previous team in this session had a **peer-to-peer violation** (restrict to sequential)

### Decision Flow

```
User request arrives
  │
  ├─ Is this a Research task? ─── No ──→ Standard delegation (Phase 1: teams only for Research)
  │
  ├─ Can it decompose into >= 2 independent questions?
  │   │
  │   ├── No ──→ Standard delegation (single Research agent)
  │   │
  │   └── Yes ──→ Check blockers:
  │               │
  │               ├── Any blocker present? ──→ Standard delegation
  │               │
  │               └── No blockers ──→ Check Agent Teams available?
  │                                   │
  │                                   ├── CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS != 1
  │                                   │   └──→ Fallback: run_in_background (Section 5)
  │                                   │
  │                                   └── Available ──→ Spawn Research team
```

---

## 2. PM Orchestration Flow

### Step-by-Step Protocol

```
1. DECOMPOSE
   PM breaks the user request into N independent research questions (N = 2-3).
   Each question must be answerable WITHOUT the other questions' results.
   PM writes the decomposition in its response before spawning.

2. SPAWN TEAM
   PM creates teammates using the Agent tool with team_name parameter.
   All spawn calls in a SINGLE message (Claude Code spawns them concurrently).

   For each teammate:
   - subagent_type: "Research"
   - model: "sonnet" (default) or "opus" (if user requests depth)
   - team_name: "<descriptive-team-name>"
   - name: "<descriptive-teammate-name>"  (e.g., "auth-researcher", "db-researcher")
   - prompt: Task-specific research question with scope boundaries

3. WAIT FOR RESULTS
   Claude Code delivers teammate results via SendMessage.
   PM does NOT poll or check on teammates — it waits for messages.

4. VALIDATE EACH RESULT (per Section 3)
   For each teammate's SendMessage:
   - Check for evidence block (CB#3)
   - Check for file manifest (CB#4)
   - If missing: send teammate back with specific ask
   - If present: accept result

5. SYNTHESIZE
   PM combines validated results into a single coherent response.
   PM identifies conflicts between teammate findings (Section 4).
   PM reports to user with attribution: "Researcher A found X; Researcher B found Y."

6. REPORT
   PM presents synthesized findings to user.
   PM does NOT claim findings as its own — attributes to teammates.
```

### Spawn Template

PM uses this pattern for each teammate:

```
Agent tool call:
  description: "Research <specific topic>"
  subagent_type: "Research"
  model: "sonnet"
  team_name: "research-<topic>"
  name: "<topic>-researcher"
  prompt: |
    Investigate <specific question>.

    Scope: ONLY look at <specific files/subsystems>.
    Do NOT investigate <out-of-scope areas>.

    Deliverable:
    - Key findings (3-5 bullet points)
    - File paths examined with relevant line numbers
    - Specific code patterns or evidence found
    - Recommendations (if applicable)
```

---

## 3. Team Composition Rules

### Size Limits

| Constraint | Value | Rationale |
|------------|-------|-----------|
| **Minimum teammates** | 2 | Below 2, standard delegation is equivalent |
| **Maximum teammates** | No ceiling | Constrained by decomposition quality — one teammate per independent question |
| **All same type** | Research only | Phase 1 scope — no mixed Engineer/QA/Research teams |

### Task Decomposition Rules

1. **Each teammate gets ONE question.** Not a list of questions — a single focused investigation.
2. **Scope boundaries are explicit.** Each prompt specifies which subsystems/files to examine.
3. **No overlap by default.** If two teammates must examine the same file, PM explicitly states this is intentional in both prompts.
4. **Acceptance criteria in every prompt.** What does "done" look like? (e.g., "List all auth middleware files with their purpose")

### Model Selection

| Scenario | Model | Cost Impact |
|----------|-------|-------------|
| Standard research (pattern search, file listing) | sonnet | 1x (baseline) |
| Deep architectural analysis, complex reasoning | opus | ~5x per teammate |
| User explicitly requests thoroughness | opus | User-directed |

Default is **sonnet** for all Research teammates. PM overrides to opus only when:
- User explicitly requests deep analysis
- The research question requires cross-system reasoning that sonnet would likely miss
- Previous sonnet attempt returned insufficient results

---

## 4. Result Collection and Verification

### What PM Checks (QA Gate for Research)

Each teammate's result must contain:

| Element | Required? | Verification Method |
|---------|:---------:|---------------------|
| **Findings summary** | Yes | At least 2 specific findings (not vague claims) |
| **File paths examined** | Yes | At least 1 file path with line reference |
| **Evidence** | Yes | Specific code snippets, grep output, or command results |
| **Forbidden phrases** | Absent | None of: "should work", "appears to be", "looks correct", "probably" |
| **File manifest** | If files modified | Path + action + summary for each file |

### Send-Back Protocol

If a teammate's result is incomplete:

```
SendMessage to <teammate-name>:
  "Your research report is missing [specific element].
   Provide [specific evidence type] for your findings about [topic].
   Do not summarize what you already reported — provide the missing evidence only."
```

PM sends back at most **once per teammate**. If the second response is still incomplete, PM accepts what's available and notes the gap in the synthesis.

### Team Completion

The team is "complete" when:
- All teammates have reported results (via SendMessage to team lead)
- Each result has passed the QA gate (or been sent back once and re-received)
- PM has synthesized findings

The team is "partially complete" when:
- At least one teammate has reported
- At least one teammate is still working or has failed
- PM waits up to the Claude Code timeout, then synthesizes what's available with explicit gaps noted

### Handling Conflicting Findings

When two researchers report contradictory findings:

1. **Present both to user with attribution.** "Researcher A found X in `src/auth/`. Researcher B found Y in `src/middleware/`. These conflict on [specific point]."
2. **PM does NOT resolve the conflict.** PM does not have domain expertise to judge which finding is correct.
3. **PM suggests resolution.** "To resolve: examine `src/auth/middleware.py:45-60` where both findings converge."
4. **PM does NOT spawn a third researcher** to break the tie. That's Phase 2 territory.

---

## 5. Fallback Protocol

### When `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` Is Absent

PM detects this during the decomposition step (Step 1). Fallback:

```
PM notices Agent Teams unavailable.
PM uses existing run_in_background pattern:
  - Spawn N Research agents using Agent tool WITHOUT team_name
  - Each runs as an independent background subagent
  - PM collects results as they complete
  - Same synthesis and verification protocol applies

PM does NOT inform the user about the fallback.
The output quality is identical; only the underlying mechanism differs.
```

**Implementation note:** The PM prompt should say: "If Agent Teams is available (team_name parameter works), use it. Otherwise, use the standard Agent tool with `run_in_background: true`."

### When Teammate Spawn Fails

If the Agent tool call with team_name returns an error:

1. **Retry once** without team_name (standard subagent).
2. If retry succeeds: continue with standard delegation for that subtask.
3. If retry fails: report to user. "Could not spawn researcher for [topic]. Proceeding with available results."
4. **Never block the entire response** on a single spawn failure.

### When One Teammate Fails Mid-Work

If a teammate reports a blocker or fails to respond:

1. PM synthesizes results from the teammates that DID complete.
2. PM notes the gap: "Research on [topic] was not completed due to [reason]."
3. PM does NOT retry the failed teammate (that's a new delegation, not a team continuation).
4. If the user requests the missing research, PM delegates it as a new standard Research task.

---

## 6. Example Scenarios

### Scenario A: Codebase Architecture Review

**User:** "Research how authentication and authorization work in this codebase"

**PM decomposition:**
- Q1: "How does authentication work? (login flow, session management, token handling)"
- Q2: "How does authorization work? (role-based access, permission checks, middleware)"

**PM spawns:**
- auth-researcher: Q1, scope limited to `src/auth/`, `src/middleware/auth*`
- authz-researcher: Q2, scope limited to `src/permissions/`, `src/middleware/authz*`

**Synthesis:** PM combines both into a unified auth/authz architecture report.

### Scenario B: Technology Evaluation

**User:** "Research our database usage patterns and our caching patterns"

**PM decomposition:**
- Q1: "What database access patterns exist? (ORM usage, raw queries, connection pooling)"
- Q2: "What caching patterns exist? (Redis, in-memory, CDN, cache invalidation)"

These are independent subsystems → team is appropriate.

### Scenario C: NOT Suitable for Teams

**User:** "Research how the login flow works end-to-end"

This is a single linear investigation through one flow. One Research agent traces the flow from entry point to completion. Decomposing it would require artificial boundaries that fragment the understanding. → Standard delegation.
