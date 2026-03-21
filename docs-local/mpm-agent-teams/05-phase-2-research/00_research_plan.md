# Phase 2 Research Plan: Parallel Engineering & Mixed Teams

**Issue:** #290
**Phase:** 2 (Research — gated on Phase 1.5 success)
**Date:** 2026-03-20
**Branch:** mpm-teams
**Gate:** Phase 1.5 must pass Gates 1, 2, 3 before Phase 2 research begins
**Purpose:** Deep investigation to produce a Phase 2 implementation plan. This is the research, not the plan itself.

---

## What Phase 2 Must Deliver

Phase 1/1.5 validated parallel Research teammates. Phase 2 extends Agent Teams to:

1. **Parallel Engineer teammates** — Multiple engineers modifying code simultaneously
2. **Parallel QA teammates** — Multiple QA agents testing different aspects simultaneously
3. **Mixed-role teams** — Research + Engineer + QA coordinating in a single team session
4. **Result aggregation** — PM merges work products from multiple write-capable agents

This is fundamentally harder than parallel Research because Engineers WRITE files. Research agents are read-only — no conflicts possible. Engineers create merge conflicts, broken builds, and integration failures.

---

## Prior Work Reference

All prior Agent Teams documents live under `docs-local/mpm-agent-teams/`. The researcher must read these before starting.

### Phase 0 (Validation)

| File | Lines | Content |
|------|-------|---------|
| `02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` | 712 | CB enforcement tiers (T1-T4), teammate protocol (Section 3), team lead protocol (Section 4), peer-to-peer risk matrix (Section 5), validation framework (Section 7) |
| `02-phase-0/PHASE0_DECISION.md` | — | GO/NO-GO decision, 5 success criteria, Phase 1 requirements |

### Phase 1 (Minimal Viable Integration)

| File | Lines | Content |
|------|-------|---------|
| `03-phase-1/00_phase1_plan.md` | 180 | Master plan, 5 work packages, 3 mandatory gates, devil's advocate integration, Phase 2 deferred items (lines 19-28), engineering spike recommendation (line 140) |
| `03-phase-1/01_context_injection_production.md` | 237 | Activation mechanism, protocol sync, logging, feature flag lifecycle |
| `03-phase-1/02_parallel_research_design.md` | 277 | Decision criteria, orchestration flow, team composition rules, result verification, fallback protocol, example scenarios |
| `03-phase-1/03_pm_instructions_changes.md` | 134 | PM_INSTRUCTIONS.md diff spec, Phase 2 deferred changes table (lines 98-108) |
| `03-phase-1/04_hook_registration.md` | 297 | TeammateIdle/TaskCompleted handlers, Phase 2 enhancement notes (lines 135, 147) |
| `03-phase-1/05_devils_advocate.md` | 571 | 8 concerns — especially Concern 3 (parallel research value, lines 135-193), Concern 7 (engineers excluded, lines 389-435), Concern 8 (cost at scale, lines 439-506) |
| `03-phase-1/results/phase1_implementation_results.md` | 232 | What was built, test evidence, gate status, 7 post-implementation findings, Phase 2 recommendation (Section 8.6) |

### Phase 1.5 (Gate Qualification)

| File | Lines | Content |
|------|-------|---------|
| `04-phase-1.5/investigation/00_phase1.5_plan.md` | ~155 | WP2+WP5 plan, design decisions (no teammate cap, test separation, compliance logging), amended to remove in-memory counting |
| `04-phase-1.5/investigation/01_wp2_parallel_research.md` | ~160 | Cap removal locations, code vs instruction enforcement split, hook API limitations (cannot block tool calls), fallback behavior |
| `04-phase-1.5/investigation/02_wp5_compliance_measurement.md` | ~320 | _compliance_log() design, audit script with Clopper-Pearson CI, 35-task battery design, scoring criteria, JSONL schema |

### Source Code (Implementation)

| File | Content |
|------|---------|
| `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` | Context injection: TEAMMATE_PROTOCOL constant (~421 tokens, 5 rules), auto-detection (4-level precedence), should_inject() gate |
| `src/claude_mpm/hooks/claude_hooks/event_handlers.py` | Hook wiring: handle_pre_tool_fast (injection point), handle_teammate_idle_fast, handle_task_completed_fast |
| `src/claude_mpm/hooks/claude_hooks/hook_handler.py` | Hook lifecycle: each invocation is a fresh Python process (singleton pattern, but process-scoped). Lines 155-167 (singleton), 794-842 (main entry). Critical for understanding why in-memory state doesn't persist. |
| `src/claude_mpm/agents/PM_INSTRUCTIONS.md` | PM behavioral spec: worktree isolation (lines 118-148), Agent Teams section (lines 1135-1181), delegation table, model routing, circuit breaker list |
| `src/claude_mpm/agents/BASE_AGENT.md` | Universal agent rules inherited by all teammates |

