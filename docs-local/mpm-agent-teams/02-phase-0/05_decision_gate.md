# Phase 0 Decision Gate: Go / No-Go Framework

**Purpose:** Define the criteria and process for deciding whether to proceed to Phase 1 after Phase 0 experiments complete.
**Decision maker:** Project owner
**Input:** Results from Experiments 1-4

---

## Decision Framework

```
                    Experiment Results
                          |
                    ┌─────┴─────┐
                    |  Critical  |
                    |  Criteria  |
                    └─────┬─────┘
                          |
              ┌───── ALL PASS? ─────┐
              |                     |
             YES                   NO
              |                     |
        ┌─────┴─────┐        ┌─────┴─────┐
        | Supporting |        |   SHELVE   |
        |  Criteria  |        | Improve    |
        └─────┬─────┘        | existing   |
              |               | patterns   |
         MAJORITY             └────────────┘
          PASS?
         /     \
       YES     NO
        |       |
   ┌────┴───┐ ┌┴──────────┐
   |   GO   | |  GO WITH   |
   | Phase 1| | CONDITIONS |
   └────────┘ └────────────┘
```

---

## Critical Criteria (ALL must pass)

These are binary pass/fail. If ANY fails, the integration is shelved.

| # | Criterion | Source | Pass Threshold | Fail Action |
|---|-----------|--------|---------------|-------------|
| C1 | Teammate context injection works | Exp. 1, Test 2 | >= 70% behavioral compliance improvement over baseline | SHELVE — fundamental mechanism doesn't work |
| C2 | Token overhead acceptable | Exp. 1, Test 3 | < 5,000 tokens per teammate spawn | SHELVE — cost of injection exceeds value |
| C3 | Circuit breakers classifiable | Exp. 2 | All 10 CBs assigned to a tier with no gaps | SHELVE — can't maintain safety guarantees |
| C4 | CB#3 (evidence) compliance | Exp. 2, Test 1 | >= 70% of teammates provide verifiable evidence | SHELVE — verification chain broken |
| C5 | PreToolUse intercepts Agent tool | Exp. 3, Test 5 | Yes, with modifiable tool_input | SHELVE — no injection mechanism available |

**Rationale for 70% threshold (not 90%):** This is Phase 0 — a proof of concept. 70% demonstrates the mechanism works. Phase 1 will iterate on prompt optimization to reach 90%+.

---

## Supporting Criteria (MAJORITY should pass)

These are graded. A majority passing (>= 4 of 7) indicates sufficient value to proceed.

| # | Criterion | Source | Pass Threshold | Weight |
|---|-----------|--------|---------------|--------|
| S1 | Per-teammate model selection works | Exp. 4, Test A1 | Model parameter overrides file default | HIGH |
| S2 | Mixed-model team completes tasks | Exp. 4, Test A2 | All teammates succeed including Haiku | MEDIUM |
| S3 | PM context relief measurable | Exp. 4, Test B2 | >= 20% reduction vs Task tool | HIGH |
| S4 | TeammateIdle hook fires | Exp. 3, Test 1 | Event received with correct data | MEDIUM |
| S5 | TaskCompleted hook fires | Exp. 3, Test 2 | Event received with correct data | MEDIUM |
| S6 | Peer delegation resistance | Exp. 2, Test 3 | >= 70% resist peer delegation | HIGH |
| S7 | Non-team invocation unaffected | Exp. 1, Test 4 | 0% regression | HIGH |

---

## Decision Outcomes

### GO — Proceed to Phase 1

**Conditions:** All 5 critical criteria pass AND >= 4 of 7 supporting criteria pass.

**Next steps:**
1. Create Phase 1 plan (minimal integration for parallel research only)
2. Productionize PreToolUse context injection (feature-flagged)
3. Deploy TEAM_CIRCUIT_BREAKER_PROTOCOL.md
4. Update PM_INSTRUCTIONS.md with Agent Teams awareness
5. Target: parallel Research teammates as first supported pattern

**Phase 1 scope:**
- PM can spawn Research teammates for parallel exploration
- Teammates receive context injection via PreToolUse hook
- Team lead (PM) maintains verification gates at team boundary
- Fallback: if `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` absent, use existing `run_in_background`
- No user-visible configuration changes

### GO WITH CONDITIONS — Proceed with Constraints

**Conditions:** All 5 critical criteria pass BUT only 2-3 of 7 supporting criteria pass.

