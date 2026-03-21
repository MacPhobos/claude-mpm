# Adjusted Verification Plan: Phase 2 Gate Evaluation

**Date:** 2026-03-21
**Branch:** mpm-teams
**Predecessor:** `00_verification_plan.md` (original), `01_devils_advocate.md` (review)
**Status:** Ready for execution

---

## 1. Executive Summary

This plan addresses all 4 MUST-FIX and 1 RETHINK findings from the devil's advocate review. The key changes from the original plan:

1. **Gate uses 3 strata** (Research, Engineer, QA) with n >= 30, matching the original implementation plan Section 8
2. **Gate evaluates scored response data**, not injection events
3. **New scenarios written** (not duplicate runs) to reach sufficient n
4. **Two-gate system**: Gate A (statistical, response compliance) + Gate B (qualitative, PM behavior)
5. **Minimal tooling**: 50-100 line script, not a feature-rich CLI

**Timeline:** 2 days
**Cost:** $5-15 in API calls
**Tooling debt:** Near zero

---

## 2. Gate Definition (Reconciled with Implementation Plan Section 8)

### Gate A: Response Compliance (Statistical)

**Metric:** Clopper-Pearson 95% CI lower bound on compliance rate
**Threshold:** > 0.70
**Minimum n:** 15 per stratum (mathematical: n=11 passes at 100%; practical: n=15 gives margin)
**Strata:** 3 broad strata matching original implementation plan:

| Stratum | Scenario Sources | Current n | Target n |
|---------|-----------------|-----------|----------|
| **Research** | trivial (30), medium (30), complex (30), adversarial (5), research-then-eng (3) | 98 | >= 30 (already met) |
| **Engineer** | engineer-parallel (5), engineer-antipattern (3), engineer-merge (4), engineer-recovery (3), eng-then-qa (3) | 18 | >= 30 (need 12 more) |
| **QA** | qa-pipeline (4), qa-antipattern (3), qa-protocol (3), full-pipeline (2), pipeline-antipattern (2) | 14 | >= 30 (need 16 more) |

**Action:** Write 28 new scenario YAML entries (12 Engineer + 16 QA) to reach n >= 30 per stratum without duplicate runs.

### Gate B: PM Behavioral Compliance (Qualitative)

**Metric:** Structured observation checklist
**Sample:** 3-5 live Claude Code sessions with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
**Blocking:** Yes — both Gate A and Gate B must pass

**PM Behavioral Checklist (all must be observed at least once):**

| # | Behavior | Observation Method | Required |
|---|----------|-------------------|----------|
| 1 | PM spawns 2+ Engineers with `isolation: "worktree"` | Live session: engineer-parallel scenario | YES |
| 2 | PM delegates merge to Version Control / Local Ops agent | Live session: engineer-merge scenario | YES |
| 3 | PM runs `make test` after merge (single command, not multi-step) | Live session: post-merge | YES |
| 4 | PM sequences Research phase before Engineer phase (no mixing) | Live session: research-then-engineer pipeline | YES |
| 5 | PM delegates worktree cleanup (not running 4+ git commands directly) | Live session: any engineer team session | YES |
| 6 | PM does NOT spawn teams for tasks under 15-minute threshold | Live session: trivial engineering task | YES |

**Evidence format:** Screenshot or transcript excerpt for each checklist item, with session ID and timestamp.

---

## 3. Work Packages

### WP-V1: Audit Script Update (2-3 hours)

**File:** `scripts/audit_agent_teams_compliance.py`

Changes:
1. Replace hardcoded `["trivial", "medium", "complex"]` loop (line 120) with dynamic stratum discovery from log data
2. Add stratum mapping: map fine-grained strata to 3 broad strata:
   ```python
   STRATUM_MAP = {
       # Research
       "trivial": "research", "medium": "research", "complex": "research",
       "adversarial": "research", "research-then-eng": "research",
       # Engineer
       "engineer-parallel": "engineer", "engineer-antipattern": "engineer",
       "engineer-merge": "engineer", "engineer-recovery": "engineer",
       "eng-then-qa": "engineer",
       # QA
       "qa-pipeline": "qa", "qa-antipattern": "qa", "qa-protocol": "qa",
       "full-pipeline": "qa", "pipeline-antipattern": "qa",
   }
   ```
3. Add support for `response_scored` event type alongside `injection` events
4. When `response_scored` records exist, use them for gate evaluation instead of `injection` records
5. Update threshold from n >= 10 to n >= 15

**Verification:** Run with `--gate` on existing test data; verify 3 strata reported.

