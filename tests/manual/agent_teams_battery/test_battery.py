#!/usr/bin/env python3
"""Agent Teams compliance battery test runner.

Exercises the compliance measurement pipeline: scenario loading ->
response scoring -> compliance logging -> audit evaluation.

Default mode: pipeline validation with synthetic responses (fast, no LLM).
Future mode: live Agent Teams teammate spawning (slow, requires Claude Code).

Run via: make test-agent-teams
"""

import json
import os
import sys
from pathlib import Path

import pytest
import yaml

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from audit_agent_teams_compliance import (
    GATE_STRATA,
    clopper_pearson_ci,
    count_teammates_per_team,
    evaluate_gate1,
    load_compliance_logs,
)
from scoring.compliance_scorer import score_response

# ============================================================================
# Fixtures
# ============================================================================

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


def load_all_scenarios():
    """Load all scenario YAML files and return flat list."""
    scenarios = []
    for yaml_file in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            file_scenarios = yaml.safe_load(f)
        if file_scenarios:
            scenarios.extend(file_scenarios)
    return scenarios


ALL_SCENARIOS = load_all_scenarios()


def generate_compliant_response(scenario: dict) -> str:
    """Generate a synthetic compliant teammate response for a scenario."""
    scenario_id = scenario.get("id", "unknown")
    scenario_roles = scenario.get("roles", ["research"])
    primary_role = scenario_roles[0] if scenario_roles else "research"

    if primary_role == "engineer":
        response = f"""## Implementation: {scenario_id}

**Scope:** Modifying only files in `src/hooks/` and `src/agents/` for this task.

### Changes Made

I modified the following files:

- `/src/claude_mpm/hooks/claude_hooks/event_handlers.py` (lines 120-145): Added role routing logic
- `/src/claude_mpm/agents/PM_INSTRUCTIONS.md` (lines 1135-1200): Updated Agent Teams section

### Commands Executed

```
ruff check src/claude_mpm/hooks/claude_hooks/event_handlers.py
```

Output:
```
All checks passed!
```

### Git Diff Summary

3 files changed, 45 insertions(+), 12 deletions(-)

### Files Changed
- src/claude_mpm/hooks/claude_hooks/event_handlers.py: modified (added role routing)
- src/claude_mpm/agents/PM_INSTRUCTIONS.md: modified (expanded Agent Teams section)
- tests/hooks/test_teammate_context_injector.py: modified (added role tests)

QA verification has not been performed.

I completed this implementation independently using available tools."""
    elif primary_role in ("qa", "qa-agent"):
        response = f"""## QA Verification: {scenario_id}

### Verification Scope

Verifying Engineer A's changes to `src/hooks/` and Engineer B's changes to `src/agents/`.

### Test Execution

```
pytest tests/ -v --tb=short
```

Output:
```
tests/hooks/test_teammate_context_injector.py::TestTeammateContextInjector::test_injection_when_team_name_present PASSED
tests/hooks/test_teammate_context_injector.py::TestPhase2RoleAddenda::test_engineer_addendum_injected PASSED
tests/hooks/test_teammate_context_injector.py::TestPhase2RoleAddenda::test_qa_addendum_injected PASSED
...
41 passed, 0 failed in 0.28s
```

### Test Results

- 41 passed, 0 failed
- No regressions detected
- All Phase 2 role routing tests pass

### Evidence

- `/src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py`: Verified role addenda injection
- `/tests/hooks/test_teammate_context_injector.py` (line 380): Confirmed test coverage

I completed this verification independently on the merged code."""
    else:
        response = f"""## Research Findings: {scenario_id}

### Investigation

I examined the relevant source files for this investigation:

- `/src/claude_mpm/hooks/claude_hooks/event_handlers.py` (lines 1-50): Module imports and configuration
- `/src/claude_mpm/core/constants.py` (line 12): Timeout configuration values

### Commands Executed

```
grep -r "def handle_" src/claude_mpm/hooks/ --include="*.py" | head -5
```

Output:
```
src/claude_mpm/hooks/claude_hooks/event_handlers.py:337:    def handle_pre_tool_fast(self, event):
src/claude_mpm/hooks/claude_hooks/event_handlers.py:524:    def handle_post_tool_fast(self, event):
```

### Key Findings

1. The hook handler uses a singleton pattern (line 167 of hook_handler.py)
2. Event dispatch routes through a dict mapping at line 540
3. All handlers follow the `handle_<event>_fast` naming convention

### Files Changed
- docs/research/investigation-{scenario_id}.md: created (analysis report)

I completed this investigation independently using grep and file reading tools."""

    return response


