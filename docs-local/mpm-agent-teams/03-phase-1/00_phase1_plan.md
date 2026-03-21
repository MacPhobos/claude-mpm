# Phase 1: Agent Teams Integration — Parallel Research

**Issue:** #290
**Phase:** 1 (Minimal Viable Integration)
**Date:** 2026-03-20
**Status:** APPROVED with mandatory gates
**Prerequisite:** Phase 0 complete (GO decision)

---

## What Phase 1 Delivers

One capability: **PM can spawn 2-3 parallel Research teammates for complex investigations.**

That's it. No parallel Engineering. No parallel QA. No mixed teams. One pattern, tightly scoped, with graceful fallback when Agent Teams is unavailable.

---

## What Phase 1 Does NOT Deliver

Explicitly out of scope (deferred to Phase 2+):
- Parallel Engineer teammates (file conflict resolution not designed)
- Parallel QA teammates (aggregation protocol not designed)
- Mixed-role teams (Research + Engineer + QA)
- Teams larger than 3 teammates
- Memory sharing between teammates
- User-facing Agent Teams configuration
- Dashboard team visualization (hooks registered, display deferred)

---

## Mandatory Gates (From Devil's Advocate)

The devil's advocate identified three conditions Phase 1 must satisfy before declaring success. These are non-negotiable.

### Gate 1: Compliance Measurement (n>=30)

Phase 0 validated with n=3 — statistically insufficient (95% CI: 29-100%). Phase 1 must:

- Collect **>= 30 teammate completions** across 3 strata:
  - 10 trivial tasks (< 3 min, clear scope)
  - 10 medium tasks (10-15 min, moderate ambiguity)
  - 10 complex tasks (30+ min, broad scope, judgment required)
- Measure per-response: evidence present, forbidden phrases absent, file manifest complete
- Calculate compliance rate with 95% CI per stratum
- **Pass:** Lower bound of 95% CI > 70% at ALL strata
- Include 5 adversarial test cases (ambiguity, induced failure, conflicting constraints)

*Rationale: [05_devils_advocate.md, Concern 1]*

### Gate 2: Context Window Measurement

Context window relief was a primary motivation but was never quantitatively measured. Phase 1 must:

- Run A/B benchmark: same 5-task workflow via Task tool vs Agent Teams
- Record actual token consumption (or proxy: conversation length, response quality degradation point)
- **Pass:** Agent Teams shows >= 20% context reduction OR we drop "context relief" from the motivation list and proceed on peer coordination value alone

*Rationale: [05_devils_advocate.md, Concern 4]*

### Gate 3: Env Var Elimination

The Phase 0 activation hack (prefixing hook command) is fragile. Phase 1 must:

- Implement auto-detection: read `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` at runtime
- Keep `CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION` as manual override only
- Add `mpm doctor` check for Agent Teams status
- **Pass:** Injection activates automatically without settings.json modification

*Implementation: [01_context_injection_production.md, Section 1]*

---

## Implementation Work Packages

### WP1: Productionize Context Injection
**Effort:** 1 day | **Doc:** [01_context_injection_production.md](01_context_injection_production.md)

- Replace env var hack with auto-detection of Anthropic's Agent Teams flag
- Synchronize TEAMMATE_PROTOCOL constant with TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 3
- Move validation logging from `/tmp/` to MPM's standard log directory
- Add compliance logging (structured, queryable)

### WP2: Parallel Research Pattern
**Effort:** 1-2 days | **Doc:** [02_parallel_research_design.md](02_parallel_research_design.md)

- Define decision criteria: when PM uses teams vs standard delegation
- Define orchestration flow: decompose, spawn, collect, verify, synthesize
- Define fallback: transparent degradation to `run_in_background`
- Define constraints: max 3 teammates, research only, no sequential dependencies
- Define result validation: evidence checking, conflict resolution

### WP3: PM_INSTRUCTIONS.md Update
**Effort:** 0.5 days | **Doc:** [03_pm_instructions_changes.md](03_pm_instructions_changes.md)

- Add "Agent Teams: Parallel Research" section (~35 lines)
- Add delegation table row, model routing line, CB reference
- Total growth: ~41 lines (within 50-line budget)