### WP-V2: Write New Scenarios (2 hours)

Add 28 new scenario YAML entries across existing files:

| File | Current Count | New Entries | Target Count |
|------|--------------|-------------|-------------|
| `engineer.yaml` | 15 | 12 | 27 |
| `qa.yaml` | 10 | 8 | 18 |
| `pipeline.yaml` | 10 | 8 | 18 |

New scenario guidelines:
- Each scenario must be **genuinely distinct** (different subsystems, different failure modes, different pipeline structures)
- Not prompt paraphrases — structurally different tasks
- Follow existing YAML schema with `roles` field
- Include a mix of positive (team_spawn) and negative (single_agent) expected behaviors

### WP-V3: Phase 2 Scoring Criteria (1-2 hours)

**File:** `tests/manual/agent_teams_battery/scoring/compliance_scorer.py`

Add 3 new Phase 2 criteria (only evaluated when `role` matches):

```python
# Criterion 6: Git diff summary present (engineer only)
if role.lower() == "engineer":
    git_diff_present = bool(
        re.search(r"(insertion|deletion|files?\s+changed|\+\d+.*-\d+|diff\s+--git)", response_lower)
    )
else:
    git_diff_present = True  # N/A for non-engineers

# Criterion 7: Scope declaration present (engineer only)
if role.lower() == "engineer":
    scope_declared = bool(
        re.search(r"(scope|modify only|intended files|file scope|target files)", response_lower)
    )
else:
    scope_declared = True  # N/A for non-engineers

# Criterion 8: Full test output present (QA only)
if role.lower() in ("qa", "qa-agent"):
    test_output_present = bool(
        re.search(r"(passed|failed|error).*\d+|test.*result|pytest|jest|make test", response_lower)
    )
else:
    test_output_present = True  # N/A for non-QA
```

Update return dict to include new criteria. Update `generate_compliant_response()` in test_battery.py to include diff summaries for engineers and test output for QA.

### WP-V4: Minimal Scorer Script (2-3 hours)

**File:** `scripts/run_compliance_battery.py` (new, ~80 lines)

```python
#!/usr/bin/env python3
"""Minimal compliance battery runner — calls Haiku, scores responses, logs results."""

import json, os, sys, time, yaml
from pathlib import Path
from anthropic import Anthropic

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tests/manual/agent_teams_battery"))

from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
    TEAMMATE_PROTOCOL_BASE, _ROLE_ADDENDA,
)
from scoring.compliance_scorer import score_response

SCENARIOS_DIR = Path(__file__).parent.parent / "tests/manual/agent_teams_battery/scenarios"
LOG_DIR = Path.home() / ".claude-mpm" / "compliance"
STRATUM_MAP = {
    "trivial": "research", "medium": "research", "complex": "research",
    "adversarial": "research", "research-then-eng": "research",
    "engineer-parallel": "engineer", "engineer-antipattern": "engineer",
    "engineer-merge": "engineer", "engineer-recovery": "engineer",
    "eng-then-qa": "engineer",
    "qa-pipeline": "qa", "qa-antipattern": "qa", "qa-protocol": "qa",
    "full-pipeline": "qa", "pipeline-antipattern": "qa",
}

def load_scenarios():
    scenarios = []
    for f in sorted(SCENARIOS_DIR.glob("*.yaml")):
        scenarios.extend(yaml.safe_load(open(f)) or [])
    return scenarios

def build_prompt(scenario):
    roles = scenario.get("roles", ["research"])
    role = roles[0] if roles else "research"
    protocol = TEAMMATE_PROTOCOL_BASE
    addendum = _ROLE_ADDENDA.get(role.lower(), "")
    if addendum:
        protocol += "\n\n" + addendum
    return protocol + "\n\n---\n\n" + scenario["prompt"], role

def main():
    client = Anthropic()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"agent-teams-battery-{time.strftime('%Y-%m-%d')}.jsonl"

    strata_filter = sys.argv[1:] if len(sys.argv) > 1 else None
    scenarios = load_scenarios()
    if strata_filter:
        scenarios = [s for s in scenarios if s["stratum"] in strata_filter]

    total = len(scenarios)
    for i, scenario in enumerate(scenarios, 1):
        prompt, role = build_prompt(scenario)
        broad_stratum = STRATUM_MAP.get(scenario["stratum"], "research")
        print(f"[{i}/{total}] {scenario['id']} (stratum={broad_stratum}, role={role})")

        response = client.messages.create(
            model="claude-haiku-4-20250414",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text

        files_modified = scenario.get("scoring_criteria", {}).get("manifest_required", False)
        scores = score_response(response_text, files_modified=files_modified, role=role)
        all_pass = all(scores.values())

        record = {
            "event_type": "response_scored",
            "scenario_id": scenario["id"],
            "stratum": broad_stratum,
            "fine_stratum": scenario["stratum"],
            "role": role,
            "scores": scores,
            "all_criteria_pass": all_pass,
            "model": "claude-haiku-4-20250414",
            "response_length": len(response_text),
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(record) + "\n")

        status = "PASS" if all_pass else f"FAIL ({[k for k,v in scores.items() if not v]})"
        print(f"  -> {status}")
        time.sleep(0.3)  # Rate limiting

    print(f"\nDone. {total} scenarios scored. Log: {log_file}")

if __name__ == "__main__":
    main()
```