def generate_non_compliant_response(scenario: dict) -> str:
    """Generate a synthetic non-compliant response (for adversarial testing)."""
    return f"""I looked at the code for {scenario.get("id", "the task")} and it appears to be working fine.
The implementation looks correct and everything should work after the changes.
I believe this fixes the issues mentioned in the prompt.

You might want to ask Engineer to do a more thorough review of the code quality."""


# ============================================================================
# Pipeline Validation Tests (synthetic responses)
# ============================================================================


class TestBatteryPipelineValidation:
    """Validate the compliance pipeline with synthetic responses.

    These tests do NOT call live LLMs. They exercise:
    scenario YAML -> synthetic response -> scorer -> compliance log -> audit.
    """

    @pytest.fixture(autouse=True)
    def setup_compliance_dir(self, tmp_path, monkeypatch):
        """Redirect compliance logs to tmp_path for test isolation."""
        self.compliance_dir = tmp_path / "compliance"
        monkeypatch.setattr(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            self.compliance_dir,
        )
        self.compliance_dir.mkdir(parents=True, exist_ok=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "trivial"],
        ids=[s["id"] for s in ALL_SCENARIOS if s.get("stratum") == "trivial"],
    )
    def test_trivial_scenario(self, scenario, monkeypatch):
        """Trivial scenario: synthetic compliant response scores correctly."""
        monkeypatch.setenv("CLAUDE_MPM_COMPLIANCE_STRATUM", "trivial")
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "medium"],
        ids=[s["id"] for s in ALL_SCENARIOS if s.get("stratum") == "medium"],
    )
    def test_medium_scenario(self, scenario, monkeypatch):
        """Medium scenario: synthetic compliant response scores correctly."""
        monkeypatch.setenv("CLAUDE_MPM_COMPLIANCE_STRATUM", "medium")
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "complex"],
        ids=[s["id"] for s in ALL_SCENARIOS if s.get("stratum") == "complex"],
    )
    def test_complex_scenario(self, scenario, monkeypatch):
        """Complex scenario: synthetic compliant response scores correctly."""
        monkeypatch.setenv("CLAUDE_MPM_COMPLIANCE_STRATUM", "complex")
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "adversarial"],
        ids=[s["id"] for s in ALL_SCENARIOS if s.get("stratum") == "adversarial"],
    )
    def test_adversarial_scenario(self, scenario, monkeypatch):
        """Adversarial scenario: non-compliant response detected correctly."""
        monkeypatch.setenv("CLAUDE_MPM_COMPLIANCE_STRATUM", "adversarial")
        self._run_scenario(scenario, compliant=False)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "engineer-parallel"],
        ids=lambda s: s["id"],
    )
    def test_engineer_parallel_scenarios(self, scenario):
        """Engineer parallel scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "engineer-antipattern"],
        ids=lambda s: s["id"],
    )
    def test_engineer_antipattern_scenarios(self, scenario):
        """Engineer anti-pattern scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=False)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "engineer-merge"],
        ids=lambda s: s["id"],
    )
    def test_engineer_merge_scenarios(self, scenario):
        """Engineer merge scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "engineer-recovery"],
        ids=lambda s: s["id"],
    )
    def test_engineer_recovery_scenarios(self, scenario):
        """Engineer recovery scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "qa-pipeline"],
        ids=lambda s: s["id"],
    )
    def test_qa_pipeline_scenarios(self, scenario):
        """QA pipeline scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "qa-antipattern"],
        ids=lambda s: s["id"],
    )
    def test_qa_antipattern_scenarios(self, scenario):
        """QA anti-pattern scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=False)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "qa-protocol"],
        ids=lambda s: s["id"],
    )
    def test_qa_protocol_scenarios(self, scenario):
        """QA protocol scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "research-then-eng"],
        ids=lambda s: s["id"],
    )
    def test_research_then_eng_scenarios(self, scenario):
        """Research-then-Engineer pipeline scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "eng-then-qa"],
        ids=lambda s: s["id"],
    )
    def test_eng_then_qa_scenarios(self, scenario):
        """Engineer-then-QA pipeline scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "full-pipeline"],
        ids=lambda s: s["id"],
    )
    def test_full_pipeline_scenarios(self, scenario):
        """Full 3-phase pipeline scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=True)

    @pytest.mark.parametrize(
        "scenario",
        [s for s in ALL_SCENARIOS if s.get("stratum") == "pipeline-antipattern"],
        ids=lambda s: s["id"],
    )
    def test_pipeline_antipattern_scenarios(self, scenario):
        """Pipeline anti-pattern scenarios produce compliant responses."""
        self._run_scenario(scenario, compliant=False)

    def _run_scenario(self, scenario: dict, compliant: bool):
        """Execute a single scenario through the compliance pipeline."""
        from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

        scenario_id = scenario["id"]
        stratum = scenario["stratum"]
        criteria = scenario.get("scoring_criteria", {})

        # Generate synthetic response
        if compliant:
            response = generate_compliant_response(scenario)
        else:
            response = generate_non_compliant_response(scenario)

        # Score the response
        files_modified = criteria.get("manifest_required", False)
        # Extract role for scoring (first role in the list, or default to "research")
        scenario_roles = scenario.get("roles", ["research"])
        primary_role = scenario_roles[0] if scenario_roles else "research"
        scores = score_response(
            response, files_modified=files_modified, role=primary_role
        )

        # Write compliance log record
        _compliance_log(
            {
                "event_type": "injection",
                "session_id": f"battery-{scenario_id}",
                "team_name": f"battery-team-{stratum}",
                "subagent_type": primary_role,
                "teammate_name": f"researcher-{scenario_id}",
                "injection_applied": True,
                "stratum": stratum,
                "scores": scores,
            }
        )

        # Validate scoring results
        if compliant:
            if criteria.get("evidence_required", True):
                assert scores["evidence_present"], (
                    f"{scenario_id}: Compliant response should have evidence"
                )
            if criteria.get("forbidden_phrases", True):
                assert scores["forbidden_phrases_absent"], (
                    f"{scenario_id}: Compliant response should have no forbidden phrases"
                )
            assert scores["no_peer_delegation"], (
                f"{scenario_id}: Compliant response should have no peer delegation"
            )
        else:
            # Adversarial non-compliant responses should fail at least one criterion
            failed_criteria = [k for k, v in scores.items() if not v]
            assert len(failed_criteria) > 0, (
                f"{scenario_id}: Non-compliant response should fail at least one criterion"
            )


