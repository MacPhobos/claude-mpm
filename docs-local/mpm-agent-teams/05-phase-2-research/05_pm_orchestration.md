# RQ5 Findings: PM Orchestration Complexity

**Date:** 2026-03-20
**Research Question:** How much more complex does PM orchestration become with mixed teams?
**Scope:** Design orchestration flows for each RQ4 composition, analyze PM context constraints, define orchestration protocols with blocking gates and failure handling.
**Dependencies:** RQ4 (team compositions), Phase 1 parallel research design, Phase 1.5 Gate 2 data (context measurement).

---

## 1. Baseline: Phase 1 PM Orchestration (Research Teams)

Phase 1 established the following orchestration flow for parallel Research teams. This is the baseline against which Phase 2 complexity is measured.

**Source:** `03-phase-1/02_parallel_research_design.md` Section 2, `PM_INSTRUCTIONS.md` lines 1135-1184.

### Phase 1 Flow

```
DECOMPOSE --> SPAWN --> WAIT --> VALIDATE --> SYNTHESIZE --> REPORT
```

| Step | PM Action | Tokens Consumed | Blocking? |
|------|-----------|:---------------:|:---------:|
| DECOMPOSE | Write 2-3 research questions | ~200-400 (PM output) | No |
| SPAWN | 2-3 Agent tool calls in single message | ~100-300 per call (PM output) | No |
| WAIT | Idle -- Claude Code delivers results via SendMessage | 0 (PM idle) | YES -- PM blocked until all teammates report |
| VALIDATE | Check each result for evidence, file paths, forbidden phrases | ~500-2000 per result (added to PM context) | No |
| SYNTHESIZE | Combine findings, identify conflicts, attribute sources | ~300-600 (PM output) | No |
| REPORT | Present to user | ~200-500 (PM output) | No |

**Total PM context consumed per team session:** ~2000-6000 tokens (primarily from teammate completion messages).

**Orchestration complexity:** LINEAR. Each step follows the previous. One decision point (validate: pass or send back). No branching, no phases, no merge gates.

### Phase 1 Characteristics

- **Single phase:** All teammates are same role, all spawn simultaneously, all results collected together
- **No merge required:** Research is read-only -- no file conflicts, no integration
- **One QA gate:** Validate evidence presence (binary pass/fail per teammate)
- **Single synthesis:** PM combines N reports into 1 response
- **Maximum simultaneous state:** N completion messages in context (where N = 2-3)

---

## 2. Phase 2 Orchestration Flows

Each RQ4 composition introduces additional phases, gates, and decision points. Below is the orchestration protocol for each.

### 2.1 All-Engineer Parallel

**Phases:** 1 (parallel Engineering) + merge gate + integration test
**Complexity increase over Phase 1:** MODERATE -- adds merge and test gates.

```
Step 1: DECOMPOSE
    PM identifies 2-3 independent subsystems
    PM estimates file overlap per subsystem pair
    PM writes decomposition in response (user-visible)

Step 2: PRE-FLIGHT CHECK
    PM verifies: overlap < 20% between all subsystem pairs?
    |
    +-- Overlap >= 20%: ABORT team, fall back to sequential delegation
    |
    +-- Overlap < 20%: Proceed

Step 3: SPAWN
    PM spawns 2-3 Engineer teammates in single message
    Each teammate: isolation="worktree", specific subsystem scope, acceptance criteria
    PM specifies: "Modify ONLY files in <subsystem path>. Do NOT modify files outside your scope."

Step 4: WAIT
    PM waits for all Engineer completion messages
    [BLOCKING GATE: All Engineers must report before proceeding]

Step 5: VALIDATE (per Engineer)
    For each Engineer result:
    - Evidence block present? (code changes, diff summary)
    - File manifest complete? (every modified file listed)
    - Scope respected? (no files outside declared scope)
    - If validation fails: send back ONCE with specific ask
    [BLOCKING GATE: All validations must pass before merge]

Step 6: MERGE
    PM merges worktrees sequentially:
    - Merge Engineer-A's worktree into integration branch
    - Check: git conflicts?
      +-- Yes: PM resolves if trivial (whitespace, import order)
      |        PM escalates to user if non-trivial
      +-- No: Continue
    - Merge Engineer-B's worktree
    - Repeat for Engineer-C
    [BLOCKING GATE: All merges must succeed before testing]

Step 7: INTEGRATION TEST
    PM runs test suite against merged integration branch
    (Direct execution if test command is documented; delegate to QA if complex)
    |
    +-- Tests pass: Proceed to REPORT
    |
    +-- Tests fail: FAILURE HANDLING (see Section 4)

Step 8: REPORT
    PM presents results with attribution:
    "Engineer-A refactored subsystem X (files: ...). Engineer-B refactored subsystem Y (files: ...)."
    PM reports merge status and test results.
```

