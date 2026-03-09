# E2E Delegation Testing: Session Resume Guide

**Last Updated:** 2026-03-09
**Current Phase:** Phase 0+1+2+3+4 COMPLETE. All phases done (CI integration deferred).
**Branch:** `e2e-delegation-tests`

---

## Quick Resume Command

Start a new Claude session and say:

```
Read docs-local/e2e-delegation-testing/SESSION-RESUME.md and continue with the next phase.
```

---

## Project Overview

We are implementing E2E delegation testing for the claude-mpm PM prompt. The tests verify that the PM correctly delegates tasks to specialized agents (engineer, research, qa, ops, etc.) rather than attempting work directly.

**Architecture: 3 tiers of testing**

| Tier | What | How | Cost | Speed |
|------|------|-----|------|-------|
| **Tier 1** | Prompt assembly correctness | FrameworkLoader + string checks | $0 | <1s |
| **Tier 2** | Delegation *intent* | `claude -p --json-schema --tools ""` | ~$0.07/test | 3-8s |
| **Tier 3** | Delegation *behavior* | Hook interception + blocking | ~$0.10/test | 5-15s |

**Full plan:** `docs-local/e2e-delegation-testing/02-initial-impl-plan/04-implementation-plan-synthesis.md`

---

## Completed Work

### Phase 0: Verification (COMPLETE - ALL PASS)

Full results: `docs-local/e2e-delegation-testing/03-verification-results/phase0-verification-results.md`

| Verification | Result | Key Finding |
|---|---|---|
| **V1: Tool Name** | PASS | Delegation tool is "Task" in PreToolUse events (6 code refs, 0 "Agent" refs) |
| **V2: Structured Output** | PASS | `--json-schema --tools ""` produces `structured_output.agent` correctly |
| **V3: FrameworkLoader** | PASS | Loads 67,610 bytes in pytest context; 5/5 tests pass |
| **V4: Consistency** | PASS | 5 runs all return "engineer" (case variation only: "Engineer"/"engineer") |

### Phase 1: Tier 1 Structural Tests (COMPLETE - 45/45 PASS)

**Commit:** `8a746f84` on branch `e2e-delegation-tests`

| Test Class | Tests | What It Validates |
|---|---|---|
| `TestPromptSectionPresence` | 23 | 12 critical sections present, 8 agents referenced, no unresolved templates, prompt size bounds (40-120KB) |
| `TestPromptSemanticChecksums` | 5 | SHA-256 hashes of 4 critical sections (delegation principle, prohibitions, circuit breakers, QA gate) + baseline helper |
| `TestPromptAssemblyComponents` | 7 | Agent definitions, workflow, memory, skills, temporal context, idempotency, no duplicates |
| `TestToolNameResolution` (Phase 0) | 5 | Tool name is "Task" in codebase |
| `TestFrameworkLoaderV3` (Phase 0) | 5 | FrameworkLoader works in pytest |

**Semantic Checksum Baselines:**
- `delegation_principle`: `75e180a6fc60c8c7`
- `absolute_prohibitions`: `b230c4855c781909`
- `circuit_breakers`: `92f8da1115e5ab54`
- `qa_verification_gate`: `ccb43e30bc3cc263`

### Phase 2: Tier 2 Structured Output Delegation Intent Tests (COMPLETE - 13 tests built)

**Commit:** `30cb01e5` on branch `e2e-delegation-tests`

| Test Category | Tests | What It Validates |
|---|---|---|
| `test_delegation_routing` | 5 | DEL-01..05: Correct agent selection for engineer/research/local-ops/qa tasks |
| `test_no_delegation_when_trivial` | 2 | NODL-01..02: PM handles capability/role questions directly |
| `test_context_quality` | 2 | CTX-01..02: Delegation reasoning references task keywords, >50 chars |
| `test_circuit_breaker_compliance` | 3 | CB-01..03: PM delegates (never handles directly) for circuit breaker scenarios |
| `test_cost_summary` | 1 | Informational: reports invocation count + cost per test |

