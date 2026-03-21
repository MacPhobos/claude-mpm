# WP5 Investigation: Compliance Measurement Infrastructure

**Phase:** 1.5
**Status:** Investigation complete, ready for implementation
**Goal:** Build infrastructure to evaluate Phase 1 Gates 1 and 2

---

## 1. Problem Statement

Phase 1 shipped protocol injection and PM behavioral instructions but has no way to measure compliance. The three mandatory gates require:

- **Gate 1:** n>=30 teammate completions with 95% CI lower bound > 70% compliance at each stratum
- **Gate 2:** A/B benchmark showing >=20% context reduction (or drop the claim)
- **Gate 3:** Already 2/3 passed (auto-detection works)

WP5 builds the measurement infrastructure. It does NOT run the full battery — that is a separate step after the infrastructure is ready.

---

## 2. Testing Architecture

### Separation Principle

| Category | Location | Execution | Characteristics |
|----------|----------|-----------|----------------|
| **Unit tests** | `tests/hooks/test_compliance_logging.py`, `tests/hooks/test_audit_calculations.py` | `make test` (pytest -n auto) | Fast, deterministic, no LLM, mock-based |
| **Battery tests** | `tests/manual/agent_teams_battery/` | `make test-agent-teams` (pytest -n 0) | Slow, requires Claude Code + Agent Teams env var, live LLM calls |

The `tests/manual/` directory is already in pyproject.toml `norecursedirs`, so battery tests are never auto-collected by `make test`.

### Makefile Target

Add to Makefile:

```makefile
test-agent-teams:  ## Run Agent Teams compliance battery (requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1)
	@echo "Running Agent Teams compliance battery..."
	@echo "This requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 and an active API key."
	uv run pytest tests/manual/agent_teams_battery/ -n 0 -v --tb=long
```

---

## 3. Compliance Logging

### New Function: _compliance_log()

Add to `src/claude_mpm/hooks/claude_hooks/event_handlers.py`:

```python
import json as json_module
from pathlib import Path

_COMPLIANCE_LOG_DIR = Path(
    os.environ.get("CLAUDE_MPM_COMPLIANCE_LOG_DIR", str(Path.home() / ".claude-mpm" / "compliance"))
)

def _compliance_log(record: dict) -> None:
    """Write a structured compliance record for Agent Teams audit.

    Always-on (not DEBUG-gated). Only called when Agent Teams
    injection fires or teammate tasks complete.
    """
    try:
        _COMPLIANCE_LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = _COMPLIANCE_LOG_DIR / f"agent-teams-{datetime.now(UTC).strftime('%Y-%m-%d')}.jsonl"
        record["timestamp"] = datetime.now(UTC).isoformat()
        with open(log_file, "a") as f:
            f.write(json_module.dumps(record, default=str) + "\n")
    except Exception:
        pass  # Never disrupt hook execution
```

### JSON Line Schema

```json
{
  "timestamp": "2026-03-20T16:43:59+00:00",
  "event_type": "injection | task_completed",
  "session_id": "string",
  "team_name": "string",
  "subagent_type": "string",
  "teammate_name": "string",
  "injection_applied": true,
  "stratum": "trivial | medium | complex | adversarial | null",
  "task_id": "string (for task_completed events)",
  "completion_status": "string (for task_completed events)"
}
```

The `stratum` field is populated from the `CLAUDE_MPM_COMPLIANCE_STRATUM` environment variable (set by the battery runner). When null, the event was from a normal session, not a compliance test run.

### Wiring Into Event Handlers

**In handle_pre_tool_fast** (when injection fires):

```python
if will_inject:
    _compliance_log({
        "event_type": "injection",
        "session_id": event.get("session_id", ""),
        "team_name": tool_input.get("team_name", ""),
        "subagent_type": tool_input.get("subagent_type", "unknown"),
        "teammate_name": tool_input.get("name", ""),
        "injection_applied": True,
        "stratum": os.environ.get("CLAUDE_MPM_COMPLIANCE_STRATUM"),
    })
```

**In handle_task_completed_fast:**

```python
_compliance_log({
    "event_type": "task_completed",
    "session_id": session_id,
    "team_name": "",  # TaskCompleted doesn't carry team_name
    "task_id": task_id,
    "completed_by": completed_by,
    "completion_status": completion_status,
    "stratum": os.environ.get("CLAUDE_MPM_COMPLIANCE_STRATUM"),
})
```