**Decision points:** 3 (pre-flight, merge conflict, test pass/fail)
**Blocking gates:** 3 (wait for all, validate all, merge all)
**PM context load:** ~4000-10000 tokens (Engineer completions are larger than Research completions because they include diff summaries)

### 2.2 Engineer-then-QA Pipeline

**Phases:** 2 (parallel Engineering, then sequential QA)
**Complexity increase over Phase 1:** HIGH -- two team sessions, cross-phase data flow.

```
--- PHASE A: ENGINEERING ---
(Steps 1-7 identical to All-Engineer Parallel above)

--- TRANSITION GATE ---
    PM has merged code and passing tests.
    PM prepares QA context: what was changed, where, why, what to verify.

--- PHASE B: QA ---

Step B1: SPAWN QA
    PM spawns QA agent (standard delegation, not necessarily Agent Teams)
    QA prompt includes:
    - Summary of changes made by Engineers (from Phase A synthesis)
    - Specific test scenarios to verify
    - File paths and line numbers of changes
    - "Test the MERGED code, not individual worktrees"

Step B2: WAIT
    PM waits for QA completion

Step B3: VALIDATE QA
    QA result must include:
    - Test commands executed with full output
    - Pass/fail with specific failure details
    - Coverage report (if applicable)
    - Regression test results

Step B4: REPORT
    PM presents full pipeline results:
    Phase A: Engineering changes (attributed per Engineer)
    Phase B: QA verification (pass/fail, coverage, issues found)
    |
    +-- QA found issues: PM identifies which Engineer's changes caused the issue
    |                     PM delegates fix to that Engineer (standard sequential)
    |
    +-- QA passed: Report success to user
```

**Decision points:** 4 (pre-flight, merge, test pass/fail, QA pass/fail)
**Blocking gates:** 4 (wait for Engineers, validate Engineers, merge, QA completion)
**PM context load:** ~6000-14000 tokens (Phase A results + Phase B results)
**Cross-phase data flow:** PM must carry Phase A findings (which Engineers changed what) into Phase B prompt. This is the primary context cost.

### 2.3 Research-then-Engineer Pipeline

**Phases:** 2-3 (parallel Research, then parallel Engineering, optionally QA)
**Complexity increase over Phase 1:** HIGHEST -- three potential phases, findings-to-tasks translation.

