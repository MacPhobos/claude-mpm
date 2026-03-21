# Phase 1.5: WP2 + WP5 Completion

**Issue:** #290
**Phase:** 1.5 (Gate Qualification)
**Date:** 2026-03-20
**Branch:** mpm-teams
**Prerequisite:** Phase 1 code changes complete (WP1, WP3, WP4 done)
**Success Criteria:** All three Phase 1 gates evaluable; clear path to Phase 2

---

## What Phase 1.5 Delivers

Phase 1 shipped the code foundation (auto-detection, protocol injection, PM instructions). Phase 1.5 completes the remaining work packages and produces the evidence needed to evaluate Phase 1 gates.

Two work packages:
1. **WP2 Completion:** Remove the 3-teammate cap, add code-level observability (role violation logging), add fast unit tests, update PM instructions
2. **WP5 Implementation:** Build compliance measurement infrastructure (structured logging, audit script, test battery), create `make test-agent-teams` target

---

## Design Decisions

### Decision 1: No Teammate Count Ceiling

The original Phase 1 plan imposed a maximum of 3 Research teammates. This constraint is removed. The PM should spawn as many research teammates as the task decomposes into independent questions. The practical ceiling is decomposition quality, not an arbitrary number.

**Rationale:** Artificial caps prevent the PM from fully utilizing Agent Teams for large investigations (security audits, architecture reviews, multi-subsystem analysis). The value of parallel research scales with the number of truly independent questions.

**Replacement guidance:** "Spawn one Research teammate per independent question. If you cannot articulate a distinct scope boundary for each teammate, do not spawn."

### Decision 2: Test Battery Separation

Testing splits into two categories with different execution models:

| Category | Location | Runner | In `make test`? | Requires LLM? |
|----------|----------|--------|:---:|:---:|
| **Unit tests** (fast, deterministic) | `tests/hooks/` | `make test` (pytest -n auto) | Yes | No |
| **Agent Teams battery** (LLM, slow) | `tests/manual/agent_teams_battery/` | `make test-agent-teams` (pytest -n 0) | No | Yes |

The `tests/manual/` directory is already in `norecursedirs` in pyproject.toml, so battery tests are automatically excluded from `make test`.

### Decision 3: Compliance Logging Architecture

A new `_compliance_log()` function writes structured JSON lines to `~/.claude-mpm/compliance/agent-teams-{date}.jsonl`. This is:
- Always-on (not DEBUG-gated) but only fires when Agent Teams injection occurs
- Machine-parseable (JSON lines, not free text)
- Durable (user home directory, not /tmp/)
- Separate from debug logging (_log) to avoid noise

---

## Work Package Summary

### WP2: Parallel Research Pattern Completion
**Effort:** 1 day

| Task | Type | Detail |
|------|------|--------|
| Remove 3-teammate cap from PM_INSTRUCTIONS.md | Text edit | 2 locations: "2-3 teammates" header + anti-pattern line |
| Remove 3-teammate cap from design doc | Text edit | 02_parallel_research_design.md Section 3 table |
| Add role violation logging | Code | Log warning when subagent_type != "research" in Agent Teams call |
| Add protocol sync test | Test | `test_protocol_matches_source_of_truth()` |
| Add role violation logging tests | Test | 2 tests: warning logged, injection still proceeds |
| Update 02_parallel_research_design.md | Text | Replace cap with decomposition-quality heuristic |

### WP5: Compliance Measurement Infrastructure
**Effort:** 2-3 days

| Task | Type | Detail |
|------|------|--------|
| Implement `_compliance_log()` function | Code | JSON lines writer to ~/.claude-mpm/compliance/ |
| Wire compliance logging into event handlers | Code | Fire on injection (PreToolUse) and completion (TaskCompleted) |
| Build audit script | Script | `scripts/audit_agent_teams_compliance.py` with Clopper-Pearson CI calculation |
| Design 35-task test battery | Design | 10 trivial + 10 medium + 10 complex + 5 adversarial |
| Build battery runner | Script | `tests/manual/agent_teams_battery/battery_runner.py` |
| Add `make test-agent-teams` Makefile target | Config | Invokes battery runner with -n 0 |
| Add compliance logging unit tests | Test | Validate JSON format, field presence, audit calculations |
| Add compliance log path configuration | Code | Environment variable or config for log directory |

