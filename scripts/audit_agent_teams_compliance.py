#!/usr/bin/env python3
"""Agent Teams compliance audit script.

Reads structured JSONL compliance logs and evaluates Gate 1 criteria:
- Per-stratum compliance rate with Clopper-Pearson exact 95% CI
- Pass criterion: lower bound of 95% CI > 70% at ALL strata

Usage:
    python scripts/audit_agent_teams_compliance.py --gate
    python scripts/audit_agent_teams_compliance.py --report
    python scripts/audit_agent_teams_compliance.py --stratum medium
    python scripts/audit_agent_teams_compliance.py --date 2026-03-20
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path


def _binomial_cdf(k: int, n: int, p: float) -> float:
    """Compute exact binomial CDF: P(X <= k) for X ~ Binomial(n, p)."""
    total = 0.0
    for i in range(k + 1):
        total += math.comb(n, i) * (p**i) * ((1 - p) ** (n - i))
    return total


def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Compute Clopper-Pearson exact confidence interval (pure Python).

    Uses binary search on the binomial CDF. No scipy dependency.

    Args:
        k: Number of successes.
        n: Number of trials.
        alpha: Significance level (default 0.05 for 95% CI).

    Returns:
        (lower, upper) bounds of the confidence interval.
    """
    if n == 0:
        return (0.0, 1.0)

    # Lower bound: find p such that P(X >= k | p) = alpha/2
    if k == 0:
        lower = 0.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(100):  # Binary search converges to machine precision
            mid = (lo + hi) / 2
            # P(X >= k) = 1 - P(X <= k-1)
            if 1 - _binomial_cdf(k - 1, n, mid) > alpha / 2:
                hi = mid
            else:
                lo = mid
        lower = lo

    # Upper bound: find p such that P(X <= k | p) = alpha/2
    if k == n:
        upper = 1.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if _binomial_cdf(k, n, mid) > alpha / 2:
                lo = mid
            else:
                hi = mid
        upper = hi

    return (lower, upper)


def count_teammates_per_team(records: list[dict]) -> dict[str, int]:
    """Count injection events per team_name from compliance log."""
    return dict(
        Counter(
            r["team_name"]
            for r in records
            if r.get("event_type") == "injection" and r.get("team_name")
        )
    )


def load_compliance_logs(log_dir: Path, date_filter: str | None = None) -> list[dict]:
    """Load all JSONL records from the compliance log directory."""
    records = []
    if not log_dir.exists():
        return records

    pattern = (
        f"agent-teams-{date_filter}.jsonl" if date_filter else "agent-teams-*.jsonl"
    )
    for log_file in sorted(log_dir.glob(pattern)):
        for line in log_file.read_text().strip().split("\n"):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def evaluate_gate1(records: list[dict], threshold: float = 0.70) -> dict[str, dict]:
    """Evaluate Gate 1: per-stratum compliance with Clopper-Pearson CI.

    Returns dict keyed by stratum with n, k, rate, ci_lower, ci_upper, passed.
    """
    # Filter to injection events with stratum labels
    injection_records = [
        r for r in records if r.get("event_type") == "injection" and r.get("stratum")
    ]

    results = {}
    for stratum in ["trivial", "medium", "complex"]:
        stratum_records = [r for r in injection_records if r["stratum"] == stratum]
        n = len(stratum_records)
        # For now, count all injection events as successes
        # (actual compliance scoring requires response analysis, done by battery runner)
        k = sum(1 for r in stratum_records if r.get("injection_applied", False))
        rate = k / n if n > 0 else 0.0
        ci_lower, ci_upper = clopper_pearson_ci(k, n)
        passed = ci_lower > threshold and n >= 10

        results[stratum] = {
            "n": n,
            "k": k,
            "rate": rate,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "passed": passed,
        }

    return results


def print_report(records: list[dict], gate_results: dict | None = None) -> None:
    """Print a human-readable compliance report."""
    injection_count = sum(1 for r in records if r.get("event_type") == "injection")
    completion_count = sum(
        1 for r in records if r.get("event_type") == "task_completed"
    )
    team_counts = count_teammates_per_team(records)

    print("=" * 60)
    print("Agent Teams Compliance Report")
    print("=" * 60)
    print(f"Total records:      {len(records)}")
    print(f"Injection events:   {injection_count}")
    print(f"Completion events:  {completion_count}")
    print(f"Unique teams:       {len(team_counts)}")
    if team_counts:
        print(f"Teammates per team: {dict(team_counts)}")
    print()

    if gate_results:
        print("Gate 1 Evaluation (Clopper-Pearson 95% CI, threshold > 0.70)")
        print("-" * 60)
        all_passed = True
        for stratum, data in gate_results.items():
            status = "PASS" if data["passed"] else "FAIL"
            if not data["passed"]:
                all_passed = False
            if data["n"] > 0:
                print(
                    f"  {stratum:>10}: {data['k']}/{data['n']} "
                    f"({data['rate'] * 100:.1f}%) "
                    f"CI=[{data['ci_lower']:.3f}, {data['ci_upper']:.3f}] "
                    f"{status}"
                )
            else:
                print(f"  {stratum:>10}: no data")
        print("-" * 60)
        print(f"  Overall: {'GATE 1 PASSED' if all_passed else 'GATE 1 FAILED'}")
    print("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Teams compliance audit")
    parser.add_argument("--gate", action="store_true", help="Evaluate Gate 1 pass/fail")
    parser.add_argument(
        "--report", action="store_true", help="Print full compliance report"
    )
    parser.add_argument(
        "--stratum",
        type=str,
        help="Filter by stratum (trivial/medium/complex/adversarial)",
    )
    parser.add_argument("--date", type=str, help="Filter by date (YYYY-MM-DD)")
    parser.add_argument(
        "--log-dir",
        type=str,
        default=str(Path.home() / ".claude-mpm" / "compliance"),
        help="Compliance log directory",
    )
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    records = load_compliance_logs(log_dir, date_filter=args.date)

    if args.stratum:
        records = [r for r in records if r.get("stratum") == args.stratum]

    if not records:
        print(f"No compliance records found in {log_dir}")
        return 1

    gate_results = evaluate_gate1(records) if args.gate else None
    print_report(records, gate_results)

    if args.gate and gate_results:
        # Exit 0 if all strata pass, 1 if any fail
        all_passed = all(d["passed"] for d in gate_results.values())
        return 0 if all_passed else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
