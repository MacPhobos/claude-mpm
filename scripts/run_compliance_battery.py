#!/usr/bin/env python3
"""Minimal compliance battery runner.

Calls Haiku API with TEAMMATE_PROTOCOL + scenario prompts, scores responses,
writes compliance JSONL records for gate evaluation.

Usage:
    python scripts/run_compliance_battery.py                    # Run all scenarios
    python scripts/run_compliance_battery.py engineer-parallel  # Filter by stratum
    python scripts/run_compliance_battery.py --dry-run          # Show prompts, don't call API

Requires: ANTHROPIC_API_KEY environment variable.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import yaml

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(
    0, str(Path(__file__).parent.parent / "tests" / "manual" / "agent_teams_battery")
)

from scoring.compliance_scorer import score_response

from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
    _ROLE_ADDENDA,
    TEAMMATE_PROTOCOL_BASE,
)

# Directories
SCENARIOS_DIR = (
    Path(__file__).parent.parent
    / "tests"
    / "manual"
    / "agent_teams_battery"
    / "scenarios"
)
LOG_DIR = Path.home() / ".claude-mpm" / "compliance"

# Phase 2: Map fine-grained strata to 3 broad gate strata
STRATUM_MAP = {
    "trivial": "research",
    "medium": "research",
    "complex": "research",
    "adversarial": "research",
    "research-then-eng": "research",
    "engineer-parallel": "engineer",
    "engineer-antipattern": "engineer",
    "engineer-merge": "engineer",
    "engineer-recovery": "engineer",
    "eng-then-qa": "engineer",
    "qa-pipeline": "qa",
    "qa-antipattern": "qa",
    "qa-protocol": "qa",
    "full-pipeline": "qa",
    "pipeline-antipattern": "qa",
}


def load_scenarios() -> list[dict]:
    """Load all scenario YAML files."""
    scenarios = []
    for f in sorted(SCENARIOS_DIR.glob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        if data:
            scenarios.extend(data)
    return scenarios


def build_prompt(scenario: dict, role: str) -> str:
    """Assemble TEAMMATE_PROTOCOL + scenario prompt. Returns full_prompt."""
    protocol = TEAMMATE_PROTOCOL_BASE
    addendum = _ROLE_ADDENDA.get(role.lower(), "")
    if addendum:
        protocol += "\n\n" + addendum
    return protocol + "\n\n---\n\n" + scenario["prompt"]


# Map broad strata to the role we are testing
STRATUM_ROLE = {"research": "research", "engineer": "engineer", "qa": "qa"}


def call_haiku(prompt: str) -> str:
    """Call Haiku API and return response text."""
    try:
        from anthropic import Anthropic
    except ImportError:
        print("ERROR: anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    client = Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main() -> int:
    # Parse simple args
    dry_run = "--dry-run" in sys.argv
    strata_filter = [a for a in sys.argv[1:] if not a.startswith("--")]

    scenarios = load_scenarios()
    if strata_filter:
        scenarios = [s for s in scenarios if s["stratum"] in strata_filter]

    if not scenarios:
        print(f"No scenarios found (filter: {strata_filter or 'none'})")
        return 1

    if not dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. Export it or use --dry-run.")
        return 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"agent-teams-battery-{time.strftime('%Y-%m-%d')}.jsonl"

    total = len(scenarios)
    passed = 0
    failed = 0

    print(f"Running {total} scenarios {'(DRY RUN)' if dry_run else ''}")
    print(f"Log file: {log_file}")
    print("=" * 60)

    for i, scenario in enumerate(scenarios, 1):
        broad_stratum = STRATUM_MAP.get(scenario["stratum"], "research")
        role = STRATUM_ROLE.get(broad_stratum, "research")
        prompt = build_prompt(scenario, role)

        print(
            f"[{i}/{total}] {scenario['id']} (stratum={broad_stratum}, role={role})",
            end="",
        )

        if dry_run:
            print(f" ... SKIPPED (dry run, prompt={len(prompt)} chars)")
            continue

        try:
            response_text = call_haiku(prompt)
        except Exception as e:
            print(f" ... ERROR: {e}")
            failed += 1
            continue

        files_modified = scenario.get("scoring_criteria", {}).get(
            "manifest_required", False
        )
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

        if all_pass:
            passed += 1
            print(" -> PASS")
        else:
            failed += 1
            failed_criteria = [k for k, v in scores.items() if not v]
            print(f" -> FAIL ({failed_criteria})")

        time.sleep(0.3)  # Rate limiting

    print("=" * 60)
    print(f"Done. {passed} passed, {failed} failed out of {total}")
    print(f"Log: {log_file}")

    if not dry_run:
        print("\nRun gate evaluation:")
        print(
            f"  python scripts/audit_agent_teams_compliance.py --gate --log-dir {LOG_DIR}"
        )

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
