"""Pytest plugin that records eval test results to JSON.

Hooks into pytest_runtest_makereport and pytest_sessionfinish to capture
per-test outcomes and write a session summary to tests/eval/results/.

Activation:
    --eval-record flag  OR  EVAL_RECORD_RESULTS=1 env var

Result files are written to tests/eval/results/{run_id}.json with a
timestamp-based run_id (e.g., 20260309-212500.json).
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Tier detection helpers
# ---------------------------------------------------------------------------

_TIER_MAP: dict[str, str] = {
    "structural": "tier1",
    "tier2": "tier2",
    "tier3": "tier3",
}


def _tier_from_nodeid(nodeid: str) -> str:
    """Extract tier label from a test node id path component.

    Examples:
        tests/eval/structural/test_foo.py::test_bar  -> "tier1"
        tests/eval/tier2/test_delegation_intent.py   -> "tier2"
        tests/eval/tier3/test_behavior.py            -> "tier3"
    """
    for path_segment, tier_label in _TIER_MAP.items():
        if f"/{path_segment}/" in nodeid or f"\\{path_segment}\\" in nodeid:
            return tier_label
    return "unknown"


_SCENARIO_RE = re.compile(r"\[([A-Z]+-\d+[^\]]*)\]")


def _scenario_id_from_nodeid(nodeid: str) -> str | None:
    """Extract scenario id from parametrize brackets like [DEL-01] or [BHV-03]."""
    match = _SCENARIO_RE.search(nodeid)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _git_branch() -> str:
    """Return current git branch name, or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return "unknown"


def _git_commit() -> str:
    """Return short git commit hash, or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return "unknown"


# ---------------------------------------------------------------------------
# Per-test result container
# ---------------------------------------------------------------------------


@dataclass
class TestRecord:
    """Captured result for a single test."""

    node_id: str
    tier: str
    outcome: str = "unknown"
    duration_seconds: float = 0.0
    scenario_id: str | None = None
    agent_routed: str | None = None
    failure_message: str | None = None


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------


class EvalResultRecorder:
    """Pytest plugin that records eval run results to JSON files.

    Registered by the top-level tests/eval/conftest.py when
    ``--eval-record`` or ``EVAL_RECORD_RESULTS=1`` is active.
    """

    def __init__(self, config: Any) -> None:
        self._config = config
        self._records: dict[str, TestRecord] = {}
        self._session_start: float = time.monotonic()
        self._results_dir = Path(__file__).resolve().parent.parent / "results"
        self._results_dir.mkdir(parents=True, exist_ok=True)

    # -- pytest hooks -------------------------------------------------------

    def pytest_runtest_makereport(self, item: Any, call: Any) -> None:  # noqa: ANN401
        """Capture per-test outcome after the *call* phase."""
        if call.when != "call":
            return

        node_id = item.nodeid
        record = self._records.get(node_id)
        if record is None:
            record = TestRecord(
                node_id=node_id,
                tier=_tier_from_nodeid(node_id),
                scenario_id=_scenario_id_from_nodeid(node_id),
            )
            self._records[node_id] = record

        # Outcome from the call phase
        if call.excinfo is None:
            record.outcome = "passed"
        else:
            # Distinguish skip from failure/error
            exctype = call.excinfo.typename
            if exctype in ("Skipped", "skip"):
                record.outcome = "skipped"
            else:
                record.outcome = "failed"
                record.failure_message = str(call.excinfo.value)[:500]

        record.duration_seconds = round(call.duration, 3)

        # Try to extract agent_routed from the test item's funcargs
        # (available when adapter results are captured by fixtures)
        self._extract_agent_routed(item, record)

    def pytest_sessionfinish(self, session: Any, exitstatus: int) -> None:
        """Write the complete results JSON at end of session."""
        now = datetime.now(timezone.utc)
        run_id = now.strftime("%Y%m%d-%H%M%S")
        duration_seconds = round(time.monotonic() - self._session_start, 2)

        # Tally outcomes
        records = list(self._records.values())
        total = len(records)
        counts: dict[str, int] = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
        for rec in records:
            key = rec.outcome if rec.outcome in counts else "error"
            counts[key] += 1

        pass_rate = round(counts["passed"] / max(total, 1), 3)

        # Determine which tiers were exercised
        tiers_run = sorted({rec.tier for rec in records if rec.tier != "unknown"})

        # Attempt to gather cost from adapter stats (best-effort)
        cost_info = self._gather_cost_info()

        result_payload: dict[str, Any] = {
            "run_id": run_id,
            "timestamp": now.isoformat(),
            "git_branch": _git_branch(),
            "git_commit": _git_commit(),
            "tiers_run": tiers_run,
            "summary": {
                "total": total,
                "passed": counts["passed"],
                "failed": counts["failed"],
                "skipped": counts["skipped"],
                "error": counts["error"],
                "pass_rate": pass_rate,
                "duration_seconds": duration_seconds,
            },
            "cost": cost_info,
            "tests": [
                {
                    "node_id": rec.node_id,
                    "tier": rec.tier,
                    "outcome": rec.outcome,
                    "duration_seconds": rec.duration_seconds,
                    "scenario_id": rec.scenario_id,
                    "agent_routed": rec.agent_routed,
                    "failure_message": rec.failure_message,
                }
                for rec in records
            ],
        }

        output_path = self._results_dir / f"{run_id}.json"
        try:
            output_path.write_text(
                json.dumps(result_payload, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            # Swallow write errors so we never break the test session
            import warnings

            warnings.warn(
                f"EvalResultRecorder: failed to write {output_path}: {exc}",
                stacklevel=1,
            )

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _extract_agent_routed(item: Any, record: TestRecord) -> None:
        """Best-effort extraction of agent_routed from test funcargs."""
        try:
            funcargs = getattr(item, "funcargs", {})
            # For parametrised scenarios with 'scenario' fixture
            scenario = funcargs.get("scenario")
            if isinstance(scenario, dict):
                record.agent_routed = scenario.get("expected_agent")
        except Exception:  # noqa: BLE001
            pass

    def _gather_cost_info(self) -> dict[str, Any]:
        """Try to pull cost stats from a module-scoped adapter if accessible."""
        cost: dict[str, Any] = {
            "total_usd": 0.0,
            "invocation_count": 0,
        }
        try:
            # Walk registered plugins looking for StructuredOutputAdapter instances
            plugin_manager = self._config.pluginmanager
            for plugin in plugin_manager.get_plugins():
                stats = getattr(plugin, "stats", None)
                if callable(stats):
                    try:
                        s = stats()
                        if isinstance(s, dict) and "total_cost_usd" in s:
                            cost["total_usd"] += s.get("total_cost_usd", 0.0)
                            cost["invocation_count"] += s.get("invocation_count", 0)
                    except Exception:  # noqa: BLE001
                        pass
        except Exception:  # noqa: BLE001
            pass
        cost["total_usd"] = round(cost["total_usd"], 4)
        return cost
