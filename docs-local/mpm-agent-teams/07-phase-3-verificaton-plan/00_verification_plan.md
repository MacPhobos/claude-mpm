# Phase 2 Verification Plan: Live Battery & Gate Evaluation

**Branch:** `mpm-teams` (commit `3d3bb251`)
**Date:** 2026-03-20
**Author:** Research Agent
**Status:** PLAN (not yet executed)

---

## 1. Executive Summary

Phase 2 implementation is code-complete with 197 passing synthetic tests (41 injector, 24 scorer, 132 battery pipeline). The remaining work is **verification**: running scenarios against a real PM operating with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, collecting compliance data, and evaluating the Gate 1 statistical criterion.

This plan identifies five gaps between the current infrastructure and what is needed for gate passage, proposes four verification strategy options with a recommended hybrid approach, and defines five work packages totaling an estimated 3-5 days of effort and $30-65 in API costs.

**Key finding:** Full end-to-end live execution (Option A) is prohibitively expensive and time-consuming for 130 scenarios. The recommended approach (Option D: Hybrid) combines automated hook-level injection validation with selective live PM observation on a representative sample, achieving gate-quality evidence at roughly 20% of the full-live cost.

---

## 2. Current State Assessment

### 2.1 What Exists

| Component | Location | Status |
|---|---|---|
| **Compliance logging** | `src/claude_mpm/hooks/claude_hooks/event_handlers.py` lines 69-102 | Production-ready. `_compliance_log()` writes JSONL to `~/.claude-mpm/compliance/agent-teams-YYYY-MM-DD.jsonl`. Always-on, never raises. |
| **Teammate context injector** | `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` | Production-ready. `TeammateContextInjector` class prepends TEAMMATE_PROTOCOL to Agent tool prompts when `team_name` is present. |
| **Compliance scorer** | `tests/manual/agent_teams_battery/scoring/compliance_scorer.py` | Production-ready. 5-criterion deterministic scorer: evidence_present, forbidden_phrases_absent, manifest_present, qa_scope_declared, no_peer_delegation. Regex-based, no LLM required. |
| **Audit script** | `scripts/audit_agent_teams_compliance.py` | Functional but incomplete. Clopper-Pearson 95% CI, n>=10 gate logic. Only evaluates 3 strata (trivial/medium/complex). |
| **Scenario YAML files** | `tests/manual/agent_teams_battery/scenarios/*.yaml` | Complete. 130 scenarios across 7 files, 15 strata. |
| **Synthetic battery** | `tests/manual/agent_teams_battery/test_battery.py` `TestBatteryPipelineValidation` | Passing (132 tests). Covers all 15 strata with synthetic responses. |
| **Gate 1 evaluation tests** | `test_battery.py` `TestGate1Evaluation` | Passing. Validates gate logic with synthetic n=30 data for trivial/medium/complex only. |
| **Live battery class** | `test_battery.py` `TestLiveBattery` | Placeholder only. Single `test_live_trivial_placeholder` that calls `pytest.skip()`. |
| **Existing compliance data** | `~/.claude-mpm/compliance/` | 46 JSONL records from unit test runs. All have `stratum: null` -- unusable for gate evaluation. |
| **Makefile target** | `make test-agent-teams` | Runs synthetic battery. Does NOT pass `--live`. |

### 2.2 What Is Missing

1. **Live battery runner** -- `TestLiveBattery` is an empty placeholder with no execution machinery.
2. **Phase 2 strata in audit script** -- `evaluate_gate1()` hardcodes `["trivial", "medium", "complex"]`, ignoring the 12 Phase 2 strata.
3. **Response capture in compliance logs** -- `_compliance_log()` records injection events and task completions but does not capture or score the actual response text.
4. **Stratum tagging in live runs** -- The `CLAUDE_MPM_COMPLIANCE_STRATUM` env var must be set per-scenario, but live PM usage does not know the battery stratum.
5. **Sample size for Phase 2 strata** -- Many Phase 2 strata have only 2-5 scenarios (e.g., `full-pipeline`: 2, `pipeline-antipattern`: 2). Gate requires n>=10 per stratum.

---

## 3. Gap Analysis