### Tests

| File | Content |
|------|---------|
| `tests/hooks/test_teammate_context_injector.py` | 21 unit + 4 integration tests for injection |
| `tests/hooks/test_agent_teams_validation_logging.py` | 9 tests for Agent Teams event logging |

### Issue and Original Motivation

| Source | Content |
|--------|---------|
| GitHub Issue #290 | Original use cases: "Complex Features: Frontend + backend + test coordinating simultaneously", "Large Refactoring: Multiple engineers working on different subsystems", "Security Audit: Research + implementation + verification in parallel" |

---

## Research Questions

Phase 2 research must answer these questions before an implementation plan can be written. Each question maps to an investigation task.

### RQ1: Worktree Isolation Mechanics

**Question:** How does `isolation: "worktree"` actually work in Claude Code, and does it solve the parallel Engineering problem?

**Investigate:**
- How does Claude Code create and manage worktrees for agents?
- Does each teammate in an Agent Teams session get its own worktree automatically, or must `isolation: "worktree"` be set per-spawn?
- What happens when two worktree-isolated teammates modify the SAME file? Does git detect the conflict at merge time?
- What is the merge strategy? Does Claude Code auto-merge worktrees, or does the PM/user need to merge manually?
- What happens to worktrees when a teammate completes? Auto-cleanup? Stale worktree accumulation?
- Can the PM merge worktree branches programmatically (via git commands)?
- What is the overhead of worktree creation? (Time, disk, git operations)
- Is there a limit on concurrent worktrees?

**Why this matters:** If worktree isolation handles merge conflicts gracefully, the parallel Engineering problem is largely solved by the platform. If it doesn't, MPM must build a merge coordination layer.