**Constraints to apply:**
- If S1/S2 fail: Lock all teammates to Sonnet (no mixed-model optimization)
- If S3 fails: Document that context relief is not yet proven; proceed for peer coordination value only
- If S4/S5 fail: Fix hook handlers first; no Phase 1 until hooks validated
- If S6 fails: Restrict to sequential task assignment only (no parallel teammates with peer messaging)
- If S7 fails: Isolate injection to team sessions only; verify isolation before proceeding

**Next steps:** Same as GO but with documented constraints limiting Phase 1 scope.

### SHELVE — Do Not Proceed

**Conditions:** Any critical criterion fails.

**Next steps:**
1. Document what failed and why
2. Invest in improving existing patterns:
   - Better result aggregation for `run_in_background` agents
   - Shared output directory convention for parallel worktree agents
   - PM-mediated coordination protocol (PM relays between background agents)
   - Document "MPM Parallel Agents" pattern as the official approach
3. Revisit when:
   - Claude Code adds parent context inheritance for teammates
   - Agent Teams exits experimental status
   - A new injection mechanism becomes available

---

## Evidence Collection Template

Each experiment produces a results document. The decision gate reviewer collects:

```markdown
# Phase 0 Decision Gate Evidence

## Critical Criteria Results

### C1: Context Injection Compliance
- Baseline compliance: ___%
- Post-injection compliance: ___%
- Improvement: ___%
- PASS / FAIL (threshold: >= 70% improvement)

### C2: Token Overhead
- Per-teammate overhead: ___ tokens
- 3-teammate total: ___ tokens
- % of PM context: ___%
- PASS / FAIL (threshold: < 5,000 per teammate)

### C3: CB Classification
- CBs classified: ___/10
- Gaps: [list]
- PASS / FAIL (threshold: 10/10)

### C4: CB#3 Evidence Compliance
- Teammates providing evidence: ___/___
- Compliance rate: ___%
- PASS / FAIL (threshold: >= 70%)

### C5: PreToolUse Intercept
- Agent tool intercepted: YES / NO
- tool_input modifiable: YES / NO
- Modified prompt reaches teammate: YES / NO
- PASS / FAIL

## Supporting Criteria Results
[Same format for S1-S7]

## Decision
- Critical: ___/5 PASS
- Supporting: ___/7 PASS
- OUTCOME: GO / GO WITH CONDITIONS / SHELVE
- Conditions (if applicable): [list]
```

---

## Timeline

| Day | Activity | Output |
|-----|----------|--------|
| 1 | Experiment 1 infrastructure + Experiment 2 protocol design | Code + protocol draft |
| 2 | Experiment 1 live testing + Experiment 2 validation | Test results |
| 3 | Experiment 1 deploy-time testing + comparison | Test results |
| 4 | Experiment 3 hook validation + Experiment 4 model routing | Test results |
| 5 | Experiment 4 context window + results compilation | Test results |
| 6 | Decision gate evidence collection + review | **GO / NO-GO DECISION** |

**Total: ~6 working days**

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Agent Teams API changes during Phase 0 | LOW | HIGH | Complete Phase 0 within 2 weeks to minimize window |
| PreToolUse can't modify Agent tool input | MEDIUM | CRITICAL | Test this FIRST (Day 1). If fails, pivot to Method B immediately. |
| LLM ignores injected protocol | MEDIUM | HIGH | Iterate on prompt strength. If < 50% compliance, SHELVE. |
| Claude Code version upgrade breaks hooks | LOW | MEDIUM | Pin Claude Code version for Phase 0 duration. |
| Phase 0 results are inconclusive | MEDIUM | MEDIUM | Define "inconclusive" as SHELVE. Don't proceed on ambiguous data. |

---

## Appendix: Phase 1 Preview (If GO)

If the decision gate produces GO, Phase 1 focuses on:

1. **Productionize context injection** — PreToolUse hook in production, feature-flagged
2. **Parallel Research pattern** — PM spawns 2-3 Research teammates for complex investigations
3. **Team lead verification** — PM collects teammate SendMessage results, applies QA gate
4. **Graceful fallback** — If Agent Teams unavailable, fall back to `run_in_background`
5. **Monitoring** — Dashboard shows teammate status via TeammateIdle/TaskCompleted
6. **Documentation** — Update PM_INSTRUCTIONS.md with Agent Teams delegation patterns

Phase 1 does NOT include:
- Parallel QA (needs QA aggregation protocol)
- Parallel Engineering (needs file conflict resolution)
- Team lead as a separate role (PM remains PM)
- Memory sharing between teammates
- User-facing Agent Teams configuration