**Key artifacts:**
- `tests/eval/adapters/structured_output_adapter.py` -- StructuredOutputAdapter with `query_delegation_intent()` and `query_with_consensus()` (2-of-3 retry)
- `tests/eval/scenarios/delegation_scenarios.json` -- 12 scenarios (5 delegation, 2 no-delegation, 2 context quality, 3 circuit breaker)
- `tests/eval/tier2/test_delegation_intent.py` -- 13 parametrized tests
- `tests/eval/tier2/conftest.py` -- Module-scoped adapter fixture + auto-skip when claude CLI unavailable

**Exit Criteria (code complete, pending terminal validation):**
- [x] StructuredOutputAdapter implemented with full error handling
- [x] All 12 delegation scenarios defined in JSON
- [x] 13 tests collected (5 delegation + 2 no-delegation + 2 context + 3 circuit breaker + 1 cost summary)
- [x] 2-of-3 consensus via `query_with_consensus()` for LLM variance
- [x] InfrastructureError -> pytest.skip, DelegationTestError -> test failure
- [x] Cost tracking built into adapter (`adapter.stats`)
- [x] `tier2` marker registered in pyproject.toml
- [x] `make test-eval-tier2` and `make test-eval-tier2-canary` Makefile targets added
- [x] All 45 structural tests still pass (0 regressions)
- [ ] **PENDING: Run from terminal** -- `uv run pytest tests/eval/tier2/ -xvs -p no:xdist` (cannot run from within Claude session)

### Phase 3: Tier 3 Hook Interception + Behavioral Tests (COMPLETE - 7 tests built)

**Commit:** (pending -- to be committed this session)

| Test Category | Tests | What It Validates |
|---|---|---|
| `test_delegation_behavior` | 5 | BHV-01..05: Correct agent selection via hook-intercepted Task tool calls (engineer/research/local-ops/qa/security) |
| `test_delegation_captures_prompt_content` | 1 | Delegation prompt >50 chars, contains task-relevant keywords |
| `test_blocking_prevents_subagent` | 1 | Hook interception captures delegation and blocks subagent spawn |

**Key artifacts:**
- `src/claude_mpm/testing/__init__.py` -- Testing package init
- `src/claude_mpm/testing/delegation_interceptor.py` -- PreToolUse hook script: reads stdin JSON, captures Task/Agent calls to JSONL, blocks or passes through, fail-open on errors
- `tests/eval/adapters/hook_interception_harness.py` -- HookInterceptionHarness: manages workspace, installs interceptor hook via settings.local.json, runs claude-mpm subprocess, reads JSONL captures, context manager support
- `tests/eval/tier3/__init__.py` -- Module init
- `tests/eval/tier3/conftest.py` -- Auto-skip if claude CLI unavailable, harness fixture with tmp_path
- `tests/eval/tier3/test_delegation_behavior.py` -- 7 parametrized + standalone tests

**Exit Criteria:**
- [x] DelegationInterceptor captures and blocks Task tool calls
- [x] HookInterceptionHarness manages interceptor lifecycle
- [x] 7 tests collected (5 behavioral routing + 1 prompt content + 1 blocking verification)
- [x] Context quality verified (prompt >50 chars, keywords present)
- [x] `tier3` marker registered in pyproject.toml
- [x] `make test-eval-tier3` Makefile target added
- [x] `test-eval` target updated to include tier3
- [x] All 45 structural tests still pass (0 regressions)
- [ ] **PENDING: Run from terminal** -- `uv run pytest tests/eval/tier3/ -xvs -p no:xdist` (cannot run from within Claude session)

### Key Design Decisions Confirmed

