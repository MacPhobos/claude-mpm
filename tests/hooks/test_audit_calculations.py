#!/usr/bin/env python3
"""Tests for Agent Teams compliance audit calculations.

Validates Clopper-Pearson CI calculations and teammate counting
from JSONL compliance log records.
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path for audit module import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from audit_agent_teams_compliance import (
    GATE_STRATA,
    STRATUM_MAP,
    clopper_pearson_ci,
    count_teammates_per_team,
    evaluate_gate1,
    load_compliance_logs,
)


class TestClopperPearsonCI:
    """Tests for the Clopper-Pearson exact CI calculation."""

    def test_ci_perfect_compliance(self):
        """n=30, k=30: lower bound should be > 0.88."""
        lower, upper = clopper_pearson_ci(30, 30)
        assert lower > 0.88, f"Lower bound {lower:.4f} should be > 0.88"
        assert upper == 1.0

    def test_ci_high_compliance(self):
        """n=30, k=27: lower bound should be > 0.70 (Gate 1 pass)."""
        lower, _upper = clopper_pearson_ci(27, 30)
        assert lower > 0.70, f"Lower bound {lower:.4f} should be > 0.70"

    def test_ci_borderline_compliance(self):
        """n=30, k=24: lower bound should be < 0.70 (Gate 1 fail)."""
        lower, _upper = clopper_pearson_ci(24, 30)
        assert lower < 0.70, f"Lower bound {lower:.4f} should be < 0.70"

    def test_ci_zero_compliance(self):
        """n=30, k=0: lower bound should be 0.0."""
        lower, upper = clopper_pearson_ci(0, 30)
        assert lower == 0.0
        assert upper < 0.15

    def test_ci_empty_stratum(self):
        """n=0: should return (0.0, 1.0)."""
        lower, upper = clopper_pearson_ci(0, 0)
        assert lower == 0.0
        assert upper == 1.0

    def test_ci_single_trial_success(self):
        """n=1, k=1: wide interval."""
        lower, upper = clopper_pearson_ci(1, 1)
        assert lower > 0.0
        assert upper == 1.0
        # With n=1 k=1, lower bound should be around 0.025
        assert lower < 0.10

    def test_ci_bounds_ordering(self):
        """Lower bound is always <= upper bound."""
        for n in [5, 10, 20, 30]:
            for k in range(n + 1):
                lower, upper = clopper_pearson_ci(k, n)
                assert lower <= upper, f"Bounds inverted for k={k}, n={n}"


class TestTeammateCountingFromJSONL:
    """Tests for counting teammates per team from compliance log records."""

    def test_count_teammates_per_team(self):
        """Count injection events grouped by team_name."""
        records = [
            {"event_type": "injection", "team_name": "team-alpha"},
            {"event_type": "injection", "team_name": "team-alpha"},
            {"event_type": "injection", "team_name": "team-alpha"},
            {"event_type": "injection", "team_name": "team-beta"},
        ]
        counts = count_teammates_per_team(records)
        assert counts == {"team-alpha": 3, "team-beta": 1}

    def test_count_teammates_empty_log(self):
        """Empty records list returns empty dict."""
        assert count_teammates_per_team([]) == {}

    def test_count_teammates_ignores_non_injection(self):
        """Only injection events are counted, not task_completed."""
        records = [
            {"event_type": "injection", "team_name": "team-alpha"},
            {"event_type": "task_completed", "team_name": "team-alpha"},
            {"event_type": "injection", "team_name": "team-alpha"},
            {"event_type": "task_completed", "task_id": "t1"},
        ]
        counts = count_teammates_per_team(records)
        assert counts == {"team-alpha": 2}

    def test_count_teammates_ignores_empty_team_name(self):
        """Records with empty team_name are not counted."""
        records = [
            {"event_type": "injection", "team_name": ""},
            {"event_type": "injection", "team_name": "team-alpha"},
        ]
        counts = count_teammates_per_team(records)
        assert counts == {"team-alpha": 1}


class TestGate1Evaluation:
    """Tests for the Gate 1 evaluation logic."""

    def test_gate1_all_pass(self):
        """Gate 1 passes when all broad strata have sufficient samples and high compliance.

        n=30, k=30 gives CI lower=0.884 > 0.70 (verified by TestClopperPearsonCI).
        n=15 is the minimum sample size for a stratum to pass.
        """
        records = []
        for stratum in GATE_STRATA:
            for i in range(30):
                records.append(
                    {
                        "event_type": "injection",
                        "stratum": stratum,
                        "injection_applied": True,
                    }
                )

        results = evaluate_gate1(records)
        for stratum in GATE_STRATA:
            assert results[stratum]["passed"] is True
            assert results[stratum]["n"] == 30
            assert results[stratum]["data_source"] == "injection"

    def test_gate1_fine_grained_strata_mapped(self):
        """Fine-grained strata are mapped to broad gate strata via STRATUM_MAP."""
        records = []
        # 20 records each for fine-grained strata that map to research
        for fine in ["trivial", "medium", "complex"]:
            for i in range(20):
                records.append(
                    {
                        "event_type": "injection",
                        "stratum": fine,
                        "injection_applied": True,
                    }
                )

        results = evaluate_gate1(records)
        # All 60 records map to "research"
        assert results["research"]["n"] == 60
        assert results["research"]["k"] == 60
        assert results["research"]["passed"] is True

    def test_gate1_insufficient_data(self):
        """Gate 1 fails when strata have < 15 samples."""
        records = [
            {
                "event_type": "injection",
                "stratum": "research",
                "injection_applied": True,
            },
        ]
        results = evaluate_gate1(records)
        assert results["research"]["passed"] is False  # n=1 < 15
        assert results["research"]["n"] == 1

    def test_gate1_prefers_response_scored(self):
        """Gate 1 prefers response_scored events over injection events."""
        records = []
        # Add injection events
        for i in range(20):
            records.append(
                {
                    "event_type": "injection",
                    "stratum": "research",
                    "injection_applied": True,
                }
            )
        # Add response_scored events (fewer, all passing)
        for i in range(16):
            records.append(
                {
                    "event_type": "response_scored",
                    "stratum": "research",
                    "all_criteria_pass": True,
                }
            )

        results = evaluate_gate1(records)
        # Should use response_scored, not injection
        assert results["research"]["n"] == 16
        assert results["research"]["data_source"] == "response_scored"


class TestLoadComplianceLogs:
    """Tests for JSONL log file loading."""

    def test_load_from_directory(self, tmp_path):
        """Load records from JSONL files in a directory."""
        import json

        log_file = tmp_path / "agent-teams-2026-03-20.jsonl"
        records = [
            {"event_type": "injection", "team_name": "t1"},
            {"event_type": "task_completed", "task_id": "t1"},
        ]
        log_file.write_text("\n".join(json.dumps(r) for r in records))

        loaded = load_compliance_logs(tmp_path)
        assert len(loaded) == 2
        assert loaded[0]["event_type"] == "injection"

    def test_load_with_date_filter(self, tmp_path):
        """Date filter selects only matching log files."""
        import json

        (tmp_path / "agent-teams-2026-03-20.jsonl").write_text(
            json.dumps({"event_type": "injection", "date": "20"})
        )
        (tmp_path / "agent-teams-2026-03-21.jsonl").write_text(
            json.dumps({"event_type": "injection", "date": "21"})
        )

        loaded = load_compliance_logs(tmp_path, date_filter="2026-03-20")
        assert len(loaded) == 1
        assert loaded[0]["date"] == "20"

    def test_load_nonexistent_directory(self):
        """Loading from nonexistent directory returns empty list."""
        loaded = load_compliance_logs(Path("/nonexistent/path"))
        assert loaded == []

    def test_scenario_yaml_schema(self):
        """Scenario YAML files have required keys for battery runner."""
        import yaml

        scenarios_dir = (
            Path(__file__).parent.parent
            / "manual"
            / "agent_teams_battery"
            / "scenarios"
        )
        if not scenarios_dir.exists():
            pytest.skip("Scenarios directory not found")

        required_keys = {
            "id",
            "stratum",
            "prompt",
            "expected_behavior",
            "scoring_criteria",
        }

        for yaml_file in scenarios_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                scenarios = yaml.safe_load(f)

            assert isinstance(scenarios, list), f"{yaml_file.name} must be a list"
            for scenario in scenarios:
                missing = required_keys - set(scenario.keys())
                assert not missing, (
                    f"{yaml_file.name} scenario '{scenario.get('id', '?')}' "
                    f"missing keys: {missing}"
                )