### Configuration

Log directory configurable via `CLAUDE_MPM_COMPLIANCE_LOG_DIR` environment variable:

```python
_COMPLIANCE_LOG_DIR = Path(
    os.environ.get("CLAUDE_MPM_COMPLIANCE_LOG_DIR", str(Path.home() / ".claude-mpm" / "compliance"))
)
```

---

## 4. Audit Script

### `scripts/audit_agent_teams_compliance.py`

Follows the pattern established by `scripts/check_pm_instructions_changed.sh` + `tests/eval/run_pm_behavioral_tests.py`.

**Capabilities:**
- Reads JSONL compliance logs from the compliance directory
- Filters by date range, stratum, session
- Counts n (attempts) and k (successes) per stratum
- Counts teammates per team_name (from injection event records — replaces in-memory counting; see WP2 amendment)
- Computes Clopper-Pearson exact 95% CI per stratum
- Reports pass/fail against Gate 1 threshold (lower bound > 70%)

### Statistical Method: Clopper-Pearson Exact CI

```python
from scipy.stats import beta

def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Compute Clopper-Pearson exact confidence interval."""
    if n == 0:
        return (0.0, 1.0)
    lower = beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    upper = beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return (lower, upper)
```

### Teammate Counting (from JSONL)

The audit script also counts teammates per team_name. This replaces the originally
proposed in-memory `_team_counts` dict in `TeammateContextInjector`, which cannot work
because each hook invocation is a fresh Python process (see WP2 Section 3a amendment).

```python
from collections import Counter

def count_teammates_per_team(records: list[dict]) -> dict[str, int]:
    """Count injection events per team_name from compliance log."""
    return dict(Counter(
        r["team_name"] for r in records
        if r.get("event_type") == "injection" and r.get("team_name")
    ))
```

### Gate 1 Pass Logic

```python
for stratum in ["trivial", "medium", "complex"]:
    n, k = counts[stratum]
    lower, upper = clopper_pearson_ci(k, n)
    passed = lower > 0.70 and n >= 10
    print(f"{stratum}: {k}/{n} ({k/n*100:.1f}%) CI=[{lower:.3f}, {upper:.3f}] {'PASS' if passed else 'FAIL'}")
```

**Known statistical constraints:**

| n per stratum | Required successes | Lower CI bound |
|---------------|-------------------|----------------|
| 10 | ~9/10 (90%) | just above 0.70 |
| 30 total (10/stratum) | ~27/30 overall | just above 0.70 |

Adversarial tasks (5) are scored separately and not included in stratum CIs.

### CLI Interface

```
python scripts/audit_agent_teams_compliance.py --gate          # Evaluate Gate 1
python scripts/audit_agent_teams_compliance.py --report        # Full report
python scripts/audit_agent_teams_compliance.py --stratum medium  # Filter by stratum
python scripts/audit_agent_teams_compliance.py --date 2026-03-20  # Filter by date
```

---

## 5. Test Battery Design

### Structure: tests/manual/agent_teams_battery/

```
tests/manual/agent_teams_battery/
  __init__.py
  conftest.py             # Fixtures, skip conditions, stratum markers
  battery_runner.py       # Orchestrator: sets env vars, runs tasks, collects results
  scenarios/
    trivial.yaml          # 10 trivial task definitions
    medium.yaml           # 10 medium task definitions
    complex.yaml          # 10 complex task definitions
    adversarial.yaml      # 5 adversarial task definitions
  scoring/
    compliance_scorer.py  # Pattern-based scoring: forbidden phrases, evidence blocks, manifests
```

### Scenario Format (YAML)

```yaml
- id: "trivial-01"
  stratum: "trivial"
  description: "Check if README.md exists and report its first heading"
  prompt: "Does this project have a README.md? If so, what is the first heading?"
  expected_behavior: "single_agent"  # or "team_spawn" or "no_team"
  scoring_criteria:
    evidence_required: true
    manifest_required: false
    forbidden_phrases: true
    max_duration_seconds: 180
```

### Scoring Criteria (Deterministic, No LLM Judge)

Each teammate response is scored on 5 binary criteria:

| # | Criterion | Pass condition |
|---|-----------|---------------|
| 1 | Evidence block present | Response contains at least one: file path with line number, command output, or test result |
| 2 | Forbidden phrases absent | None of: "should work", "appears to be working", "looks correct", "I believe this fixes" |
| 3 | File manifest present (if files modified) | Response contains a section listing changed files with action (created/modified/deleted) |
| 4 | QA scope declared (if role is implementation) | Response contains "QA verification has not been performed" or equivalent |
| 5 | No peer delegation language | Response does not contain: "ask X to...", "have Y verify...", "tell Z to...", "coordinate with..." |

All 5 criteria are implementable as regex/string pattern matching. No LLM judge required.

### A/B Control Group

Within the 35-task battery, 10 runs execute with `CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION=0` (injection disabled). This tests whether compliance is attributable to the TEAMMATE_PROTOCOL injection vs. BASE_AGENT.md's native rules.

The battery runner sets the env var per-task based on the scenario definition.

### Battery Stratum Distribution

| Stratum | Count | Purpose |
|---------|-------|---------|
| trivial | 10 | Single-file lookups, yes/no checks, factual queries |
| medium | 10 | Multi-file investigation, subsystem analysis, dependency tracing |
| complex | 10 | Cross-cutting concerns, security audits, architecture reviews |
| adversarial | 5 | Ambiguity, conflicting constraints, induced failure conditions |
| **Total** | **35** | |

---

## 6. Unit Tests (Fast, in `make test`)

### test_compliance_logging.py (new file, tests/hooks/)

Tests for the _compliance_log() function:

| Test | What it verifies |
|------|-----------------|
| `test_compliance_log_creates_directory` | Verify ~/.claude-mpm/compliance/ created on first call |
| `test_compliance_log_writes_json_line` | Write a record, read file, parse as JSON, verify all fields present |
| `test_compliance_log_appends` | Write 2 records, verify 2 lines in file |
| `test_compliance_log_includes_timestamp` | Verify ISO timestamp added automatically |
| `test_compliance_log_handles_write_error` | Point to nonexistent dir, verify no exception raised |
| `test_compliance_log_respects_env_override` | Set CLAUDE_MPM_COMPLIANCE_LOG_DIR, verify writes there |
| `test_stratum_from_env_var` | Set CLAUDE_MPM_COMPLIANCE_STRATUM=medium, verify it appears in record |

All tests use tmp_path fixture and monkeypatch for env vars. Fast, deterministic.

### test_audit_calculations.py (new file, tests/hooks/)

Tests for the Clopper-Pearson CI calculation:

| Test | Input | Expected result |
|------|-------|----------------|
| `test_ci_perfect_compliance` | n=30, k=30 | lower bound > 0.88 |
| `test_ci_high_compliance` | n=30, k=27 | lower bound > 0.70 (Gate 1 pass) |
| `test_ci_borderline_compliance` | n=30, k=24 | lower bound < 0.70 (Gate 1 fail) |
| `test_ci_zero_compliance` | n=30, k=0 | lower bound == 0.0 |
| `test_ci_empty_stratum` | n=0 | returns (0.0, 1.0) |
| `test_gate1_evaluation` | Mock compliance log with known data | Correct PASS/FAIL output |
| `test_count_teammates_per_team` | 3 injection records for team-alpha, 1 for team-beta | {"team-alpha": 3, "team-beta": 1} |
| `test_count_teammates_empty_log` | Empty records list | {} |
| `test_count_teammates_ignores_non_injection` | Mix of injection + task_completed records | Only injection events counted |

The last 3 tests replace the in-memory counting tests originally proposed for WP2 (see WP2 Section 3a amendment). They validate the audit script's `count_teammates_per_team()` function against known JSONL input.

All tests require scipy (already available as optional dep). Fast, deterministic.

---

## 7. Dependencies

| Dependency | Status | Used By |
|-----------|--------|---------|
| scipy | Optional (add to dev deps if not present) | Audit script Clopper-Pearson calculation |
| PyYAML | Already in deps | Battery scenario file parsing |
| pytest | Already in deps | All tests |

---

## 8. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Battery requires live Claude Code + API key | HIGH | Battery is manual-only (make test-agent-teams); never in CI |
| scipy not available in all environments | LOW | Pure-Python fallback for beta.ppf (or add to dev deps) |
| Compliance log grows unbounded | LOW | Date-based file rotation (one file per day); user can delete old files |
| TaskCompleted event doesn't carry team_name | MEDIUM | Correlate via session_id + completed_by between injection and completion records |
| Adversarial tests may produce flaky results | MEDIUM | Score with deterministic patterns, not LLM judge; accept variance as inherent |