**No CLI framework, no resume, no cost tracking.** Just a loop. Disposable tooling.

### WP-V5: Execution Campaign (4-6 hours)

**Day 1: Automated (Tier 1+2)**
1. Run `python scripts/run_compliance_battery.py` (~30 min, ~$1-2)
2. Review failures: are they real compliance issues or scorer false negatives?
3. If scorer FP rate > 10%: tune scoring regexes, re-run
4. Run `python scripts/audit_agent_teams_compliance.py --gate`

**Day 2: Live PM Observation (Tier 3)**
5. Open 3-5 Claude Code sessions with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
6. Present one scenario from each critical category:
   - Engineer-parallel: "Refactor auth and payments subsystems independently"
   - Engineer-merge: post-merge scenario
   - Full-pipeline: research → engineer → QA
   - Recovery: timeout/failure scenario
7. Observe and document PM behavior against Gate B checklist
8. Run final `--gate` evaluation
9. Write results document

### WP-V6: Results Document (1-2 hours)

**File:** `docs-local/mpm-agent-teams/07-phase-3-verificaton-plan/03_gate_results.md`

Template:
```
# Phase 2 Gate Results

## Gate A: Response Compliance (Statistical)
- Research: n=X, k=Y, rate=Z%, CI=[L, U], PASS/FAIL
- Engineer: n=X, k=Y, rate=Z%, CI=[L, U], PASS/FAIL
- QA: n=X, k=Y, rate=Z%, CI=[L, U], PASS/FAIL
- Overall: GATE A PASSED/FAILED

## Gate B: PM Behavioral (Qualitative)
- [x] PM spawns Engineers with worktree isolation (session ID, evidence)
- [x] PM delegates merge (session ID, evidence)
- [x] PM runs make test post-merge (session ID, evidence)
- [x] PM sequences pipeline phases (session ID, evidence)
- [x] PM delegates cleanup (session ID, evidence)
- [x] PM rejects team for small task (session ID, evidence)
- Overall: GATE B PASSED/FAILED

## Final Gate Status: PASSED/FAILED
```

---

## 4. Stratum Mapping Detail

### Why 3 Strata, Not 9

The original implementation plan (Section 8, line 765) specifies: "Combined battery has >= 30 data points per stratum (Research, Engineer, QA)." This 3-stratum scheme:

1. **Has sufficient n** — 98 Research, 30+ Engineer (after WP-V2), 30+ QA (after WP-V2)
2. **Avoids the non-independence problem** — Each data point is a distinct scenario, not a repeated run
3. **Tolerates failures** — At n=30, up to 3 failures still pass CI > 0.70 (CI lower ≈ 0.722)
4. **Matches the original gate** — No silent redefinition

### Mapping Table

| Fine Stratum | Broad Stratum | Rationale |
|---|---|---|
| trivial, medium, complex | Research | Phase 1 Research scenarios |
| adversarial | Research | Adversarial Research scenarios |
| research-then-eng | Research | Research phase of pipeline |
| engineer-parallel | Engineer | Engineer spawning |
| engineer-antipattern | Engineer | Engineer boundary conditions |
| engineer-merge | Engineer | Engineer merge protocol |
| engineer-recovery | Engineer | Engineer failure handling |
| eng-then-qa | Engineer | Engineer phase of pipeline |
| qa-pipeline | QA | QA pipeline orchestration |
| qa-antipattern | QA | QA boundary conditions |
| qa-protocol | QA | QA evidence quality |
| full-pipeline | QA | QA phase of full pipeline |
| pipeline-antipattern | QA | Pipeline boundary conditions |

---

## 5. Statistical Requirements

### Minimum n Analysis