| # | Gap | Severity | Impact | Effort to Close |
|---|---|---|---|---|
| G1 | **Audit script only evaluates 3 strata** | HIGH | Gate literally cannot evaluate Phase 2 strata. The `for stratum in ["trivial", "medium", "complex"]` loop must be expanded or made dynamic. | 1-2 hours |
| G2 | **Live battery runner is a placeholder** | HIGH | No mechanism to execute scenarios against a real PM and capture results. The entire verification campaign depends on this. | 1-3 days (depends on strategy) |
| G3 | **Response text not captured in compliance logs** | HIGH | The compliance scorer needs the actual response text, but `_compliance_log()` only records metadata (injection_applied, session_id, etc.). Without response capture, scoring is impossible for live runs. | 4-8 hours |
| G4 | **Stratum tagging absent in live usage** | MEDIUM | Live compliance records will have `stratum: null` (as seen in the existing 46 records). Without stratum tags, records cannot be grouped for per-stratum gate evaluation. | 2-4 hours |
| G5 | **Insufficient scenario count for some strata** | MEDIUM | `full-pipeline` has 2 scenarios, `pipeline-antipattern` has 2, `engineer-recovery` has 3. Gate requires n>=10. Either: (a) add more scenarios, (b) group related strata, or (c) run each scenario multiple times. | 2-4 hours to add scenarios OR design grouping |
| G6 | **No `--live` Makefile target** | LOW | `make test-agent-teams` does not pass `--live`. Minor: just needs a new target. | 15 minutes |
| G7 | **No cost guardrails** | LOW | No mechanism to cap spending during live verification. A runaway battery could consume significant API credits. | 1-2 hours |

---

## 4. Verification Strategy Options

### Option A: Full Live Execution (Spawn Real Teams)

**How it works:** For each of the 130 scenarios, start a Claude Code session with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, feed the scenario prompt to the PM, let it spawn real teammates via the Agent tool, capture the teammate responses, score them with the compliance scorer, and write scored compliance records.

**Pros:**
- Tests the entire end-to-end flow including PM decomposition behavior
- Validates that teammate context injection works in production conditions
- Captures real teammate responses for scoring

**Cons:**
- Extremely expensive: 130 scenarios x 2-3 subagents x $0.10-$0.50 each = $26-$195
- Very slow: ~5-10 minutes per scenario = ~11-22 hours of wall-clock time
- Requires active API key with sufficient credits
- PM decomposition behavior is non-deterministic -- same prompt may not spawn teams
- Cannot control which strata the PM selects (PM does not know about strata)
- Difficult to automate: Claude Code sessions are interactive

**Estimated cost:** $50-200
**Estimated time:** 15-25 hours (execution) + 2-3 days (tooling)
**Verdict:** Impractical as the sole strategy. Useful for a small representative sample.

### Option B: Hook-Level Simulation (Inject + Capture + Score)

**How it works:** Bypass the PM entirely. Directly invoke the `TeammateContextInjector` with synthetic PreToolUse events that mimic the Agent tool being called with team context. Capture the injected prompt, feed it (plus the scenario prompt) to a single LLM call to generate a teammate-style response, then score that response with the compliance scorer.

**Pros:**
- Tests that injection logic works correctly with realistic event shapes
- Can generate scored compliance records for all 130 scenarios
- Cheaper: 130 single-turn LLM calls at ~$0.02 each = ~$2.60
- Fast: ~1-2 minutes per scenario = ~2-4 hours total
- Fully automatable

**Cons:**
- Does NOT test PM decomposition behavior (the PM instructions in WP-B)
- Teammate responses are generated by a single LLM call, not actual subagents
- Missing the multi-agent orchestration dynamics (worktree isolation, merge, etc.)
- Essentially a more expensive version of the existing synthetic battery

**Estimated cost:** $3-5
**Estimated time:** 3-5 hours (execution) + 1 day (tooling)
**Verdict:** Good for validating injection + scoring pipeline at scale. Insufficient for PM behavioral validation.

### Option C: Manual Execution with Passive Collection

**How it works:** An operator manually uses Claude Code with Agent Teams enabled for real development tasks. The compliance hooks passively log all injection events and task completions. After accumulating enough data, run the audit script.

**Pros:**
- Tests the real production workflow
- Zero tooling investment
- Generates authentic compliance data
- Captures genuine PM decomposition decisions

**Cons:**
- No control over which strata are exercised
- Cannot guarantee n>=10 for all 15 strata
- Response text not captured (G3 still applies)
- Stratum tagging is absent (G4 still applies) -- all records will have `stratum: null`
- Extremely slow: could take weeks to accumulate sufficient data organically
- Non-reproducible: results depend on the operator's natural usage patterns

**Estimated cost:** Normal development API costs
**Estimated time:** Weeks to months for organic data accumulation
**Verdict:** Useful as background data collection but cannot drive gate evaluation on a timeline.

### Option D: Hybrid (Recommended)

**How it works:** Three-tier approach combining automated validation with targeted live verification:

**Tier 1 -- Automated injection validation (all 130 scenarios):**
Extend the existing synthetic battery to also exercise the `TeammateContextInjector` with realistic event payloads. Verify that injection fires correctly, the TEAMMATE_PROTOCOL is prepended, and compliance records are written with proper stratum tags. This validates the hook pipeline end-to-end without LLM costs.

**Tier 2 -- LLM-scored simulation (all 130 scenarios):**
For each scenario, construct a prompt that includes the injected TEAMMATE_PROTOCOL + scenario prompt, send it to Claude (Haiku for cost efficiency), capture the response, score it with the compliance scorer, and write a full compliance record. This validates that the protocol instructions produce compliant responses.