**Prior docs to read first:**
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md` lines 118-148 (worktree isolation for parallel agents, EnterWorktree vs isolation: "worktree")
- `03-phase-1/05_devils_advocate.md` lines 415-420 (unsolved engineering problems: file conflict, build verification, merge strategy)
- `03-phase-1/00_phase1_plan.md` line 140 (engineering spike recommendation: 2 parallel Engineers on non-overlapping files)

**Method:** Hands-on experiment. Spawn 2 Engineer agents in isolated worktrees modifying overlapping files. Observe what happens. Document the merge path.

### RQ2: File Conflict Detection and Resolution

**Question:** When two parallel Engineers modify overlapping files, how should conflicts be detected and resolved?

**Investigate:**
- What are the conflict scenarios?
  - Same file, different sections (likely auto-mergeable)
  - Same file, same section (true conflict — needs human or PM resolution)
  - Different files, shared dependency (semantic conflict — tests catch it, git doesn't)
  - Different files, no overlap (no conflict — trivial case)
- Can the PM detect potential conflicts BEFORE spawning (by analyzing task scope)?
- Can the PM detect actual conflicts AFTER completion (by running git merge --no-commit)?
- Who resolves conflicts? PM? User? A dedicated merge agent?
- What does the existing MPM `run_in_background` + `isolation: "worktree"` pattern do today for parallel Engineers (outside Agent Teams)? Are there existing patterns to learn from?
- How do other multi-agent frameworks handle parallel writes? (LangGraph, CrewAI, etc.)

**Why this matters:** This is the core unsolved problem. Research agents don't have it. Engineers do.

**Prior docs to read first:**
- RQ1 findings (must complete first)
- `03-phase-1/05_devils_advocate.md` lines 415-418 (file conflict, merge strategy, integration test — the 4 unsolved problems)
- `04-phase-1.5/investigation/01_wp2_parallel_research.md` Section 2 (code vs instruction enforcement split — what hooks CAN and CANNOT do)

**Method:** Codebase analysis + experiment. Review how PM_INSTRUCTIONS.md currently handles worktree isolation for parallel agents. Run the 2-Engineer experiment from RQ1. Survey approaches in other frameworks via web research.

### RQ3: Build Verification Across Parallel Changes

**Question:** When Engineers A and B each produce working code independently, does A+B together still compile/pass tests?

**Investigate:**
- After merging two worktrees, who runs the integration test?
- Should the PM run tests after merging? Or delegate to a QA agent?
- What if the merge succeeds (no git conflicts) but tests fail (semantic conflict)?
- How long does a typical test run take? Is it acceptable to block the PM while tests run?
- Can integration testing be parallelized with ongoing work?
- What is the rollback strategy if A+B fails integration? Revert B? Revert both? Manual fix?

**Why this matters:** Two pieces of code that work independently can fail together. This is the integration testing problem, and it's unique to parallel Engineering.

**Prior docs to read first:**
- RQ2 findings (must complete first)
- `CLAUDE.md` in project root (running tests: `uv run pytest`, `make test`)
- `03-phase-1/05_devils_advocate.md` line 418 ("Who runs the final integration test? Neither Engineer has the complete picture")

**Method:** Design analysis. Map the possible outcomes of merging N worktrees and define the verification protocol for each.

### RQ4: Team Composition Patterns

**Question:** What team compositions make sense, and what are the anti-patterns?

**Investigate:**
- **Research-then-Engineer:** N researchers investigate, then N engineers implement based on findings. Sequential dependency — is this a team or a pipeline?
- **Engineer-then-QA:** N engineers build, then QA verifies. Sequential dependency again.
- **Research + Engineer parallel:** Researcher investigates while Engineer builds scaffolding. Semi-independent. Useful?
- **Engineer + QA parallel:** Engineer builds while QA writes tests for the interface contract. Semi-independent. Useful?
- **All-Engineer parallel:** 3 engineers on 3 non-overlapping subsystems. The core Phase 2 use case.
- **Mixed all-role:** Research + Engineer + QA on different aspects of the same feature. The most complex case.
- What team compositions are actively harmful? (e.g., 2 Engineers on overlapping files without worktree isolation)

**Why this matters:** PM_INSTRUCTIONS.md needs clear guidance on which compositions to use and which to avoid. Bad compositions waste tokens and create conflicts.

**Prior docs to read first:**
- GitHub Issue #290 (original use cases: frontend+backend+test, large refactoring, security audit)
- `03-phase-1/05_devils_advocate.md` lines 394-399 (issue #290 use cases quoted, value asymmetry analysis)
- `03-phase-1/02_parallel_research_design.md` Section 3 (team composition rules — Phase 1 was Research-only)
- `03-phase-1/03_pm_instructions_changes.md` lines 98-108 (Phase 2 deferred changes: mixed teams, peer violation detection, team lead spot-check, dashboard)

**Method:** Design analysis + review of issue #290 original use cases. Map each use case to a team composition and assess feasibility.

### RQ5: PM Orchestration Complexity

**Question:** How much more complex does PM orchestration become with mixed teams?

**Investigate:**
- Phase 1 PM orchestration: decompose → spawn → wait → validate → synthesize. Linear.
- Phase 2 PM orchestration: decompose → spawn researchers → collect findings → decompose engineering tasks → spawn engineers → merge worktrees → run integration tests → spawn QA → collect results. Multi-phase with dependencies.
- Can the PM handle multi-phase orchestration within a single Agent Teams session?
- What happens to PM context when managing 5-7 teammates across 3 roles?
- Is there a practical limit on PM orchestration complexity before context degradation?
- Should Phase 2 limit team compositions to reduce PM cognitive load? (e.g., "all-same-role teams only" even across roles?)

**Why this matters:** PM context window is finite. More teammates = more results to track, validate, and merge. At some point the PM becomes the bottleneck.

**Prior docs to read first:**
- Phase 1.5 Gate 2 results (context window measurement — must exist before this RQ)
- `03-phase-1/02_parallel_research_design.md` Section 2 (PM orchestration flow — the Phase 1 baseline)
- `03-phase-1/05_devils_advocate.md` lines 486-489 (PM context accumulation as self-limiting factor)
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md` full "Agent Teams: Parallel Research" section (lines 1135-1181)

**Method:** Analysis of Phase 1.5 Gate 2 results (context measurement). Extrapolate to multi-role scenarios. Design PM orchestration protocols for each team composition.

### RQ6: TEAMMATE_PROTOCOL Extensions

**Question:** Does the TEAMMATE_PROTOCOL need role-specific rules for Engineers and QA?

**Investigate:**
- Current protocol is role-agnostic (5 rules apply to all teammates)
- Engineer-specific concerns:
  - Must declare files they intend to modify BEFORE starting (scope declaration)
  - Must run linting/formatting before reporting completion
  - Must NOT modify files outside their declared scope
  - Must report git diff summary (not just file list)