```
--- PHASE A: RESEARCH ---
(Phase 1 parallel Research pattern -- already implemented)

Step A1: DECOMPOSE into research questions
Step A2: SPAWN Research team (2-3 researchers)
Step A3: WAIT for all researchers
Step A4: VALIDATE research results (evidence, file paths)
Step A5: SYNTHESIZE research findings

--- TRANSITION GATE A->B ---
    PM translates research findings into engineering tasks.
    This is the hardest PM orchestration step:
    - PM must understand research findings deeply enough to decompose implementation work
    - PM must map findings to specific code changes
    - PM must identify file scope for each Engineer
    - PM must estimate overlap

    [DECISION POINT: Are research findings sufficient for implementation?]
    |
    +-- Insufficient: Delegate additional sequential Research. Do NOT re-run team.
    |
    +-- Sufficient: Proceed to Phase B

--- PHASE B: ENGINEERING ---
(All-Engineer Parallel pattern from Section 2.1 above)

Step B1: DECOMPOSE engineering tasks BASED ON research findings
Step B2: PRE-FLIGHT (file overlap check)
Step B3: SPAWN Engineer team
Step B4-B7: Wait, Validate, Merge, Test

--- OPTIONAL PHASE C: QA ---
(Only if user requests verification or task is high-risk)

Step C1: SPAWN QA against merged result
Step C2: QA verifies fixes against ORIGINAL research findings
Step C3: Report integrated results across all 3 phases
```

**Decision points:** 6+ (research sufficiency, engineering decomposition quality, pre-flight, merge, test, optional QA)
**Blocking gates:** 5+ (research completion, research validation, engineering completion, engineering validation, merge)
**PM context load:** ~8000-18000 tokens (Research phase results + Engineering phase results + optionally QA results)
**Critical path:** The A-to-B transition gate. If PM cannot translate research findings into actionable engineering tasks, the pipeline stalls. This requires PM to have BOTH research understanding and engineering decomposition ability simultaneously in context.

---

## 3. PM Context Constraint Analysis

### Token Budget Model

**Source for baseline figures:** Devil's advocate Concern 8 (lines 446-489), Phase 1 parallel research design Section 2.

Per-teammate context contribution to PM:

| Content Type | Tokens (est.) | When Added |
|--------------|:-------------:|:----------:|
| PM task description (output) | 200-500 | At spawn |
| Teammate completion message (input) | 500-2000 | At collection |
| PM validation response (output) | 100-300 | At validation |
| PM send-back + re-collection (if needed) | 500-1500 | At re-validation |

**Conservative estimate per teammate:** ~1500 tokens added to PM context.

### Context Accumulation by Composition

| Composition | Teammates (total across phases) | Est. Context from Teammates | Other PM State | Total Est. |
|-------------|:-------------------------------:|:---------------------------:|:--------------:|:----------:|
| Phase 1 Research (baseline) | 2-3 | 3000-4500 | 500 (synthesis) | 3500-5000 |
| All-Engineer Parallel | 2-3 | 3000-4500 | 1000 (merge + test) | 4000-5500 |
| Engineer-then-QA Pipeline | 3-4 | 4500-6000 | 2000 (merge + test + QA context) | 6500-8000 |
| Research-then-Engineer Pipeline | 4-6 | 6000-9000 | 3000 (synthesis + transition + merge + test) | 9000-12000 |

### Context Window Limits

Claude Code operates within a context window. Based on the devil's advocate analysis:

- **Estimated PM available context (after system prompt + PM_INSTRUCTIONS + CLAUDE.md):** ~150,000-180,000 tokens
- **PM quality degradation threshold:** Unknown precisely, but the devil's advocate (Concern 8, line 487) notes: "PM context accumulation: 14,000 tokens from 7 teammates' completion messages fills PM context fast"
- **Practical concern is not running OUT of context but DILUTING attention:** With 12,000+ tokens of teammate results, PM must track multiple completion reports, merge states, test outputs, and cross-reference them against each other. The more state in context, the higher the chance PM misses a detail or produces a less coherent synthesis.

### Practical Team Size Limit

Based on context analysis:

| Factor | Limit Implied | Reasoning |
|--------|:------------:|-----------|
| Context tokens | 5-7 teammates total | ~10,500 tokens at 1500/teammate. Leaves ample room in 200K window but accumulates significant state. |
| PM attention quality | 3-4 teammates per phase | Each completion report requires individual validation. Beyond 4, PM starts pattern-matching rather than genuinely verifying. |
| Merge complexity | 3 Engineers per phase | Merge #4 operates on a codebase already modified by merges 1-3. Each successive merge is against a different base. |
| Orchestration decision load | 2 phases per session | Each phase transition requires PM to translate outputs to inputs. The A-to-B transition in Research-then-Engineer is cognitively expensive. A third transition (B-to-C for QA) is feasible because QA input is simpler. |