**Tier 3 -- Selective live PM observation (15-20 scenarios, ~1 per stratum):**
Hand-select one representative scenario per stratum. Start a real Claude Code session with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, feed the scenario prompt, observe whether the PM spawns teams correctly, and manually capture the teammate response for scoring. This validates the PM behavioral instructions.

**Pros:**
- Tests all three layers: injection pipeline, response compliance, PM behavior
- Cost-efficient: bulk coverage from Tier 1+2, targeted live from Tier 3
- Generates n>=10 per stratum from Tier 2, with live validation from Tier 3
- Manageable timeline: 3-5 days total
- Fallback: if Tier 3 is too expensive, Tier 1+2 data is sufficient for a provisional gate pass

**Cons:**
- Tier 2 responses are simulated (single LLM call, not actual subagent)
- Tier 3 sample size per stratum is small (1-2 per stratum)
- Requires some tooling investment for Tier 2 runner

**Estimated cost:** $30-65 (Tier 2: ~$5, Tier 3: ~$25-60)
**Estimated time:** 3-5 days total

### Recommendation: Option D (Hybrid)

Option D is recommended because it provides evidence across all three validation layers at a fraction of Option A's cost. The key insight is that the gate criterion (Clopper-Pearson 95% CI lower bound > 0.70) measures **whether the protocol instructions produce compliant responses**, which Tier 2 tests directly. Tier 3 adds confidence that the PM orchestration layer works correctly in production conditions.

If budget constraints require further cost reduction, Tier 3 can be reduced to 8-10 scenarios (covering the highest-risk strata: engineer-parallel, engineer-merge, full-pipeline, qa-pipeline) while still providing meaningful live validation.

---

## 5. Implementation Work Packages

### WP-V1: Audit Script Update (Add Phase 2 Strata)

**Goal:** Make `evaluate_gate1()` dynamic so it evaluates ALL strata found in the data, not just the hardcoded 3.

**Changes to `scripts/audit_agent_teams_compliance.py`:**

1. Replace the hardcoded stratum list with dynamic discovery:
   ```python
   # BEFORE (line 120):
   for stratum in ["trivial", "medium", "complex"]:

   # AFTER:
   all_strata = sorted(set(
       r["stratum"] for r in injection_records if r.get("stratum")
   ))
   if not all_strata:
       all_strata = ["trivial", "medium", "complex"]  # fallback
   for stratum in all_strata:
   ```

2. Add `--strata-groups` CLI option to support stratum grouping (see Section 6):
   ```python
   parser.add_argument(
       "--strata-groups",
       type=str,
       help="JSON file mapping group names to stratum lists for grouped evaluation"
   )
   ```

3. Update the `--report` output to show all discovered strata.

4. Add an `--all-strata` flag to evaluate every distinct stratum in the data (as opposed to `--gate` which might use grouping).

**Estimated effort:** 2-4 hours
**Dependencies:** None
**Tests:** Extend `TestGate1Evaluation` to include Phase 2 strata data.

### WP-V2: Live Battery Runner Implementation

**Goal:** Implement a Tier 2 runner that generates LLM-scored responses for all 130 scenarios and writes compliance records.

**New file: `tests/manual/agent_teams_battery/live_runner.py`**

This is a standalone script (not a pytest test) that:

1. Loads all scenario YAML files.
2. For each scenario:
   a. Constructs the injected prompt by:
      - Loading the TEAMMATE_PROTOCOL text from `TeammateContextInjector`
      - Prepending it to the scenario's `prompt` field
      - Setting the appropriate role context
   b. Sends the combined prompt to Claude Haiku via the Anthropic API:
      ```python
      response = client.messages.create(
          model="claude-3-5-haiku-20241022",
          max_tokens=1500,
          system="You are a Claude Code teammate. Follow the protocol exactly.",
          messages=[{"role": "user", "content": injected_prompt}]
      )
      ```
   c. Scores the response using `score_response()`.
   d. Writes a compliance record via `_compliance_log()` with:
      - `event_type: "injection"`
      - `stratum`: from the scenario YAML
      - `injection_applied: True`
      - `scores`: from the scorer
      - `response_text`: the actual response (new field)
      - `source: "tier2-simulation"`
3. Prints a progress summary after each stratum.
4. Writes a final summary report.

**CLI interface:**
```bash
python tests/manual/agent_teams_battery/live_runner.py \
    --tier 2 \
    --strata trivial,medium,engineer-parallel \
    --max-cost 10.00 \
    --output-dir ~/.claude-mpm/compliance/
```

**Flags:**
- `--tier`: 1 (injection-only, no LLM), 2 (LLM-scored), 3 (manual prompts)
- `--strata`: comma-separated list of strata to run (default: all)
- `--max-cost`: abort if estimated cumulative cost exceeds this value
- `--output-dir`: compliance log output directory
- `--model`: model for Tier 2 responses (default: `claude-3-5-haiku-20241022`)
- `--dry-run`: print prompts without calling the API

