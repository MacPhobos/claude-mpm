# E2E Delegation Testing: Developer Guide

This guide covers how to run, extend, and maintain the E2E delegation test suite for the claude-mpm PM prompt.

---

## Overview

The test suite verifies that the PM correctly delegates tasks to specialized agents rather than attempting work directly. It uses a 3-tier architecture:

| Tier | What It Tests | Mechanism | Cost | Speed |
|------|--------------|-----------|------|-------|
| **Tier 1** | Prompt assembly correctness | FrameworkLoader + string checks | $0 | <1s |
| **Tier 2** | Delegation *intent* | `claude -p --json-schema --tools ""` | ~$0.07/test | 3-8s |
| **Tier 3** | Delegation *behavior* | Hook interception + blocking | ~$0.10/test | 5-15s |

## Running Tests

### Quick Commands

```bash
# Tier 1 only (free, fast — run anytime)
make test-eval-structural

# Tier 2 delegation intent (requires claude CLI, ~$0.84 total)
make test-eval-tier2

# Tier 2 canary (5 routing tests only, ~$0.11)
make test-eval-tier2-canary

# Tier 3 behavioral (requires claude CLI, ~$0.50 total)
make test-eval-tier3

# All tiers
make test-eval

# All tiers with result recording
make test-eval-record

# Check for degradation against historical results
make test-eval-check-degradation
```

### Direct pytest Commands

```bash
# Tier 1
uv run pytest tests/eval/structural/ -v

# Tier 2 (MUST use -p no:xdist for prompt caching)
uv run pytest tests/eval/tier2/ -xvs -p no:xdist

# Tier 3 (MUST use -p no:xdist)
uv run pytest tests/eval/tier3/ -xvs -p no:xdist

# With result recording
EVAL_RECORD_RESULTS=1 uv run pytest tests/eval/ -v -p no:xdist

# Or using the --eval-record flag
uv run pytest tests/eval/ -v -p no:xdist --eval-record
```

### Important Constraints

1. **Tier 2 and Tier 3 tests CANNOT run from within a Claude session.** They must be run from a terminal because they invoke `claude -p` or `claude-mpm run` as subprocesses.

2. **Always use `-p no:xdist`** for Tier 2 and Tier 3 tests. Sequential execution enables Anthropic's prompt caching (90% cost reduction after first call).

3. **`claude` CLI must be installed** for Tier 2 and Tier 3. Tests auto-skip if unavailable.

---

## Test Architecture

### Directory Structure

```
tests/eval/
  conftest.py                          # Top-level config, result recorder plugin registration
  adapters/
    structured_output_adapter.py       # Tier 2: wraps claude -p with --json-schema
    hook_interception_harness.py       # Tier 3: manages interceptor + claude-mpm subprocess
  scenarios/
    delegation_scenarios.json          # Shared scenario definitions
  structural/                          # Tier 1 tests
    conftest.py                        # Session-scoped assembled_prompt fixture
    test_prompt_assembly.py            # Section presence, checksums, components
    test_v1_tool_name.py               # Tool name consistency
    test_v3_framework_loader.py        # FrameworkLoader works in pytest
  tier2/                               # Tier 2 tests
    conftest.py                        # Module-scoped adapter, auto-skip
    test_delegation_intent.py          # 13 delegation intent tests
  tier3/                               # Tier 3 tests
    conftest.py                        # Harness fixture, auto-skip
    test_delegation_behavior.py        # 7 behavioral tests
  tracking/                            # Result tracking + degradation detection
    result_recorder.py                 # Pytest plugin for recording results
    degradation_detector.py            # Historical comparison + alerting
  results/                             # Result JSON files (gitignored)
    .gitkeep
```

### How Each Tier Works

#### Tier 1: Structural Validation

Tests run entirely in-process using `FrameworkLoader` to assemble the PM prompt, then check:
- **Section presence**: Critical sections like "DELEGATION-BY-DEFAULT PRINCIPLE", "ABSOLUTE PROHIBITIONS" exist
- **Agent references**: All 8 core agents are referenced
- **Semantic checksums**: SHA-256 hashes of critical sections haven't changed (detects unintentional drift)
- **Assembly components**: Agent definitions, workflow instructions, memory, skills all present

