# Experiment 4 Results: Model Routing & Context Window Validation

**Date:** 2026-03-20
**Status:** PARTIAL — observational evidence from live session, formal benchmarks pending

---

## Part A: Per-Teammate Model Routing

### Evidence from This Session

This Phase 0 execution session used mixed-model teammate spawning:

| Teammate | Requested Model | Task | Completed Successfully? |
|----------|----------------|------|------------------------|
| capabilities-researcher | sonnet | API research | Yes |
| architecture-analyst | sonnet | Architecture analysis | Yes |
| devils-advocate | sonnet | Challenge analysis | Yes |
| phase0-planner | sonnet | Codebase research | Yes |
| injector-engineer | opus | Build context injector + tests + logging | Yes |
| protocol-writer | opus | Write CB protocol document | Yes |

### Observations

1. **Model parameter accepted by Agent tool** — All `model` parameters were accepted without error
2. **Quality scaling visible** — Opus agents (injector-engineer, protocol-writer) produced more detailed, structured output with deeper codebase analysis than Sonnet agents. This supports the cost-optimization thesis: use Opus where quality matters most, Sonnet for standard research.
3. **Haiku not tested in this session** — No ops/documentation tasks warranted Haiku. This remains to be validated.

### Preliminary Assessment

| Criterion | Status | Evidence |
|-----------|--------|----------|
| S1: Model override works | **PASS** | 6 teammates spawned with explicit model params, all completed |
| S2: Mixed-model team completes | **PASS** | Mixed Sonnet + Opus team completed all 5 tasks |

---

## Part B: Context Window Relief

### Observational Evidence

This session has been running for an extended period with multiple delegation rounds:

**Session history:**
1. Investigation team (3 parallel researchers) — received summary messages via teammate notifications
2. Phase 0 research (1 researcher) — received summary message
3. Phase 0 execution (2 parallel agents + 1 sequential) — received summary messages

**Key observation:** We are deep into a complex multi-phase workflow (investigation -> planning -> execution) with 7+ teammate delegations, and the PM (team lead) context has NOT degraded. We are still producing coherent, contextually-aware responses.

**Comparison point:** In a standard Task tool session with this many sequential delegations (7+), the PM context would typically show signs of saturation (losing earlier context, repetitive responses, missing details).

### Why This Evidence is Suggestive but Not Conclusive

1. We don't have exact token counts per teammate message vs Task tool return
2. The session has user interactions between delegations (which adds to context regardless)
3. No controlled A/B comparison was conducted
4. The Agent Teams messages we received were summaries, not full agent output — this IS the predicted mechanism for context relief

### Preliminary Assessment

| Criterion | Status | Evidence |
|-----------|--------|----------|
| S3: PM context relief measurable | **LIKELY PASS** | Sustained coherent orchestration through 7+ delegations across 2 teams. Teammate messages are targeted summaries, not full output. |

---

## Formal Benchmark Plan (Remaining Work)

To produce rigorous evidence, a controlled benchmark is needed:

### A/B Test Protocol
1. **Condition A (Task tool):** 5 sequential delegations via standard MPM Task tool
   - Record: PM response quality at delegation #1, #3, #5
   - Record: Approximate context consumed per delegation
2. **Condition B (Agent Teams):** Same 5 tasks via Agent Teams teammates
   - Record: Same metrics
3. **Compare:** Context growth rate, PM quality degradation point

### Cost Benchmark
1. Run same 3-task workflow (Research -> Engineer -> QA) on:
   - All Sonnet (baseline)
   - Mixed model (Research:Sonnet, Engineer:Opus, QA:Sonnet, hypothetical Ops:Haiku)
2. Compare: Total token usage, total estimated cost

**Estimated effort:** 2-3 hours in dedicated session