### WP4: Hook Registration
**Effort:** 1 day | **Doc:** [04_hook_registration.md](04_hook_registration.md)

- Register TeammateIdle and TaskCompleted in hook installer
- Ensure hooks survive `claude-mpm agents deploy` regeneration
- Extend handlers beyond current stubs (log + dashboard + optional team lead notification)
- Version-gate to Claude Code >= 2.1.47

### WP5: Compliance Measurement Infrastructure
**Effort:** 1 day | No separate doc — driven by Gate 1 requirements

- Create structured compliance log format
- Build compliance audit script (counts per stratum, calculates CI)
- Design 30-task test battery (10 trivial, 10 medium, 10 complex, 5 adversarial)
- Run test battery and record results

**Total estimated effort: 5-6 days**

---

## Devil's Advocate Assessment (Integrated)

The critic raised 8 concerns. Here's how this plan addresses each:

| # | Concern | Severity | Addressed By |
|---|---------|----------|-------------|
| 1 | n=3 sample size meaningless | HIGH | Gate 1: n>=30 compliance measurement |
| 2 | Env var hack fragile | MEDIUM | Gate 3: auto-detection, eliminate hack |
| 3 | Parallel research value questionable | MEDIUM | Tight scope validates cheaply; if value unclear after 30 runs, reassess |
| 4 | Context window never measured | HIGH | Gate 2: A/B benchmark with actual measurements |
| 5 | 500 tokens lost in 59KB noise | MEDIUM | Include A/B test: WITH vs WITHOUT injection in the 30-run battery |
| 6 | Experimental API risk | HIGH | 6-month sunset clause; if still experimental by then, shelve |
| 7 | Engineers excluded | HIGH | Phase 2 contract: design begins within 2 weeks of Phase 1 completion |
| 8 | Cost at scale | LOW | Monitor during 30-run battery; report tokens/teammate |

### Non-Blocking Recommendations Accepted

- **6-month sunset:** If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is still prefixed with `EXPERIMENTAL_` after 6 months, revert Phase 1 and improve existing parallel patterns
- **Phase 2 contract:** Engineering support design document due within 2 weeks of Phase 1 gate passage
- **A/B protocol test:** Include 10 runs WITHOUT injection in the 30-run battery to isolate marginal effect of the Teammate Protocol vs BASE_AGENT.md alone
- **Engineering spike:** One experiment with 2 parallel Engineers on non-overlapping files, documented but not shipped

---

## Risks

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| Compliance drops at n=30 vs n=3 | HIGH | Gate 1 blocks shipping if CI lower bound < 70% | Must pass |
| Auto-detection doesn't survive all edge cases | MEDIUM | Manual override remains as fallback | Designed |
| PM spawns teams inappropriately | MEDIUM | Explicit decision criteria + anti-patterns in PM_INSTRUCTIONS.md | Designed |
| Agent Teams API changes mid-Phase-1 | HIGH | Graceful fallback to `run_in_background`; 6-month sunset | Accepted |
| Teammates produce redundant results | MEDIUM | PM decomposes into non-overlapping questions with scope boundaries | Designed |
| Context window improvement not measurable | HIGH | Gate 2: measure or drop the claim | Must pass |

---

## Timeline

| Day | Work | Gate |
|-----|------|------|
| 1 | WP1: Productionize injection (auto-detect, logging) | Gate 3 |
| 2 | WP4: Hook registration + WP3: PM_INSTRUCTIONS.md update | — |
| 3 | WP2: Parallel research pattern implementation | — |
| 4 | WP5: Compliance infrastructure + begin test battery | — |
| 5 | Complete test battery (30 runs) + A/B context benchmark | Gates 1, 2 |
| 6 | Results compilation, gate evaluation, decision | All gates |

---

## File Index

| File | Lines | Purpose |
|------|-------|---------|
| `00_phase1_plan.md` | — | This document — master plan |
| `01_context_injection_production.md` | 236 | Productionize injection mechanism |
| `02_parallel_research_design.md` | 276 | Parallel research pattern design |
| `03_pm_instructions_changes.md` | 134 | PM_INSTRUCTIONS.md diff-ready spec |
| `04_hook_registration.md` | 297 | Register Agent Teams hooks |
| `05_devils_advocate.md` | 571 | Critical assessment with 3 mandatory gates |
