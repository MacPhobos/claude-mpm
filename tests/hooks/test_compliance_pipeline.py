#!/usr/bin/env python3
"""End-to-end pipeline smoke tests for Agent Teams compliance.

Validates data flows correctly between: _compliance_log() -> JSONL ->
load_compliance_logs() -> evaluate_gate1(). Fast, deterministic.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from audit_agent_teams_compliance import (
    evaluate_gate1,
    load_compliance_logs,
)


class TestCompliancePipeline:
    """Smoke tests for the compliance measurement pipeline."""

    def test_compliance_log_schema_matches_audit_loader(self, tmp_path):
        """Records written by _compliance_log() can be loaded by audit script."""
        log_dir = tmp_path / "compliance"

        with patch(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            log_dir,
        ):
            from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

            _compliance_log(
                {
                    "event_type": "injection",
                    "session_id": "sess-1",
                    "team_name": "research-auth",
                    "subagent_type": "research",
                    "teammate_name": "auth-researcher",
                    "injection_applied": True,
                    "stratum": "trivial",
                }
            )

        # Load via audit script
        records = load_compliance_logs(log_dir)
        assert len(records) == 1

        r = records[0]
        assert r["event_type"] == "injection"
        assert r["session_id"] == "sess-1"
        assert r["team_name"] == "research-auth"
        assert r["injection_applied"] is True
        assert r["stratum"] == "trivial"
        assert "timestamp" in r  # Added by _compliance_log

    def test_injection_to_gate1_pipeline(self, tmp_path):
        """30 injection records per stratum -> Gate 1 evaluation produces correct pass/fail."""
        log_dir = tmp_path / "compliance"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "agent-teams-2026-03-20.jsonl"

        # Write 30 successful injections per stratum
        records = []
        for stratum in ["trivial", "medium", "complex"]:
            for i in range(30):
                records.append(
                    {
                        "event_type": "injection",
                        "stratum": stratum,
                        "injection_applied": True,
                        "session_id": f"sess-{stratum}-{i}",
                        "team_name": f"team-{stratum}",
                        "timestamp": "2026-03-20T12:00:00+00:00",
                    }
                )

        log_file.write_text("\n".join(json.dumps(r) for r in records))

        # Load and evaluate
        loaded = load_compliance_logs(log_dir)
        assert len(loaded) == 90

        results = evaluate_gate1(loaded)
        for stratum in ["trivial", "medium", "complex"]:
            assert results[stratum]["n"] == 30
            assert results[stratum]["k"] == 30
            assert results[stratum]["passed"] is True
            assert results[stratum]["ci_lower"] > 0.88  # Perfect n=30 lower bound

    def test_scorer_output_keys_are_defined(self):
        """Scorer output dict keys are documented and stable."""
        # Import scorer
        sys.path.insert(
            0,
            str(Path(__file__).parent.parent / "manual" / "agent_teams_battery"),
        )
        from scoring.compliance_scorer import score_response

        result = score_response("Test response")
        expected_keys = {
            "evidence_present",
            "forbidden_phrases_absent",
            "manifest_present",
            "qa_scope_declared",
            "no_peer_delegation",
        }
        assert set(result.keys()) == expected_keys
        assert all(isinstance(v, bool) for v in result.values())