---

## Testing Strategy

### Fast Tests (in `make test`)
These run in the existing pytest suite with -n auto parallelization:

1. **Role violation logging** (2 tests) — Tests warning log on non-research subagent_type, injection still proceeds
2. **Protocol sync** (1 test) — Verifies TEAMMATE_PROTOCOL matches TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 3
3. **Compliance log format** (3-4 tests) — Validates JSON line structure, required fields, file creation
4. **Audit script calculations** (3-4 tests) — Validates Clopper-Pearson CI on known inputs (n=30 k=30, n=30 k=27, etc.)
5. **Teammate counting from JSONL** (3 tests) — Validates audit script's ability to count teammates per team_name from compliance log records

Total: ~12-14 new fast tests added to the regular suite.

> **Design note (amendment from devil's advocate review):** In-memory teammate counting
> was originally proposed for `TeammateContextInjector._team_counts`. This was removed
> because each hook invocation is a **fresh Python process** — the dict resets every time
> and never accumulates across teammate spawns. Teammate counting is instead derived from
> the compliance log JSONL by the audit script, which reads the persistent file.

### Agent Teams Battery (in `make test-agent-teams`)
These require Claude Code with Agent Teams enabled. Run manually, never in CI:

1. **Task classification battery** (35 tasks) — Tests PM decision-making: when to spawn teams vs single agent
2. **Protocol compliance scoring** — Scores teammate output against 5 criteria per the Phase 0 Section 7 framework
3. **A/B injection comparison** (within the 35 tasks) — 10 runs with injection disabled as control group
4. **Adversarial scenarios** — Tasks designed to induce protocol violations (ambiguity, conflicting constraints, induced failure)

Battery output: compliance JSONL log + human-readable report with per-stratum CI calculations.

---

## Gate Evaluation Path

| Gate | What Phase 1.5 Delivers | How to Evaluate |
|------|------------------------|-----------------|
| Gate 1 (Compliance n>=30) | Compliance log infrastructure + audit script + test battery | Run `make test-agent-teams`, then `python scripts/audit_agent_teams_compliance.py --gate` |
| Gate 2 (Context 20% reduction) | Token measurement hooks in battery runner | Compare token counts between Task tool and Agent Teams conditions in battery output |
| Gate 3 (Env var elimination) | Already 2/3 passed; add `mpm doctor` check if time permits | Run `mpm doctor` and verify Agent Teams status line |

---

## Timeline

| Day | Work | Deliverable |
|-----|------|-------------|
| 1 | WP2: Cap removal, role logging, unit tests | PM_INSTRUCTIONS.md updated, 3 new fast tests |
| 2 | WP5: Compliance log function, event handler wiring, unit tests | _compliance_log() working, 7 new fast tests |
| 3 | WP5: Audit script, battery design, Makefile target | `make test-agent-teams` functional, audit script ready |
| 4 | Battery execution (if Agent Teams available) + gate evaluation | Gate 1/2/3 results documented |

---

## Constraints

- All unit tests must be fast and deterministic (no network, no LLM, no subprocess)
- All unit tests must pass with `make test` (pytest -n auto)
- Agent Teams battery runs only via `make test-agent-teams` (never auto-collected)
- No artificial teammate count ceiling — PM decides based on decomposition quality
- Compliance logging must not impact hook performance (< 1ms overhead)
- Battery runner must work with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set

---

## File Index

| File | Purpose |
|------|---------|
| `00_phase1.5_plan.md` | This document |
| `01_wp2_parallel_research.md` | WP2 investigation: cap removal, code enforcement, test design |
| `02_wp5_compliance_measurement.md` | WP5 investigation: logging, audit script, battery design |