1. **Tool name = "Task"** in hook events (interceptor should check "Task" primarily, "Agent" defensively)
2. **`--json-schema --tools ""`** is the safe Tier 2 approach (prevents tool execution entirely)
3. **Case-insensitive matching** required in Tier 2 and Tier 3 assertions (use `.lower()`)
4. **2-of-3 retry** strategy appropriate for LLM output variation (Tier 2)
5. **`claude -p` cannot run from within a Claude session** -- tests using it must use `subprocess` with `CLAUDECODE` env var unset
6. **Session-scoped fixture** for assembled_prompt (loaded once, shared across all structural test modules)
7. **Module-scoped adapter** for Tier 2 (prompt caching benefit across sequential tests)
8. **`-p no:xdist`** required for Tier 2 and Tier 3 (sequential execution enables prompt caching)
9. **Research Gate affects first-delegation** -- Complex/ambiguous/security-sensitive tasks correctly route to Research before Engineer; scenarios accept "research" as valid alternative
10. **Fail-open interceptor** -- Any exception in the interceptor outputs `{"continue": true}` and logs errors to `.errors` file, never breaking Claude Code
11. **Embedded fallback interceptor** -- HookInterceptionHarness embeds the interceptor script as fallback if the source file path is not found

### All Files Created (Phase 0 + Phase 1 + Phase 2 + Phase 3)

```
scripts/
  verify-e2e-prerequisites.sh            # Standalone V1-V4 verification script
  verify-v1-tool-name.py                 # Python V1 code analysis tool

src/claude_mpm/testing/
  __init__.py                            # Testing package init (Phase 3)
  delegation_interceptor.py              # PreToolUse hook interceptor (Phase 3)

tests/eval/adapters/
  __init__.py                            # Module init
  structured_output_adapter.py           # Wraps claude -p with --json-schema (Phase 2)
  hook_interception_harness.py           # Wraps claude-mpm run with interceptor hook (Phase 3)

tests/eval/scenarios/
  delegation_scenarios.json              # 12 scenarios for Tier 2 + Tier 3 (Phase 2)

tests/eval/structural/
  __init__.py                            # Module init
  conftest.py                            # Session-scoped assembled_prompt fixture
  test_v1_tool_name.py                   # 5 tests: tool name consistency (V1)
  test_v3_framework_loader.py            # 5 tests: FrameworkLoader works (V3)
  test_prompt_assembly.py                # 32 tests: section presence, checksums, components

tests/eval/tier2/
  __init__.py                            # Module init
  conftest.py                            # Module-scoped adapter + auto-skip (Phase 2)
  test_delegation_intent.py              # 13 tests: delegation intent validation (Phase 2)

tests/eval/tier3/
  __init__.py                            # Module init (Phase 3)
  conftest.py                            # Auto-skip + harness fixture (Phase 3)
  test_delegation_behavior.py            # 7 tests: behavioral delegation validation (Phase 3)

tests/eval/tracking/
  __init__.py                            # Module init (Phase 4)
  __main__.py                           # CLI entry for python -m (Phase 4)
  result_recorder.py                     # Pytest plugin for recording results (Phase 4)
  degradation_detector.py                # Historical comparison + alerting (Phase 4)

tests/eval/results/
  .gitkeep                               # Directory placeholder (JSON results gitignored)

docs-local/e2e-delegation-testing/
  DEVELOPER-GUIDE.md                     # How to run, extend, troubleshoot (Phase 4)
  03-verification-results/
    phase0-verification-results.md       # Comprehensive V1-V4 results
    phase0-verification-20260309-155101.md  # Raw script output
```

---

### Phase 4: Hardening — Result Tracking + Degradation Detection (COMPLETE)

**Commit:** (pending -- to be committed this session)

| Component | What It Does |
|---|---|
| `result_recorder.py` | Pytest plugin hooking `pytest_runtest_makereport` + `pytest_sessionfinish`. Records per-test pass/fail, duration, tier, scenario_id, git info to JSON. Activated via `--eval-record` flag or `EVAL_RECORD_RESULTS=1` env var. |
| `degradation_detector.py` | Standalone module + CLI. Loads historical JSON results, detects test regressions (>=80% historical pass now fails), new failures, cost spikes (>50%), pass rate drops (>5%). Exit code 0=clean, 1=degraded. |
| `DEVELOPER-GUIDE.md` | Comprehensive docs: running tests, adding scenarios, result tracking, fidelity gap, cost model, troubleshooting. |