**Recommended limits:**

| Constraint | Value |
|------------|:-----:|
| Maximum teammates per phase | 3 |
| Maximum phases per pipeline | 3 (Research, Engineering, QA) |
| Maximum total teammates per pipeline session | 7 (3 Research + 3 Engineers + 1 QA) |
| Maximum simultaneous teammates | 3 (all within one phase) |

### Should Multi-Phase Orchestration Use Separate Sessions?

**Question:** Should the PM run Research-then-Engineer as one continuous Claude Code conversation, or as separate sessions per phase?

**Analysis:**

| Approach | Pros | Cons |
|----------|------|------|
| **Single session** | PM retains all context (research findings, engineering plans, merge results). No need to re-establish context. | Context accumulates across all phases. Research findings take up space even during Engineering phase when they are no longer actively needed. |
| **Separate sessions per phase** | Each session starts fresh with minimal context. PM gets full context window for each phase. | Context re-establishment required. PM must summarize prior phase findings in the new session prompt. Information loss during summarization. |

**Recommendation: Single session with progressive summarization.**

The PM should operate in a single session but SUMMARIZE completed phases before starting new ones. Specifically:
- After Phase A (Research) completes and Phase B (Engineering) begins, the PM's working context should contain a SUMMARY of research findings (not the full teammate reports) plus the engineering task decomposition.
- This mimics how a human manager works: they read the full research reports, create an implementation plan, and then work from the plan -- they do not re-read the full reports while managing engineers.

**Implementation:** The PM should produce a "phase transition summary" at each gate:

```
Phase A complete. Summary of findings:
1. [Key finding 1 from Researcher-A]
2. [Key finding 2 from Researcher-B]
3. [Key finding 3 from Researcher-C]

Engineering decomposition based on findings:
- Task 1: [description] (subsystem X, estimated files: ...)
- Task 2: [description] (subsystem Y, estimated files: ...)
```

This summary replaces the full Research results in the PM's working memory for Phase B. Context cost: ~500 tokens instead of ~4500 tokens.

---

## 4. Failure Handling Per Gate

Every blocking gate needs a defined failure path. Without explicit failure handling, the PM will either stall indefinitely or make ad-hoc decisions that may be suboptimal.

### Gate: Pre-Flight (File Overlap Check)

| Outcome | PM Action |
|---------|-----------|
| Overlap < 20% | Proceed with parallel team |
| Overlap 20-50% | Warn user: "Subsystems share files X, Y, Z. Parallel Engineering may produce merge conflicts. Proceed anyway, or use sequential delegation?" If user approves, proceed with explicit awareness. |
| Overlap > 50% | Abort team. Fall back to sequential delegation. Inform user: "These tasks share too many files for safe parallel execution." |

### Gate: Teammate Completion

| Outcome | PM Action |
|---------|-----------|
| All teammates complete | Proceed to validation |
| 1+ teammates timeout | Synthesize available results. Note gaps: "Engineer-B did not complete subsystem Y refactoring." Offer user: retry the failed task as standalone delegation, or proceed without it. |
| All teammates fail | Report failure to user. Do NOT retry as team. Offer sequential delegation as fallback. |

### Gate: Validation

| Outcome | PM Action |
|---------|-----------|
| All teammates pass validation | Proceed to merge |
| 1 teammate fails validation | Send back ONCE with specific ask. If re-submission fails, accept what is available and note the gap. |
| Majority fail validation | Abort team. Report: "Multiple engineers produced incomplete results. This task may be too complex for parallel execution." Offer sequential fallback. |

### Gate: Merge