**For Tier 3 (live PM observation):**
The runner generates a markdown file with structured prompts for manual execution:
```bash
python tests/manual/agent_teams_battery/live_runner.py \
    --tier 3 \
    --strata engineer-parallel,engineer-merge,full-pipeline \
    --output-dir ./live-verification/
```
This produces `live-verification/tier3-prompts.md` with:
- Instructions for setting up the Claude Code session
- The exact prompt to paste for each scenario
- A response capture template (paste the response, script scores it)
- A checklist of PM behavioral observations (did it spawn teams? how many?)

**Estimated effort:** 1-2 days
**Dependencies:** WP-V1 (for dynamic strata), Anthropic API key
**Tests:** Integration test that runs Tier 1 (no LLM) against 5 scenarios.

### WP-V3: Response Capture and Scoring Pipeline

**Goal:** Extend compliance logging to capture and score response text for both automated and manual runs.

**Changes:**

1. **Add `response_text` field to compliance records** (`event_handlers.py`):
   The `_compliance_log()` function already accepts arbitrary dict fields. No code change needed -- just ensure callers pass `response_text` in the record. For production hooks, the response text comes from the PostToolUse event's `result` field.

2. **Add response capture to PostToolUse handler** (`event_handlers.py`):
   When processing a PostToolUse event for the Agent tool (indicating a teammate has finished), extract the response text and score it:
   ```python
   if tool_name == "Agent" and event.get("team_name"):
       response_text = extract_tool_results(event)
       scores = score_response(response_text, ...)
       _compliance_log({
           "event_type": "response_scored",
           "session_id": session_id,
           "team_name": team_name,
           "response_text": response_text[:5000],  # truncate for log size
           "scores": scores,
           "stratum": os.environ.get("CLAUDE_MPM_COMPLIANCE_STRATUM"),
       })
   ```

3. **Add a manual scoring CLI** for Tier 3:
   ```bash
   python tests/manual/agent_teams_battery/score_response.py \
       --response-file ./captured-response.txt \
       --stratum engineer-parallel \
       --role engineer \
       --scenario-id eng-01
   ```
   Reads the response file, scores it, and appends a compliance record.

4. **Update audit script to use scored records:**
   Modify `evaluate_gate1()` to evaluate based on `response_scored` events (with actual scores) rather than just `injection` events (which only show injection_applied):
   ```python
   scored_records = [
       r for r in records
       if r.get("event_type") == "response_scored" and r.get("stratum")
   ]
   # Fall back to injection records if no scored records exist
   if not scored_records:
       scored_records = injection_records
   ```

**Estimated effort:** 4-8 hours
**Dependencies:** WP-V1
**Tests:** Unit tests for response capture and manual scoring CLI.

### WP-V4: Execution Campaign (Run the Scenarios)

**Goal:** Execute the three tiers and accumulate compliance data.

**Execution plan:**

**Day 1: Tier 1 -- Automated Injection Validation**
```bash
# Run existing synthetic battery (validates pipeline)
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 make test-agent-teams

# Run Tier 1 of live runner (injection-only, no LLM)
python tests/manual/agent_teams_battery/live_runner.py --tier 1 --strata all
```
Expected output: 130 compliance records with `source: tier1-injection`, all showing `injection_applied: true`.
Expected duration: ~5 minutes.
Expected cost: $0.

**Day 2-3: Tier 2 -- LLM-Scored Simulation**
```bash
# Run Tier 2 for all strata
python tests/manual/agent_teams_battery/live_runner.py \
    --tier 2 \
    --strata all \
    --max-cost 10.00 \
    --model claude-3-5-haiku-20241022
```
Expected output: 130 compliance records with `source: tier2-simulation`, each including `response_text` and `scores`.
Expected duration: ~2-4 hours (rate-limited).
Expected cost: ~$3-5.

**Post-Tier-2 checkpoint:**
```bash
python scripts/audit_agent_teams_compliance.py --gate --report
```
Review per-stratum pass rates. If any stratum fails (CI lower bound <= 0.70), investigate:
- Is the TEAMMATE_PROTOCOL insufficient for that stratum?
- Does the scorer have false negatives?
- Does the scenario prompt need adjustment?

**Day 4-5: Tier 3 -- Live PM Observation**
```bash
# Generate Tier 3 prompt sheets
python tests/manual/agent_teams_battery/live_runner.py \
    --tier 3 \
    --strata engineer-parallel,engineer-merge,qa-pipeline,full-pipeline,research-then-eng
```

For each selected scenario:
1. Open a new Claude Code session:
   ```bash
   CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 \
   CLAUDE_MPM_COMPLIANCE_STRATUM=<stratum> \
   claude
   ```