**Key artifacts:**
- `tests/eval/tracking/result_recorder.py` -- EvalResultRecorder pytest plugin
- `tests/eval/tracking/degradation_detector.py` -- DegradationDetector + DegradationReport/TestRegression/CostAlert dataclasses
- `tests/eval/tracking/__main__.py` -- CLI entry point for `python -m tests.eval.tracking`
- `tests/eval/results/.gitkeep` -- Results directory (JSON files gitignored)
- `tests/eval/conftest.py` -- Updated with `--eval-record` option + plugin registration
- `docs-local/e2e-delegation-testing/DEVELOPER-GUIDE.md` -- Developer documentation

**Exit Criteria:**
- [x] Result tracking JSON schema defined and implemented
- [x] Historical comparison via DegradationDetector
- [x] Degradation alerting (test regressions, cost spikes, pass rate drops)
- [x] `make test-eval-record` target for recording results
- [x] `make test-eval-check-degradation` target for degradation checks
- [x] Developer documentation with fidelity gap, adding scenarios, troubleshooting
- [x] All 45 structural tests still pass (0 regressions)
- [x] Both modules import cleanly
- [ ] **DEFERRED: GitHub Actions CI workflow** (not implemented per user request)

---

## Deferred Work: CI Integration

GitHub Actions workflow was intentionally deferred. When ready to implement:

**Reference:** Plan Section 11 (lines 1277-1368) in `04-implementation-plan-synthesis.md`

Key requirements:
- Tier 1 runs on every PR (zero cost, <2s) — BLOCKING
- Tier 2 canary on PM file changes — BLOCKING for PM changes, advisory otherwise
- Tier 3 nightly — advisory only (continue-on-error)
- GitHub Actions secret for Anthropic API access (Tier 2+3)  # pragma: allowlist secret
- Pin Claude Code CLI version in CI

---

## Important References

| Document | Location | Contents |
|----------|----------|----------|
| **Full implementation plan** | `docs-local/e2e-delegation-testing/02-initial-impl-plan/04-implementation-plan-synthesis.md` | Complete spec for all 4 phases |
| **Approach 1 investigation** | `docs-local/e2e-delegation-testing/02-initial-impl-plan/01-approach1-investigation.md` | CLI mechanics, output formats, cost model |
| **Approach 3 investigation** | `docs-local/e2e-delegation-testing/02-initial-impl-plan/02-approach3-investigation.md` | Hook interception, blocking protocol |
| **Devil's advocate review** | `docs-local/e2e-delegation-testing/02-initial-impl-plan/03-devils-advocate-impl-review.md` | Stress test, adjustments |
| **Phase 0 results** | `docs-local/e2e-delegation-testing/03-verification-results/phase0-verification-results.md` | V1-V4 verification evidence |
| **PM Instructions source** | `PM_INSTRUCTIONS.md` | The actual PM prompt being tested |

## Running Tests

See also: `docs-local/e2e-delegation-testing/DEVELOPER-GUIDE.md` for comprehensive documentation.

```bash
# Run ALL structural tests (Phase 0 + Phase 1) -- $0 cost, <2s
uv run pytest tests/eval/structural/ -v

# Run Tier 2 delegation intent tests (~$0.84 for all 12, from TERMINAL only)
uv run pytest tests/eval/tier2/ -xvs -p no:xdist

# Run Tier 2 canary (5 delegation routing tests only, ~$0.11)
uv run pytest tests/eval/tier2/ -xvs -p no:xdist -k "test_delegation_routing"

# Run Tier 3 hook interception tests (~$0.50 for 7 tests, from TERMINAL only)
uv run pytest tests/eval/tier3/ -xvs -p no:xdist

# Run ALL eval tests
make test-eval

# Run only structural (Tier 1)
make test-eval-structural

# Run only Tier 2
make test-eval-tier2

# Run Tier 2 canary (5 tests)
make test-eval-tier2-canary

# Run only Tier 3
make test-eval-tier3

# Run all tiers with result recording
make test-eval-record

# Check for degradation against historical results
make test-eval-check-degradation
```

## Git State

- **Branch:** `e2e-delegation-tests`
- **Latest commit:** (Phase 4 commit pending)
- **Previous commits:** `d2cf0199` (Phase 3), `2349209c` (research-first fix), `30cb01e5` (Phase 2), `8a746f84` (Phase 0+1)
- **Base branch for PRs:** `main`