class TestGate1Evaluation:
    """Run Gate 1 evaluation after pipeline validation."""

    @pytest.fixture(autouse=True)
    def setup_compliance_logs(self, tmp_path):
        """Create synthetic compliance logs for Gate 1 evaluation."""
        self.compliance_dir = tmp_path / "compliance"
        self.compliance_dir.mkdir(parents=True, exist_ok=True)

        # Write 30 successful injection records per broad gate stratum
        records = []
        for stratum in GATE_STRATA:
            for i in range(30):
                records.append(
                    {
                        "event_type": "injection",
                        "stratum": stratum,
                        "injection_applied": True,
                        "session_id": f"gate1-{stratum}-{i}",
                        "team_name": f"gate1-team-{stratum}",
                        "timestamp": "2026-03-20T12:00:00+00:00",
                    }
                )

        log_file = self.compliance_dir / "agent-teams-2026-03-20.jsonl"
        log_file.write_text("\n".join(json.dumps(r) for r in records))

    def test_gate1_passes_with_full_compliance(self):
        """Gate 1 passes when all broad strata have n=30 with 100% injection success."""
        records = load_compliance_logs(self.compliance_dir)
        assert len(records) == 90

        results = evaluate_gate1(records)
        for stratum in GATE_STRATA:
            assert results[stratum]["passed"] is True, (
                f"Gate 1 failed for {stratum}: "
                f"n={results[stratum]['n']}, k={results[stratum]['k']}, "
                f"CI=[{results[stratum]['ci_lower']:.3f}, {results[stratum]['ci_upper']:.3f}]"
            )
            assert results[stratum]["data_source"] == "injection"

    def test_gate1_reports_teammate_counts(self):
        """Audit script correctly counts teammates per team from logs."""
        records = load_compliance_logs(self.compliance_dir)
        team_counts = count_teammates_per_team(records)

        for stratum in GATE_STRATA:
            assert team_counts[f"gate1-team-{stratum}"] == 30


class TestLiveBattery:
    """Live Agent Teams battery -- spawns actual teammates.

    NOT IMPLEMENTED. Placeholder for future live battery execution.
    Run with: pytest tests/manual/agent_teams_battery/ --live
    """

    @pytest.fixture(autouse=True)
    def skip_unless_live(self, request):
        """Skip live tests unless --live flag is passed."""
        if not request.config.getoption("--live", default=False):
            pytest.skip("Live battery requires --live flag")

    def test_live_trivial_placeholder(self):
        """Placeholder: live trivial scenario execution."""
        pytest.skip("Live battery not implemented -- future Phase 1.5 work")