2. Paste the scenario prompt.
3. Observe:
   - Does the PM spawn a team? (Y/N)
   - How many teammates? (expected vs. actual)
   - Does it use worktree isolation for engineers? (Y/N)
   - Does it delegate merge to a single teammate? (Y/N for merge strata)
4. Copy the teammate response(s) to a file.
5. Score:
   ```bash
   python tests/manual/agent_teams_battery/score_response.py \
       --response-file ./response-eng-01.txt \
       --stratum engineer-parallel \
       --role engineer \
       --scenario-id eng-01
   ```

Expected output: 15-20 scored compliance records with `source: tier3-live`.
Expected duration: ~4-8 hours (manual).
Expected cost: ~$25-60.

### WP-V5: Gate Evaluation and Results

**Goal:** Run the final gate evaluation and document results.

```bash
# Final gate evaluation
python scripts/audit_agent_teams_compliance.py \
    --gate \
    --report \
    --log-dir ~/.claude-mpm/compliance/
```

**Gate pass criteria (per stratum):**
- n >= 10
- Clopper-Pearson 95% CI lower bound > 0.70

**If gate passes:**
- Document results in `docs-local/mpm-agent-teams/07-phase-3-verificaton-plan/01_gate_results.md`
- Archive compliance logs
- Create summary PR for review

**If gate fails for specific strata:**
1. Analyze failure mode:
   - Low n? Run more scenarios for that stratum.
   - Low compliance rate? Investigate scorer false negatives or protocol gaps.
   - Borderline CI? Increase sample size (n=20-30) to tighten the interval.
2. Implement fixes.
3. Re-run affected strata only.
4. Re-evaluate gate.

**Estimated effort:** 2-4 hours
**Dependencies:** WP-V1 through WP-V4 complete.

---

## 6. Sample Size & Statistical Requirements

### 6.1 Per-Stratum Minimums

The gate criterion is: **Clopper-Pearson 95% CI lower bound > 0.70 with n >= 10.**

For a perfect compliance rate (k = n), the CI lower bound as a function of n:

| n | k (if perfect) | CI lower bound | Passes gate? |
|---|---|---|---|
| 5 | 5 | 0.478 | No (below 0.70) |
| 8 | 8 | 0.631 | No (below 0.70) |
| 10 | 10 | 0.692 | Borderline (barely below 0.70) |
| 11 | 11 | 0.715 | Yes |
| 12 | 12 | 0.735 | Yes |
| 15 | 15 | 0.782 | Yes |
| 20 | 20 | 0.832 | Yes |
| 30 | 30 | 0.884 | Yes |

**Critical observation:** Even with 100% compliance (k=n), **n=10 barely fails** (CI lower = 0.692 < 0.70). The minimum viable sample size for passing with perfect compliance is **n=11**. With any single failure, the minimum n rises:

| n | k (one failure) | Rate | CI lower bound | Passes? |
|---|---|---|---|---|
| 11 | 10 | 90.9% | 0.587 | No |
| 15 | 14 | 93.3% | 0.681 | No |
| 20 | 19 | 95.0% | 0.751 | Yes |
| 25 | 24 | 96.0% | 0.798 | Yes |
| 30 | 29 | 96.7% | 0.828 | Yes |

**Practical recommendation:** Target n >= 15 per stratum with 0 failures, or n >= 20 per stratum to tolerate 1 failure. This provides a safety margin above the mathematical minimum.

### 6.2 Stratification Grouping

Several Phase 2 strata have too few scenarios to reach n >= 15 individually:

| Stratum | Scenario count | Viable alone? |
|---|---|---|
| trivial | 30 | Yes |
| medium | 30 | Yes |
| complex | 30 | Yes |
| adversarial | 5 | No |
| engineer-parallel | 5 | No |
| engineer-merge | 4 | No |
| engineer-antipattern | 3 | No |
| engineer-recovery | 3 | No |
| qa-pipeline | 4 | No |
| qa-protocol | 3 | No |
| qa-antipattern | 3 | No |
| research-then-eng | 3 | No |
| eng-then-qa | 3 | No |
| full-pipeline | 2 | No |
| pipeline-antipattern | 2 | No |

**Proposed grouping strategy:**

| Group | Strata included | Scenario count | Rationale |
|---|---|---|---|
| **basic** | trivial, medium | 60 | Phase 1 core strata, well-tested |
| **complex** | complex | 30 | Phase 1 complex stratum |
| **adversarial** | adversarial | 5 | Anti-pattern detection (different evaluation: expects failure) |
| **engineer** | engineer-parallel, engineer-merge, engineer-recovery | 12 | All positive engineer behaviors |
| **engineer-antipattern** | engineer-antipattern | 3 | Anti-pattern detection |
| **qa** | qa-pipeline, qa-protocol | 7 | All positive QA behaviors |
| **qa-antipattern** | qa-antipattern | 3 | Anti-pattern detection |
| **pipeline** | research-then-eng, eng-then-qa, full-pipeline | 8 | All positive multi-phase pipelines |
| **pipeline-antipattern** | pipeline-antipattern | 2 | Anti-pattern detection |