- QA-specific concerns:
  - Must run tests in a clean environment (no leftover state from previous runs)
  - Must report test command AND full output (not just pass/fail counts)
  - Must test against the MERGED code (not just their assigned engineer's worktree)
- Token budget impact: adding role-specific rules increases injection from ~421 tokens to ~600-700 tokens. Is this within budget?
- Should role-specific rules be injected conditionally based on subagent_type?

**Why this matters:** The current protocol was designed for Research (read-only). Engineers and QA have different failure modes that need different rules.

**Prior docs to read first:**
- `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` lines 24-54 (current TEAMMATE_PROTOCOL constant — the 5 rules with CB# references, ~421 tokens)
- `02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 3 (canonical protocol text), Section 2 (enforcement tiers T1-T4)
- `src/claude_mpm/agents/BASE_AGENT.md` (universal rules already inherited by all agents — overlap analysis needed)
- Phase 1.5 compliance battery results (which rules had lowest compliance? — must exist before this RQ)

**Method:** Analyze the 5 existing rules for role-applicability. Draft role-specific extensions. Measure token budget impact. Review Phase 1.5 compliance data for Research — which rules had lowest compliance? Those likely need strengthening for Engineers too.

### RQ7: SendMessage Coordination Patterns

**Question:** Should teammates coordinate via SendMessage, or should all coordination flow through the PM?

**Investigate:**
- Phase 1 Rule 5 prohibits peer delegation via SendMessage. Should this change for Phase 2?
- Scenario: Engineer A finishes an interface. Engineer B needs to call it. Should A SendMessage B the interface spec? Or should A report to PM, PM forwards to B?
- PM-mediated coordination: clearer audit trail, PM maintains control, but adds latency and PM context load
- Peer coordination: faster, lower PM context, but harder to audit, risk of shadow workflows
- What does Claude Code's Agent Teams actually support? Can teammates see each other's task lists? Can they read each other's worktrees?
- What is the current SendMessage behavior? Can MPM intercept or log SendMessage events?

**Why this matters:** The coordination model determines whether teams scale or collapse. PM-mediated is safe but slow. Peer is fast but risky.

**Prior docs to read first:**
- `02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 5 (peer-to-peer risk matrix: unauthorized delegation, collective unverified completion, file tracking omission, shadow workflow)
- `02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 6 (what CANNOT be enforced via prompts: SendMessage blocking listed explicitly)
- `04-phase-1.5/investigation/01_wp2_parallel_research.md` Section 2 ("What Code CANNOT Enforce" table — hook API limitation, no "reject" return path)

**Method:** Review Claude Code Agent Teams documentation/behavior. Review TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 5 (peer-to-peer risk matrix). Run an experiment with 2 teammates and observe SendMessage behavior.

### RQ8: Rollback and Recovery

**Question:** What happens when a teammate fails, and how does the team recover?

**Investigate:**
- Researcher fails: PM gets partial results. Manageable (Phase 1 handles this).
- Engineer fails: Worktree may contain partial/broken code. What happens to the worktree? Can it be discarded safely? What if other engineers depend on its output?
- QA fails: Tests are incomplete. PM doesn't know if the feature works. What's the recovery?
- Teammate timeout: Agent Teams has timeout behavior. What happens to the worktree when a teammate times out mid-edit?
- Can the PM "restart" a failed teammate? Or must it be a new spawn with a new worktree?
- What is the maximum acceptable failure rate before the PM should abort the team and fall back to sequential?

**Why this matters:** Phase 1 Research failures are low-risk (read-only, no state to clean up). Phase 2 Engineering failures leave state behind (worktrees, partial commits, broken files).

**Prior docs to read first:**
- RQ1 findings (worktree lifecycle — must complete first)
- `03-phase-1/02_parallel_research_design.md` Section 5 (fallback protocol: teammate spawn fails, teammate fails mid-work)
- `src/claude_mpm/hooks/claude_hooks/hook_handler.py` lines 794-842 (process lifecycle — each hook is a fresh process, relevant to understanding what state survives a teammate crash)

**Method:** Design analysis + experiment. Deliberately cause an Engineer teammate to fail mid-task and observe worktree state.

---

## Research Execution Plan

### Ordering and Dependencies

```
RQ1 (Worktree mechanics) ──────────┐
                                    ├── RQ2 (File conflicts) ──── RQ3 (Build verification)
RQ7 (SendMessage coordination) ────┘                                     │
                                                                         v
RQ4 (Team compositions) ──── RQ5 (PM orchestration) ──── Phase 2 Plan
                                                                         ^
RQ6 (Protocol extensions) ──── RQ8 (Rollback/recovery) ─────────────────┘
```

**Parallel group 1** (can run simultaneously):
- RQ1: Worktree mechanics (experiment)
- RQ4: Team composition patterns (design analysis)
- RQ6: Protocol extensions (design analysis)
- RQ7: SendMessage coordination (experiment + analysis)

**Sequential after group 1:**
- RQ2: File conflicts (depends on RQ1 worktree findings)
- RQ5: PM orchestration (depends on RQ4 compositions)
- RQ8: Rollback/recovery (depends on RQ1 worktree findings)

**Final synthesis:**
- RQ3: Build verification (depends on RQ2 conflict resolution approach)

### Estimated Effort

| RQ | Type | Effort | Dependencies |
|----|------|--------|-------------|
| RQ1 | Experiment + analysis | 0.5 days | None |
| RQ2 | Experiment + analysis | 1 day | RQ1 |
| RQ3 | Design analysis | 0.5 days | RQ2 |
| RQ4 | Design analysis | 0.5 days | None |
| RQ5 | Analysis + extrapolation | 0.5 days | RQ4, Phase 1.5 Gate 2 data |
| RQ6 | Design + measurement | 0.5 days | None |
| RQ7 | Experiment + analysis | 0.5 days | None |
| RQ8 | Experiment + design | 0.5 days | RQ1 |
| **Total** | | **~4-5 days** | |

With parallelization: ~3 days wall-clock.

### Deliverables

Each RQ produces a findings document in `docs-local/mpm-agent-teams/05-phase-2-research/`:

| File | Content |
|------|---------|
| `01_worktree_mechanics.md` | RQ1 findings: how worktrees work, experiment results |
| `02_file_conflicts.md` | RQ2 findings: conflict scenarios, detection, resolution |
| `03_build_verification.md` | RQ3 findings: integration testing protocol |
| `04_team_compositions.md` | RQ4 findings: valid compositions, anti-patterns |
| `05_pm_orchestration.md` | RQ5 findings: orchestration complexity, context limits |
| `06_protocol_extensions.md` | RQ6 findings: role-specific rules, token budget |
| `07_sendmessage_coordination.md` | RQ7 findings: peer vs PM-mediated, experiment results |
| `08_rollback_recovery.md` | RQ8 findings: failure modes, worktree cleanup, recovery |
| `09_phase2_implementation_plan.md` | Synthesized implementation plan (the final output) |

---

## Gate: Phase 1.5 Must Pass First

This research plan does NOT execute until Phase 1.5 gates pass:

| Gate | Required Result | Why It Blocks Phase 2 |
|------|----------------|----------------------|
| Gate 1 (Compliance) | 95% CI lower bound > 70% at all strata | If Research teammates can't follow protocol, Engineering teammates won't either |
| Gate 2 (Context) | >= 20% reduction OR claim dropped | If context relief is a myth, Phase 2's larger teams will hit context limits faster |
| Gate 3 (Env var) | Auto-detection working | Phase 2 builds on the same activation mechanism |

**If Gate 1 fails:** Fix protocol compliance first. Phase 2 adds complexity; compliance must be solid on the simpler case before attempting the harder one.

**If Gate 2 fails but claim dropped:** Phase 2 can proceed, but PM orchestration complexity (RQ5) becomes more critical — PM context will be the binding constraint.

---

## Risks to Phase 2 Research

| Risk | Severity | Mitigation |
|------|----------|------------|
| Worktree isolation doesn't handle merge conflicts | HIGH | If true, Phase 2 scope shrinks to "non-overlapping files only" which reduces value significantly |
| Claude Code Agent Teams API changes | HIGH | 6-month sunset clause from Phase 1 still applies |
| PM context insufficient for 5+ teammates | MEDIUM | RQ5 investigates; may limit team size or require multi-phase orchestration |
| SendMessage not interceptable by MPM | MEDIUM | RQ7 investigates; may force PM-mediated-only coordination |
| Phase 1.5 gates don't pass | HIGH | Phase 2 research is blocked entirely; fix Phase 1.5 first |
| Engineering spike reveals unsolvable merge problem | HIGH | If 2 Engineers can't safely merge, Phase 2 reduces to "isolated subsystems only" |

---

## Success Criteria for This Research

The research is complete when:

1. All 8 RQ documents are written with concrete findings (not speculation)
2. At least 2 RQs include hands-on experiment results (RQ1 and one of RQ2/RQ7/RQ8)
3. The synthesized implementation plan (09_phase2_implementation_plan.md) exists and covers:
   - Supported team compositions with rationale
   - Worktree merge strategy
   - Integration testing protocol
   - PM orchestration protocol changes
   - TEAMMATE_PROTOCOL extensions
   - Estimated effort and timeline
   - Go/No-Go recommendation based on findings
4. A devil's advocate review has been performed on the implementation plan
