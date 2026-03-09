"""Degradation detector for eval test results.

Compares the latest (or a given) run against historical results stored in
tests/eval/results/ and flags regressions, cost spikes, and pass-rate drops.

Usage as library:
    from tests.eval.tracking.degradation_detector import DegradationDetector
    detector = DegradationDetector(results_dir)
    report = detector.detect()
    if report.is_degraded:
        print(report.summary)

Usage as CLI:
    uv run python -m tests.eval.tracking.degradation_detector
    uv run python -m tests.eval.tracking.degradation_detector --results-dir tests/eval/results/
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TestRegression:
    """A test that previously passed but now fails."""

    test_id: str
    historical_pass_rate: float  # e.g. 0.95 = passed 95% of recent runs
    current_outcome: str  # "failed"
    first_seen: str  # run_id when test first appeared


@dataclass
class CostAlert:
    """A cost metric that spiked above threshold."""

    metric: str  # "total_usd" or "per_test_usd"
    historical_avg: float
    current_value: float
    increase_pct: float  # e.g. 0.75 = 75% increase


@dataclass
class DegradationReport:
    """Summary of degradation detection results."""

    is_degraded: bool
    test_regressions: list[TestRegression] = field(default_factory=list)
    cost_alerts: list[CostAlert] = field(default_factory=list)
    pass_rate_delta: float = 0.0  # negative means degradation
    summary: str = ""


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

# Thresholds (configurable via constructor)
_DEFAULT_LOOKBACK = 5
_REGRESSION_PASS_THRESHOLD = 0.80  # test passed >= 80% of recent runs
_COST_SPIKE_THRESHOLD = 0.50  # cost increased > 50%
_PASS_RATE_DROP_THRESHOLD = 0.05  # pass rate dropped > 5%


class DegradationDetector:
    """Compare the latest eval run against recent history.

    Parameters:
        results_dir: Path to the directory containing result JSON files.
        lookback: Number of recent runs to compare against (default 5).
    """

    def __init__(
        self,
        results_dir: Path,
        lookback: int = _DEFAULT_LOOKBACK,
    ) -> None:
        self.results_dir = Path(results_dir)
        self.lookback = lookback

    # -- public API ---------------------------------------------------------

    def load_history(self) -> list[dict[str, Any]]:
        """Load all result files sorted by timestamp (oldest first).

        Returns:
            List of parsed result dicts, sorted chronologically.
        """
        if not self.results_dir.is_dir():
            return []

        results: list[dict[str, Any]] = []
        for path in sorted(self.results_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "run_id" in data:
                    results.append(data)
            except (json.JSONDecodeError, OSError):
                # Skip malformed / unreadable files silently
                continue

        # Sort by timestamp (ISO 8601) then by run_id as fallback
        results.sort(key=lambda r: r.get("timestamp", r.get("run_id", "")))
        return results

    def detect(self, current: dict[str, Any] | None = None) -> DegradationReport:
        """Compare *current* run (or latest from history) against recent runs.

        Parameters:
            current: A result dict to treat as the current run.  When
                ``None`` the most recent file in results_dir is used.

        Returns:
            DegradationReport with regression details.
        """
        history = self.load_history()

        if current is not None:
            # Exclude the current run from history if it appears there
            current_id = current.get("run_id")
            history = [h for h in history if h.get("run_id") != current_id]
        elif history:
            current = history.pop()
        else:
            return DegradationReport(
                is_degraded=False,
                summary="No historical results found. Nothing to compare.",
            )

        if current is None:
            return DegradationReport(
                is_degraded=False,
                summary="No current run provided and no results in history.",
            )

        # Use only the most recent N runs for comparison
        recent = history[-self.lookback :] if history else []
        if not recent:
            return DegradationReport(
                is_degraded=False,
                summary="Only one run available. No baseline for comparison.",
            )

        # Detect regressions
        test_regressions = self._detect_test_regressions(current, recent)
        cost_alerts = self._detect_cost_spikes(current, recent)
        pass_rate_delta = self._detect_pass_rate_drop(current, recent)

        is_degraded = (
            bool(test_regressions)
            or bool(cost_alerts)
            or (pass_rate_delta < -_PASS_RATE_DROP_THRESHOLD)
        )

        summary = self._build_summary(
            current, recent, test_regressions, cost_alerts, pass_rate_delta
        )

        return DegradationReport(
            is_degraded=is_degraded,
            test_regressions=test_regressions,
            cost_alerts=cost_alerts,
            pass_rate_delta=pass_rate_delta,
            summary=summary,
        )

    # -- detection helpers --------------------------------------------------

    def _detect_test_regressions(
        self,
        current: dict[str, Any],
        recent: list[dict[str, Any]],
    ) -> list[TestRegression]:
        """Find tests that passed historically but fail in the current run."""
        # Build per-test pass rate from recent history
        test_history: dict[str, list[str]] = {}  # test_id -> list of outcomes
        test_first_seen: dict[str, str] = {}  # test_id -> earliest run_id

        for run in recent:
            run_id = run.get("run_id", "unknown")
            for test in run.get("tests", []):
                tid = test.get("node_id", "")
                if not tid:
                    continue
                test_history.setdefault(tid, []).append(test.get("outcome", "unknown"))
                if tid not in test_first_seen:
                    test_first_seen[tid] = run_id

        # Check current run tests against history
        regressions: list[TestRegression] = []
        for test in current.get("tests", []):
            tid = test.get("node_id", "")
            outcome = test.get("outcome", "unknown")
            if outcome != "failed":
                continue

            hist = test_history.get(tid, [])
            if not hist:
                # New test that failed on first appearance is a "new failure"
                regressions.append(
                    TestRegression(
                        test_id=tid,
                        historical_pass_rate=1.0,  # never failed before
                        current_outcome=outcome,
                        first_seen=current.get("run_id", "unknown"),
                    )
                )
                continue

            pass_count = sum(1 for o in hist if o == "passed")
            pass_rate = pass_count / len(hist)

            if pass_rate >= _REGRESSION_PASS_THRESHOLD:
                regressions.append(
                    TestRegression(
                        test_id=tid,
                        historical_pass_rate=round(pass_rate, 3),
                        current_outcome=outcome,
                        first_seen=test_first_seen.get(tid, "unknown"),
                    )
                )

        return regressions

    def _detect_cost_spikes(
        self,
        current: dict[str, Any],
        recent: list[dict[str, Any]],
    ) -> list[CostAlert]:
        """Detect cost increases above threshold."""
        alerts: list[CostAlert] = []

        current_cost = self._extract_cost(current)
        if current_cost is None or current_cost == 0.0:
            return alerts

        historical_costs = [
            c for r in recent if (c := self._extract_cost(r)) is not None and c > 0
        ]
        if not historical_costs:
            return alerts

        avg_cost = sum(historical_costs) / len(historical_costs)
        if avg_cost <= 0:
            return alerts

        increase_pct = (current_cost - avg_cost) / avg_cost
        if increase_pct > _COST_SPIKE_THRESHOLD:
            alerts.append(
                CostAlert(
                    metric="total_usd",
                    historical_avg=round(avg_cost, 4),
                    current_value=round(current_cost, 4),
                    increase_pct=round(increase_pct, 3),
                )
            )

        return alerts

    def _detect_pass_rate_drop(
        self,
        current: dict[str, Any],
        recent: list[dict[str, Any]],
    ) -> float:
        """Return pass rate delta (negative = regression)."""
        current_rate = current.get("summary", {}).get("pass_rate")
        if current_rate is None:
            return 0.0

        historical_rates = [
            r.get("summary", {}).get("pass_rate")
            for r in recent
            if r.get("summary", {}).get("pass_rate") is not None
        ]
        if not historical_rates:
            return 0.0

        avg_rate = sum(historical_rates) / len(historical_rates)
        return round(current_rate - avg_rate, 4)

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _extract_cost(run: dict[str, Any]) -> float | None:
        """Extract total_usd cost from a result dict."""
        cost = run.get("cost", {})
        if isinstance(cost, dict):
            val = cost.get("total_usd")
            if isinstance(val, (int, float)):
                return float(val)
        return None

    @staticmethod
    def _build_summary(
        current: dict[str, Any],
        recent: list[dict[str, Any]],
        regressions: list[TestRegression],
        cost_alerts: list[CostAlert],
        pass_rate_delta: float,
    ) -> str:
        """Build a human-readable summary string."""
        lines: list[str] = []
        run_id = current.get("run_id", "unknown")
        lines.append(f"Degradation Report for run {run_id}")
        lines.append(f"  Compared against {len(recent)} recent run(s)")
        lines.append("")

        summary = current.get("summary", {})
        lines.append(
            f"  Current: {summary.get('passed', '?')}/{summary.get('total', '?')} passed "
            f"(rate={summary.get('pass_rate', '?')})"
        )
        lines.append(f"  Pass rate delta: {pass_rate_delta:+.3f}")
        lines.append("")

        if regressions:
            lines.append(f"  TEST REGRESSIONS ({len(regressions)}):")
            for reg in regressions:
                lines.append(
                    f"    - {reg.test_id}"
                    f"  (historical pass rate: {reg.historical_pass_rate:.0%},"
                    f" current: {reg.current_outcome})"
                )
            lines.append("")

        if cost_alerts:
            lines.append(f"  COST ALERTS ({len(cost_alerts)}):")
            for alert in cost_alerts:
                lines.append(
                    f"    - {alert.metric}: ${alert.current_value:.4f}"
                    f" (avg: ${alert.historical_avg:.4f},"
                    f" +{alert.increase_pct:.0%})"
                )
            lines.append("")

        if (
            not regressions
            and not cost_alerts
            and pass_rate_delta >= -_PASS_RATE_DROP_THRESHOLD
        ):
            lines.append("  No degradation detected.")
        else:
            lines.append("  DEGRADATION DETECTED - review regressions above.")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for degradation detection.

    Returns:
        0 if clean, 1 if degradation detected.
    """
    parser = argparse.ArgumentParser(
        description="Check for eval test degradation against historical results.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "results",
        help="Path to the results directory (default: tests/eval/results/)",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=_DEFAULT_LOOKBACK,
        help=f"Number of recent runs to compare against (default: {_DEFAULT_LOOKBACK})",
    )

    args = parser.parse_args(argv)

    detector = DegradationDetector(
        results_dir=args.results_dir,
        lookback=args.lookback,
    )

    report = detector.detect()
    print(report.summary)  # noqa: T201

    return 1 if report.is_degraded else 0


if __name__ == "__main__":
    sys.exit(main())