| Outcome | PM Action |
|---------|-----------|
| All merges clean | Proceed to integration test |
| Merge conflict (trivial) | PM resolves automatically: whitespace changes, import ordering, adjacent-line additions. Log the resolution. |
| Merge conflict (non-trivial) | STOP. Present conflict to user with both versions. Offer: "Engineer-A changed function X to do A. Engineer-B changed the same function to do B. Which approach should be kept?" OR delegate conflict resolution to a new Engineer agent. |
| Merge conflict (semantic) | Merges succeed (no git conflicts) but code is logically inconsistent (e.g., Engineer-A renamed a function that Engineer-B calls). Caught by integration test, not by merge. See integration test gate. |

### Gate: Integration Test

| Outcome | PM Action |
|---------|-----------|
| All tests pass | Proceed to report (or QA phase) |
| Tests fail -- attributable to one Engineer | Report: "Tests fail in subsystem X after Engineer-A's changes. Engineer-B's changes are clean." Offer: revert Engineer-A's merge, fix via sequential delegation, or user intervention. |
| Tests fail -- interaction between Engineers | Report: "Tests pass for each Engineer individually but fail when merged. This is an integration conflict between subsystems X and Y." Offer: revert to pre-merge state, delegate integration fix to a single Engineer with full context. |
| Tests fail -- pre-existing | Report: "These test failures exist in the base branch (verified by running tests before merge). Not caused by team changes." Proceed to report. |

### Gate: QA (in Pipeline)

| Outcome | PM Action |
|---------|-----------|
| QA passes | Report full pipeline success |
| QA finds issues in one Engineer's work | Delegate fix to that specific Engineer (sequential). Re-run QA after fix. |
| QA finds issues across multiple Engineers | Delegate comprehensive fix to a SINGLE Engineer with full context (not parallel -- the fix requires cross-subsystem understanding). Re-run QA after fix. |
| QA itself fails (crashes, timeout) | Report Engineering results without QA verification. Note: "QA verification was not completed. Manual testing recommended." |

---

## 5. Orchestration Protocol Summary

### Complete Protocol for Phase 2 PM Orchestration

```
1. RECEIVE user request
2. CLASSIFY: Is this Research-only, Engineering-only, or Pipeline?
3. DECOMPOSE into phases based on RQ4 composition rules
4. For EACH PHASE:
   a. PRE-FLIGHT: Check team viability (file overlap, dependency check)
   b. SPAWN: Create teammates (all in single message)
   c. WAIT: Block until all teammates report
   d. VALIDATE: Per-teammate QA gate (send back once if needed)
   e. PHASE-SPECIFIC GATE:
      - Research phase: SYNTHESIZE findings
      - Engineering phase: MERGE worktrees + RUN integration tests
      - QA phase: COLLECT verification results
   f. PHASE TRANSITION SUMMARY: Compress completed phase to summary
5. REPORT: Present full pipeline results with per-phase attribution
6. On ANY gate failure: Follow failure handling table (Section 4)
```

### Orchestration Complexity Comparison

| Metric | Phase 1 (Research) | All-Engineer | Eng-then-QA | Research-then-Eng |
|--------|:------------------:|:------------:|:-----------:|:-----------------:|
| Phases | 1 | 1 + gates | 2 | 2-3 |
| Decision points | 1 | 3 | 4 | 6+ |
| Blocking gates | 1 | 3 | 4 | 5+ |
| Merge operations | 0 | 2-3 | 2-3 | 2-3 |
| Test runs | 0 | 1 | 2 (integration + QA) | 1-2 |
| PM context (est.) | 3.5-5K tokens | 4-5.5K tokens | 6.5-8K tokens | 9-12K tokens |
| Failure paths | 2 (timeout, validation) | 6 | 8 | 10+ |
| PM instructions lines needed | ~50 (existing) | ~30 additional | ~15 additional (on top of Eng) | ~10 additional (on top of Pipeline) |

---

## 6. Implications for PM_INSTRUCTIONS.md Changes