**Anti-pattern groups** should be evaluated differently: they expect at least one scoring criterion to fail. The gate for anti-pattern groups is: "detection rate > 0.70" (the scorer correctly identifies non-compliant responses).

**To reach n >= 15 per group, three options:**

**Option 1: Run scenarios multiple times** (recommended for Tier 2). Since LLM responses are non-deterministic, running the same scenario 3 times produces 3 distinct data points. For the `engineer` group (12 scenarios), running each twice yields n=24.

**Option 2: Add more scenarios.** Write additional scenario YAML entries. For example, add 5 more `engineer-parallel` scenarios. This takes 1-2 hours per stratum but produces genuinely distinct scenarios.

**Option 3: Relax grouping.** Combine all positive Phase 2 strata into a single "phase2-positive" group (27 scenarios). This is statistically defensible if the protocol applies uniformly across roles.

**Recommended approach:** Combine Option 1 (run each Tier 2 scenario 2x) with the grouping table above. This yields:

| Group | Scenarios x Runs | Total n | Sufficient? |
|---|---|---|---|
| basic | 60 x 1 | 60 | Yes |
| complex | 30 x 1 | 30 | Yes |
| adversarial | 5 x 3 | 15 | Yes |
| engineer | 12 x 2 | 24 | Yes |
| engineer-antipattern | 3 x 5 | 15 | Yes |
| qa | 7 x 3 | 21 | Yes |
| qa-antipattern | 3 x 5 | 15 | Yes |
| pipeline | 8 x 2 | 16 | Yes |
| pipeline-antipattern | 2 x 8 | 16 | Yes |

**Total Tier 2 LLM calls:** 60 + 30 + 15 + 24 + 15 + 21 + 15 + 16 + 16 = **212 calls** (vs. 130 with single runs).

### 6.3 Expected Number of Live Runs

| Tier | Scenarios | Runs per scenario | Total executions | Purpose |
|---|---|---|---|---|
| Tier 1 | 130 | 1 | 130 | Injection validation (no LLM) |
| Tier 2 | 130 | 1-3 (avg ~1.6) | ~212 | LLM-scored compliance |
| Tier 3 | 15-20 | 1 | 15-20 | Live PM observation |
| **Total** | | | **~360** | |

---

## 7. Cost Estimation

### 7.1 Tokens Per Scenario Type

| Component | Input tokens | Output tokens | Notes |
|---|---|---|---|
| TEAMMATE_PROTOCOL injection | ~800 | 0 | Fixed protocol text |
| Scenario prompt (avg) | ~200 | 0 | Varies by scenario |
| System prompt for Tier 2 | ~100 | 0 | Role instructions |
| Tier 2 response (Haiku) | 0 | ~500-1000 | Teammate response |
| **Total per Tier 2 call** | **~1,100** | **~750** | |

### 7.2 Per-Tier Cost Breakdown

**Tier 1: Automated injection validation**
- LLM calls: 0
- Cost: **$0.00**

**Tier 2: LLM-scored simulation (Claude 3.5 Haiku)**
- Haiku pricing: $0.80 / 1M input tokens, $4.00 / 1M output tokens
- Per call: (1,100 / 1M x $0.80) + (750 / 1M x $4.00) = $0.00088 + $0.003 = ~$0.004
- Total calls: ~212
- **Cost: ~$0.85**
- (With Sonnet instead of Haiku: ~$0.02/call x 212 = ~$4.24)

**Tier 3: Live PM observation**
- Each live scenario spawns the PM + 2-3 teammates
- PM input context: ~10K tokens, output: ~2K tokens
- Per teammate: ~5K input, ~1K output
- Per scenario (PM + 2 teammates): ~20K input + ~4K output
- Sonnet pricing: $3.00 / 1M input, $15.00 / 1M output
- Per scenario: (20K/1M x $3) + (4K/1M x $15) = $0.06 + $0.06 = ~$0.12
- But Agent Teams sessions often involve tool calls, expanding to ~$0.50-$2.00 per scenario
- 15-20 scenarios: **$7.50-$40.00**

### 7.3 Total Campaign Cost

| Tier | Low estimate | High estimate |
|---|---|---|
| Tier 1 | $0.00 | $0.00 |
| Tier 2 (Haiku) | $0.85 | $4.24 (Sonnet) |
| Tier 3 (15-20 live) | $7.50 | $40.00 |
| **Total** | **$8.35** | **$44.24** |

**Budget recommendation:** Allocate $65 to cover Tier 2 with Sonnet, Tier 3 with 20 scenarios, and a 50% contingency buffer for retries and debugging.

---

## 8. Timeline