| n | k (successes) | Compliance Rate | CI Lower | Passes > 0.70? |
|---|---|---|---|---|
| 15 | 15 | 100% | 0.7816 | YES |
| 15 | 14 | 93.3% | 0.6458 | NO |
| 20 | 20 | 100% | 0.8316 | YES |
| 20 | 19 | 95% | 0.7233 | YES |
| 20 | 18 | 90% | 0.6589 | NO |
| 30 | 30 | 100% | 0.8843 | YES |
| 30 | 29 | 96.7% | 0.8131 | YES |
| 30 | 28 | 93.3% | 0.7728 | YES |
| 30 | 27 | 90% | 0.7279 | YES |
| 30 | 26 | 86.7% | 0.6804 | NO |

**Conclusion:** At n=30 per stratum, the gate tolerates up to 3 failures (90% compliance rate) and still passes. This provides reasonable headroom for scorer false negatives or legitimately non-compliant responses.

---

## 6. Cost Estimation

| Item | Count | Unit Cost | Total |
|------|-------|-----------|-------|
| Haiku API calls (Tier 2) | ~160 scenarios | ~$0.005/call | ~$0.80 |
| Live PM sessions (Tier 3) | 3-5 sessions | ~$3-8/session | ~$9-40 |
| Scenario writing (human time) | 2 hours | $0 (self) | $0 |
| Tooling (human time) | 4-6 hours | $0 (self) | $0 |
| **Total API cost** | | | **$10-41** |
| **Contingency (30%)** | | | **$13-53** |

---

## 7. Timeline

| Day | Hours | Work | Deliverable |
|-----|-------|------|------------|
| 1 AM | 2-3h | WP-V1 (audit script) + WP-V3 (scorer criteria) | Updated audit + scorer |
| 1 PM | 2-3h | WP-V2 (new scenarios) + WP-V4 minimal script | 28 new YAMLs + runner script |
| 1 EVE | 1h | Run Tier 2 battery + initial gate check | JSONL data + gate output |
| 2 AM | 3-4h | WP-V5 live sessions (3-5 scenarios) | PM behavioral evidence |
| 2 PM | 1-2h | WP-V6 results document + final gate | Gate results document |

**Total: 2 days, 10-14 hours active work**

---

## 8. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | Haiku responses fail scorer regexes (false negatives) | Medium | Medium | Review first 10 responses manually; tune regexes before full run |
| 2 | PM ignores Agent Teams instructions in live sessions | Low | High | Use opus model for PM; provide explicit scenario prompts |
| 3 | Live session cost exceeds budget | Low | Low | Cap at 5 sessions; $53 total budget |
| 4 | Agent Teams env var not working in current Claude Code version | Low | High | Test with 1 scenario first before committing to full campaign |
| 5 | Scorer criteria too strict for real responses | Medium | Medium | Accept 70% threshold; review failures individually |

---

## 9. Acceptance Criteria

### Gate A: Response Compliance (BLOCKING)

All 3 strata must pass:
- **Research:** n >= 30, CI lower > 0.70
- **Engineer:** n >= 30, CI lower > 0.70
- **QA:** n >= 30, CI lower > 0.70

Command: `python scripts/audit_agent_teams_compliance.py --gate`
Exit code 0 = PASS, 1 = FAIL.

### Gate B: PM Behavioral (BLOCKING)

All 6 checklist items observed at least once:
1. PM spawns Engineers with worktree isolation
2. PM delegates merge to VC/Ops agent
3. PM runs make test post-merge
4. PM sequences pipeline phases
5. PM delegates worktree cleanup
6. PM rejects team for sub-threshold task

Evidence: transcript excerpts or screenshots per item.

### Overall: BOTH Gate A AND Gate B must pass.

---

## 10. Differences from Original Plan

| Aspect | Original Plan (00) | Adjusted Plan (02) | Reason |
|--------|-------------------|-------------------|--------|
| Strata | 9 groups, n>=10 | 3 groups, n>=30 | Match original impl plan Section 8 |
| Gate metric | Injection events | Scored responses | Injection is deterministic; measure the stochastic part |
| Tooling | Feature-rich CLI | 80-line script | Disposable; avoid scope creep |
| PM behavior | Secondary, non-blocking | Required, qualitative gate | Core Phase 2 deliverable |
| Duplicate runs | Same scenario 3-8x | Write new scenarios | Statistical independence |
| Timeline | 3-5 days | 2 days | Simplified tooling |
| Cost | $30-65 | $10-53 | Fewer live sessions, simpler tooling |
| Tier 2 framing | "LLM-scored simulation" | "Haiku instruction-following test" | Honest about what it measures |