### What Must Be Added

1. **Phase-based orchestration model:**
   The PM must understand that Phase 2 teams operate in PHASES, not as a single flat spawn. This is the fundamental conceptual change from Phase 1. The PM instructions must make explicit:
   - "Parallel teammates within a phase are same-role"
   - "Phases execute sequentially"
   - "Each phase has a blocking gate before the next phase begins"

2. **Merge protocol:**
   PM currently has no instructions for merging worktrees. Phase 2 requires:
   - Sequential merge order (one worktree at a time)
   - Conflict classification (trivial vs non-trivial)
   - Escalation path for non-trivial conflicts

3. **Phase transition summaries:**
   PM must be instructed to COMPRESS completed phase results before starting the next phase. Without this instruction, PM will carry full Research reports into the Engineering phase, wasting context.

4. **Failure handling decision tree:**
   PM needs explicit guidance for each failure mode. The tables in Section 4 should be condensed into PM-actionable rules:
   - "If a teammate times out, proceed with available results"
   - "If merge conflicts, resolve trivial ones automatically; escalate non-trivial to user"
   - "If integration tests fail, identify the responsible Engineer's changes"

5. **Team size limits:**
   - Maximum 3 teammates per phase (hard limit)
   - Maximum 3 phases per pipeline (Research, Engineering, QA)
   - Maximum 7 total teammates per pipeline session

### Estimated PM_INSTRUCTIONS.md Growth

| Change Category | Lines | Section |
|----------------|:-----:|---------|
| Phase-based model explanation | ~10 | New subsection under "Agent Teams" |
| Merge protocol | ~15 | New subsection under "Agent Teams" |
| Phase transition summary instruction | ~5 | Addition to spawning protocol |
| Failure handling rules (condensed) | ~15 | New subsection under "Agent Teams" |
| Team size limits | ~5 | Addition to anti-patterns |
| **Total Phase 2 additions** | **~50** | |
| **Combined with Phase 1 (existing ~50)** | **~100 total** | Full "Agent Teams" section |

### What Should NOT Be Added

- Detailed failure handling tables (too verbose for PM instructions; reference external doc instead)
- Full orchestration flowcharts (PM should internalize the protocol, not follow a flowchart)
- Token budget analysis (internal engineering concern, not a PM behavioral instruction)
- Context window management tips (PM already has auto-compression; explicit management would be micromanaging)

---

## 7. Open Questions for Implementation Plan

1. **Merge delegation:** Should the PM merge worktrees directly (via git commands) or delegate to a Version Control agent? Direct merge is faster but violates the "PM does not execute complex multi-step tasks" principle. Delegating adds latency but stays within PM's orchestration role.

2. **Integration test delegation:** Similar question. PM_INSTRUCTIONS.md currently allows PM to "run single documented test commands" directly. Is `make test` after a 3-way merge a "single documented test command" or a "complex multi-step task"? Recommendation: PM runs tests directly if the command is documented in CLAUDE.md; delegate to QA if the test requires setup or interpretation.

3. **Phase 1.5 Gate 2 data:** This analysis estimates context costs but has not been validated against actual Gate 2 measurements. If Gate 2 shows that Agent Teams context cost is significantly different from estimates here (higher or lower), the team size limits should be adjusted accordingly.

4. **Progressive summarization implementation:** How does the PM actually "compress" a completed phase? Does it write a summary to a file (persistent)? Or does it simply state the summary in its next message (ephemeral, subject to Claude Code's auto-compression)? Recommendation: PM writes phase transition summary as a message to itself (in the conversation), not to a file. This keeps it in context naturally and lets Claude Code's compression handle long-term management.

5. **Abort threshold:** At what point should the PM abort a pipeline entirely vs. continuing with partial results? Current heuristic: if >50% of teammates in a phase fail, abort the phase. If a phase abort blocks a downstream phase, abort the pipeline. This needs user testing to validate.