| Day | Activity | Deliverables |
|---|---|---|
| **Day 1** | WP-V1: Update audit script (dynamic strata, grouping) | Updated `audit_agent_teams_compliance.py`, new tests |
| **Day 1** | WP-V3 (partial): Add response capture to compliance log | Updated `event_handlers.py`, manual scoring CLI |
| **Day 2** | WP-V2: Build Tier 2 live runner | `live_runner.py` with Tier 1 and Tier 2 modes |
| **Day 2** | WP-V4 Tier 1: Run automated injection validation | 130 Tier 1 compliance records |
| **Day 3** | WP-V4 Tier 2: Run LLM-scored simulation | ~212 Tier 2 compliance records |
| **Day 3** | Checkpoint: Evaluate Tier 2 results, fix issues | Intermediate gate report |
| **Day 4** | WP-V2 (Tier 3): Generate manual prompt sheets | `tier3-prompts.md` |
| **Day 4-5** | WP-V4 Tier 3: Live PM observation (15-20 scenarios) | 15-20 Tier 3 compliance records |
| **Day 5** | WP-V5: Final gate evaluation and documentation | Gate pass/fail report, archived logs |

**Critical path:** WP-V1 -> WP-V2 -> WP-V4 (Tier 2) -> WP-V5
**Parallelizable:** WP-V3 can proceed alongside WP-V2. Tier 3 can run after Tier 2 checkpoint.

---

## 9. Risks

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **PM does not spawn teams for Tier 3 scenarios** -- the PM may decide a task is better handled solo. | Medium | High -- no live team data for that stratum | Select scenarios with clear multi-agent decomposition cues. Include "have two engineers work in parallel" in the prompt. Accept that PM autonomy means some runs will not produce team spawns. |
| R2 | **Haiku produces lower-quality responses than real teammates** -- Tier 2 uses Haiku for cost, but real teammates use Sonnet/Opus. | Medium | Medium -- Tier 2 compliance rates may not reflect production. | Run a subset (10-20 scenarios) with Sonnet for comparison. If compliance rates differ significantly, use Sonnet for the full Tier 2 run. |
| R3 | **Compliance scorer has false negatives on real responses** -- the regex-based scorer was tuned for synthetic responses. | Medium | Medium -- legitimate responses scored as non-compliant. | Manually review all scored-as-non-compliant Tier 3 responses. Update scorer patterns if false negatives found. |
| R4 | **Stratum grouping is challenged in review** -- grouping `engineer-parallel` and `engineer-merge` may be questioned. | Low | Medium -- may need per-stratum evidence. | Document the grouping rationale (shared TEAMMATE_PROTOCOL, same scoring criteria). Offer to run additional scenarios for ungrouped evaluation if requested. |
| R5 | **API rate limits or outages during Tier 2** | Low | Low -- delays but no data loss. | Implement retry with exponential backoff. Save progress after each scenario. Support `--resume` flag. |
| R6 | **Gate fails for some strata after full campaign** | Medium | High -- cannot declare Phase 2 verified. | Plan for iterative fixes: update protocol text, add scorer patterns, increase n. Budget 1-2 extra days for remediation. |
| R7 | **Cost overrun in Tier 3** -- complex scenarios with many tool calls could exceed budget. | Low | Medium | Implement per-session cost tracking. Set `--max-cost` guardrail. Cancel sessions approaching budget limit. |

---

## 10. Acceptance Criteria (What Constitutes "Gate Passed")

### 10.1 Formal Gate Criterion

```
For EVERY stratum group:
  n >= 10  AND  clopper_pearson_ci(k, n, alpha=0.05).lower > 0.70
```

Where:
- `n` = number of scored compliance records for that group
- `k` = number of records where ALL applicable scoring criteria pass
- "applicable" means: for positive strata, all 5 criteria must be true; for anti-pattern strata, at least 1 criterion must be false (detection test)

### 10.2 Evidence Requirements

The gate evaluation must be accompanied by:

1. **Compliance log archive** -- all JSONL files from `~/.claude-mpm/compliance/` covering the verification campaign, archived to `docs-local/mpm-agent-teams/07-phase-3-verificaton-plan/compliance-archive/`.

2. **Gate evaluation output** -- the full output of:
   ```bash
   python scripts/audit_agent_teams_compliance.py --gate --report
   ```

3. **Tier 3 observation log** -- for each live scenario:
   - Scenario ID and stratum
   - Whether PM spawned a team (Y/N)
   - Number of teammates spawned (actual vs. expected)
   - Whether worktree isolation was used (for engineer strata)
   - Teammate response text (or file path)
   - Compliance scores
   - Any anomalies or observations

4. **Summary statistics** -- per-group table:

   | Group | n | k | Rate | CI lower | CI upper | Gate |
   |---|---|---|---|---|---|---|
   | basic | 60 | 60 | 100% | 0.940 | 1.000 | PASS |
   | engineer | 24 | 24 | 100% | 0.858 | 1.000 | PASS |
   | ... | | | | | | |

### 10.3 Secondary Criteria (Not Blocking, But Tracked)