No API calls, no cost, runs in <2 seconds.

#### Tier 2: Delegation Intent

Sends prompts through `claude -p` with `--json-schema` (forces structured output) and `--tools ""` (prevents tool execution). The PM's system prompt is assembled and the LLM responds with a structured JSON indicating:
- `would_delegate`: boolean
- `target_agent`: string
- `reasoning`: string

Uses 2-of-3 consensus voting to handle LLM non-determinism.

#### Tier 3: Delegation Behavior

Runs `claude-mpm run` with a PreToolUse hook interceptor that:
1. Captures Task tool call parameters (agent, prompt, description)
2. Blocks execution (prevents actual subagent spawn)
3. Writes captured data to a JSONL file

Tests then read the JSONL and verify the correct agent was selected.

---

## Adding New Test Scenarios

### Step 1: Add to delegation_scenarios.json

```json
// tests/eval/scenarios/delegation_scenarios.json
{
  "scenarios": {
    "delegation": [
      // ... existing scenarios ...
      {
        "id": "DEL-06",
        "prompt": "Your new test prompt here",
        "expected_agent": "engineer",
        "agent_alternatives": ["research"],
        "description": "What this scenario tests"
      }
    ]
  }
}
```

**Fields:**
- `id`: Unique identifier (DEL-XX, NODL-XX, CTX-XX, CB-XX)
- `prompt`: The user prompt to send to the PM
- `expected_agent`: Primary expected agent (lowercase)
- `agent_alternatives`: List of acceptable alternative agents (e.g., research-gate may trigger)
- `description`: Human-readable description
- `expected_keywords`: (context_quality only) Keywords expected in reasoning
- `circuit_breaker`: (circuit_breaker only) Which CB number this tests

### Step 2: Reference in Tests

**For Tier 2** (`test_delegation_intent.py`):
Scenarios are auto-loaded from JSON. New delegation scenarios in the `"delegation"` category will automatically be picked up by `test_delegation_routing`.

**For Tier 3** (`test_delegation_behavior.py`):
Scenarios are defined inline in `BEHAVIOR_SCENARIOS`. Add a new dict:

```python
{
    "id": "BHV-06",
    "prompt": "Your new test prompt here",
    "expected_agents": ["engineer"],
    "description": "What this scenario tests",
},
```

### Step 3: Update Counts

Update the SESSION-RESUME.md test counts and any cost estimates (each Tier 2 test costs ~$0.07, each Tier 3 test costs ~$0.10).

### Guidelines for Good Scenarios

- **Be specific**: "Implement OAuth2 authentication" not "do something"
- **Use trigger keywords**: Match the PM's routing rules (e.g., "localhost" for local-ops)
- **Include alternatives**: The Research Gate may cause research-first routing for complex tasks
- **Avoid ambiguity**: Each scenario should have a clear expected agent
- **Test boundaries**: Include scenarios that test PM's decision between similar agents

---

## Result Tracking

### How It Works

When `--eval-record` or `EVAL_RECORD_RESULTS=1` is set, the `EvalResultRecorder` pytest plugin:
1. Hooks into each test's result (pass/fail/skip/error)
2. Extracts tier, scenario ID, and duration
3. On session finish, writes a JSON file to `tests/eval/results/`

### Result File Format

Each run produces a file like `tests/eval/results/20260309-212500.json`:

```json
{
  "run_id": "20260309-212500",
  "timestamp": "2026-03-09T21:25:00Z",
  "git_branch": "e2e-delegation-tests",
  "git_commit": "d2cf0199",
  "tiers_run": ["tier1", "tier2"],
  "summary": {
    "total": 45,
    "passed": 44,
    "failed": 1,
    "skipped": 0,
    "error": 0,
    "pass_rate": 0.978,
    "duration_seconds": 12.5
  },
  "tests": [
    {
      "node_id": "tests/eval/tier2/test_delegation_intent.py::test_delegation_routing[DEL-01]",
      "tier": "tier2",
      "outcome": "passed",
      "duration_seconds": 3.2,
      "scenario_id": "DEL-01"
    }
  ]
}
```

Result JSON files are gitignored — they're local-only historical data.

### Degradation Detection

Run the detector to compare the latest result against recent history:

```bash
# Default: compare latest against last 5 runs
uv run python -m tests.eval.tracking.degradation_detector

# Custom lookback window
uv run python -m tests.eval.tracking.degradation_detector --lookback 10

# Custom results directory
uv run python -m tests.eval.tracking.degradation_detector --results-dir path/to/results/
```

**What it detects:**
- **Test regression**: A test that passed >=80% of recent runs now fails
- **New failure**: A test that never failed before now fails
- **Cost spike**: Total cost increased by >50% vs recent average
- **Pass rate drop**: Overall pass rate dropped by >5% vs recent average

Exit code: 0 = clean, 1 = degradation detected.

---

## Fidelity Gap

The test suite validates delegation behavior at three levels, but there are inherent limitations:

### What the Tests Prove

| Level | Evidence | Confidence |
|-------|----------|------------|
| Tier 1 | PM prompt is correctly assembled with all required sections | High (deterministic) |
| Tier 2 | Given the PM prompt, Claude *intends* to delegate correctly | Medium-High (LLM variance handled by consensus) |
| Tier 3 | In the full runtime, Claude *attempts* correct delegation via Task tool | Medium (real pipeline, but blocked before execution) |

### What the Tests Cannot Prove

1. **Subagent quality**: Tests verify routing, not whether the subagent does good work
2. **End-to-end completion**: Delegation is blocked before the subagent runs
3. **Multi-turn behavior**: Tests capture only the first delegation decision
4. **Post-block behavior**: After a Tool is blocked, Claude may retry, error, or continue unpredictably
5. **Context sensitivity**: The PM's routing may differ based on project context, memory, or prior conversation

### Mitigation Strategies

- **2-of-3 consensus** (Tier 2): Reduces false positives from LLM non-determinism
- **Alternative agents accepted**: Scenarios allow multiple valid routing options
- **Historical tracking**: Detect gradual degradation over time
- **Cost monitoring**: Alert on unexpected cost changes (may indicate behavioral shift)

---

## Cost Model

### Per-Invocation Costs

| Tier | Cost/Test | Full Suite | With Prompt Caching |
|------|-----------|-----------|-------------------|
| Tier 1 (45 tests) | $0.00 | $0.00 | $0.00 |
| Tier 2 (13 tests) | ~$0.07 | ~$0.84 | ~$0.21 |
| Tier 3 (7 tests) | ~$0.10 | ~$0.70 | ~$0.50 |
| **Total** | | **~$1.54** | **~$0.71** |

Prompt caching activates after the first call in a sequential run (90% discount on input tokens, 5-minute TTL). This is why `-p no:xdist` is required.

### Budget Controls

- Tier 2 adapter: `max_budget_usd=0.50` per invocation
- Tier 3 harness: `CLAUDE_CODE_MAX_TURNS=3` env var (limits retries after block)
- Sequential execution (`-p no:xdist`) enables prompt caching

---

## Troubleshooting

### "claude CLI not available" — tests skipped

Install Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

### Tests fail with "nested session error"

You're running Tier 2/3 tests from within a Claude session. Run from a regular terminal instead.

### Flaky test failures

LLM responses are non-deterministic. Strategies:
- Tier 2 uses 2-of-3 consensus voting
- Tier 3 captures the first delegation attempt
- If a test fails intermittently, consider adding `agent_alternatives` to the scenario

### "No delegation captured" in Tier 3

The interceptor may not have been installed correctly. Check:
1. `.claude/settings.local.json` was written in the workspace
2. The interceptor script is executable
3. The `CLAUDE_MPM_DELEGATION_CAPTURE_FILE` env var is set

### Semantic checksum failures

A Tier 1 checksum test failing means a critical PM prompt section has changed. This is intentional protection — if you've deliberately changed the section, update the baseline hash:

```python
# In test_prompt_assembly.py, update CHECKSUM_BASELINES
"delegation_principle": "new_hash_here",
```

Run with `test_baseline_hash_helper` to get the new hash values.

---

## Pytest Markers

| Marker | Description |
|--------|-------------|
| `eval` | All evaluation tests |
| `structural` | Tier 1 structural validation tests |
| `tier2` | Tier 2 structured output intent tests |
| `tier3` | Tier 3 hook interception behavioral tests |
| `e2e` | End-to-end tests (includes tier3) |
