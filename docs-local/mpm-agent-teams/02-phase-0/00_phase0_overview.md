# Phase 0: Agent Teams Integration — Proof of Concept Plan

**Issue:** #290 — Integrate Anthropic Agent Teams with MPM orchestration
**Phase:** 0 (Proof of Concept — no production code)
**Date:** 2026-03-20
**Prerequisite:** Initial Investigation complete (see `01_initial_investigation/`)

---

## Purpose

Phase 0 validates that the two critical blockers identified in the initial investigation can be solved at acceptable cost before committing to integration work.

**This is a validation phase, not an implementation phase.** Deliverables are test results and protocol documents, not production features.

---

## Motivation (Why Agent Teams)

The primary motivations for integrating Agent Teams into MPM:

1. **Independent context windows** — Teammates operate in their own context, preventing PM context saturation during complex multi-phase workflows. Currently, every Task tool result returns into PM's context window.
2. **Per-teammate model selection** — Fine-grained cost optimization (Opus team lead, Sonnet researchers, Haiku ops) extending MPM's existing model routing to team-level granularity.
3. **Real-time peer coordination** — Teammates communicate directly, share discoveries mid-task, and redirect effort without round-tripping through PM.

---

## Critical Blockers to Validate

| # | Blocker | What We Must Prove | Experiment |
|---|---------|-------------------|------------|
| B1 | Teammate Context Gap | MPM behavioral protocols can be reliably injected into teammates at acceptable token cost | [Experiment 1](01_experiment_context_injection.md) |
| B2 | Circuit Breaker Integrity | A formal protocol can maintain verification chain integrity when agents communicate peer-to-peer | [Experiment 2](02_experiment_circuit_breaker_protocol.md) |

## Supporting Validations

| # | Validation | What We Must Prove | Experiment |
|---|-----------|-------------------|------------|
| V1 | Hook System Reality Check | TeammateIdle/TaskCompleted hooks actually fire in real Agent Teams sessions | [Experiment 3](03_experiment_hook_validation.md) |
| V2 | Model Routing Per-Teammate | Per-teammate model selection works and produces cost savings | [Experiment 4](04_experiment_model_routing.md) |
| V3 | Context Window Relief | Agent Teams measurably reduces PM context consumption vs Task tool | [Experiment 4](04_experiment_model_routing.md) |

---

## Experiments Summary

| Experiment | Document | Effort | Dependencies |
|-----------|----------|--------|-------------|
| 1. Context Injection PoC | [01_experiment_context_injection.md](01_experiment_context_injection.md) | 2-3 days | None |
| 2. Circuit Breaker Protocol | [02_experiment_circuit_breaker_protocol.md](02_experiment_circuit_breaker_protocol.md) | 1-2 days | None |
| 3. Hook Validation | [03_experiment_hook_validation.md](03_experiment_hook_validation.md) | 1 day | Exp. 1 (needs teammate session) |
| 4. Model & Context Validation | [04_experiment_model_routing.md](04_experiment_model_routing.md) | 1 day | Exp. 1 (needs teammate session) |

**Total estimated effort:** 5-7 days
**Can run in parallel:** Experiments 1+2 are independent. Experiments 3+4 depend on 1.

---

## Decision Gate

After all experiments complete, a formal go/no-go decision is made using criteria defined in [05_decision_gate.md](05_decision_gate.md).

```
Experiment 1 (Context Injection)     ──┐
Experiment 2 (CB Protocol)           ──┤
Experiment 3 (Hook Validation)       ──┼──> Decision Gate ──> Phase 1 or Shelve
Experiment 4 (Model & Context)       ──┘
```

**Three possible outcomes:**
1. **GO** — All critical criteria pass. Proceed to Phase 1 (minimal integration for parallel research).
2. **GO WITH CONDITIONS** — Critical criteria pass with caveats. Proceed to Phase 1 with specific constraints.
3. **SHELVE** — Any critical criterion fails. Invest in improving existing `run_in_background` patterns instead.

---

## Scope Boundaries

### In Scope for Phase 0
- PreToolUse hook modification for context injection testing
- Teammate behavioral compliance measurement
- Circuit breaker protocol document creation
- Hook event validation in live Agent Teams sessions
- Model routing and context window measurement
- Unit and integration tests for new hook behavior

### Out of Scope for Phase 0
- Production deployment of any Agent Teams integration
- Modifications to PM_INSTRUCTIONS.md for team orchestration
- QA aggregation protocol (Phase 1+)
- Team lead role definition (Phase 1+)
- Memory sharing mechanisms (Phase 1+)
- User-facing documentation or configuration

---

## Environment Requirements

```bash
# Required for all experiments
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Claude Code version
claude --version  # Must be >= 2.1.47 for Agent Teams hooks

# MPM version
claude-mpm --version  # Current: 5.10.9
```

---

## File Index

| File | Purpose |
|------|---------|
| `00_phase0_overview.md` | This document — plan overview and structure |
| `01_experiment_context_injection.md` | Experiment 1: Teammate context injection PoC |
| `02_experiment_circuit_breaker_protocol.md` | Experiment 2: Circuit breaker protocol for teams |
| `03_experiment_hook_validation.md` | Experiment 3: Validate Agent Teams hooks fire correctly |
| `04_experiment_model_routing.md` | Experiment 4: Model selection and context window validation |
| `05_decision_gate.md` | Go/no-go criteria and decision framework |
| `research_findings.md` | Technical research backing this plan |