- **Tier 3 PM behavior compliance:** >= 80% of live scenarios should show correct PM decomposition (team spawn when expected, correct number of teammates, appropriate role assignment).
- **Scorer false-negative rate:** Manual review of <= 5 scored-as-non-compliant responses shows 0 false negatives.
- **Cross-tier consistency:** Tier 2 and Tier 3 compliance rates for the same stratum should not differ by more than 20 percentage points.

### 10.4 Gate Failure Resolution

If the gate fails:

1. Identify the failing stratum group(s).
2. For each failing group, categorize failure:
   - **Insufficient n:** Run more scenarios (increase repetitions or add YAML entries).
   - **Low compliance rate (scorer issue):** Manually review responses. Update scorer regex if false negatives. Re-score and re-evaluate.
   - **Low compliance rate (protocol issue):** The TEAMMATE_PROTOCOL instructions are insufficient. Update the protocol text in `teammate_context_injector.py`, then re-run affected strata.
   - **Low compliance rate (model issue):** Haiku may not follow the protocol as well as Sonnet. Switch to Sonnet for Tier 2 and re-run.
3. Re-run only the affected groups.
4. Re-evaluate the gate.
5. Document the iteration in the gate results file.

---

## Appendix A: Complete Stratum Inventory

| Stratum | Category | Scenarios | Expected behavior | Evaluation type |
|---|---|---|---|---|
| trivial | Phase 1 | 30 | Single researcher, basic task | Positive (all criteria pass) |
| medium | Phase 1 | 30 | Single researcher, moderate complexity | Positive |
| complex | Phase 1 | 30 | Multi-step research, high complexity | Positive |
| adversarial | Phase 1 | 5 | Non-compliant patterns | Negative (at least 1 criterion fails) |
| engineer-parallel | Phase 2 | 5 | PM spawns 2-3 engineers, parallel work, worktree isolation | Positive |
| engineer-merge | Phase 2 | 4 | PM delegates merge to one engineer after parallel work | Positive |
| engineer-antipattern | Phase 2 | 3 | Non-compliant engineering patterns | Negative |
| engineer-recovery | Phase 2 | 3 | Error recovery in engineering workflow | Positive |
| qa-pipeline | Phase 2 | 4 | QA teammate validates engineer output | Positive |
| qa-protocol | Phase 2 | 3 | QA follows structured validation protocol | Positive |
| qa-antipattern | Phase 2 | 3 | Non-compliant QA patterns | Negative |
| research-then-eng | Phase 2 | 3 | Sequential: Research phase then Engineering phase | Positive |
| eng-then-qa | Phase 2 | 3 | Sequential: Engineering phase then QA phase | Positive |
| full-pipeline | Phase 2 | 2 | Full 3-phase: Research -> Engineering -> QA | Positive |
| pipeline-antipattern | Phase 2 | 2 | Non-compliant pipeline orchestration | Negative |

## Appendix B: File Inventory

| File | Role in verification |
|---|---|
| `scripts/audit_agent_teams_compliance.py` | Gate evaluation (WP-V1 target) |
| `src/claude_mpm/hooks/claude_hooks/event_handlers.py` | Compliance logging (WP-V3 target) |
| `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` | Injection source for Tier 2 prompts |
| `tests/manual/agent_teams_battery/test_battery.py` | Synthetic battery + live battery placeholder |
| `tests/manual/agent_teams_battery/scoring/compliance_scorer.py` | Response scoring (5 criteria) |
| `tests/manual/agent_teams_battery/scenarios/*.yaml` | 130 scenario definitions |
| `tests/manual/agent_teams_battery/conftest.py` | `--live` flag, env var skip |
| `tests/manual/agent_teams_battery/live_runner.py` | NEW: Tier 2/3 runner (WP-V2) |
| `tests/manual/agent_teams_battery/score_response.py` | NEW: Manual response scorer (WP-V3) |
| `~/.claude-mpm/compliance/agent-teams-*.jsonl` | Compliance data accumulation |

## Appendix C: Minimal Viable Verification (If Time-Constrained)

If the full 5-day plan is not feasible, the following 2-day minimal path achieves a provisional gate:

**Day 1:**
1. WP-V1: Update audit script (2 hours)
2. WP-V2 (Tier 2 only): Build live runner without Tier 3 support (4 hours)
3. WP-V4 (Tier 2): Run LLM-scored simulation for all scenarios x2 (~212 calls, ~$1-5)

**Day 2:**
1. Review Tier 2 results, fix any scorer issues
2. WP-V5: Run gate evaluation
3. Document results as "Provisional Gate -- Tier 2 only, pending Tier 3 live validation"

This defers Tier 3 live PM observation but provides statistical evidence that the TEAMMATE_PROTOCOL produces compliant responses across all 15 strata. Tier 3 can be executed later as a confirmatory step.

**Cost: ~$5-10 | Duration: 2 days | Coverage: Tier 1 + Tier 2**
