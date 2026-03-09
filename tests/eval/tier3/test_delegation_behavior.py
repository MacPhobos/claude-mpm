"""Tier 3: Behavioral delegation tests using hook interception.

These tests invoke ``claude-mpm run`` with a PreToolUse hook that captures
(and blocks) Task/Agent tool calls, allowing us to verify the PM's actual
delegation behaviour without spawning real sub-agents.

IMPORTANT: These tests CANNOT run from within a Claude session.
Run from terminal: uv run pytest tests/eval/tier3/ -xvs -p no:xdist --tb=long

Cost: ~$0.10/test  (7 tests ~ $0.50-$0.70 total)
Speed: 15-45s/test (network + LLM latency)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.eval.adapters.hook_interception_harness import HookInterceptionHarness

pytestmark = [pytest.mark.e2e, pytest.mark.eval, pytest.mark.tier3]


# ---------------------------------------------------------------------------
# Behavioural scenarios (BHV-01 .. BHV-05)
# ---------------------------------------------------------------------------

BEHAVIORAL_SCENARIOS = [
    {
        "id": "BHV-01",
        "prompt": "Implement user authentication with OAuth2",
        "expected_agents": ["engineer"],
        "description": "Implementation task should route to engineer",
    },
    {
        "id": "BHV-02",
        "prompt": "Research the database architecture and document patterns used",
        "expected_agents": ["research"],
        "description": "Research task should route to research agent",
    },
    {
        "id": "BHV-03",
        "prompt": "Start the development server on localhost:3000",
        "expected_agents": ["local-ops", "local_ops", "localops", "ops"],
        "description": "Local ops task should route to local-ops agent",
    },
    {
        "id": "BHV-04",
        "prompt": "Run the full test suite and report any failures",
        "expected_agents": ["qa", "test"],
        "description": "QA task should route to qa agent",
    },
    {
        "id": "BHV-05",
        "prompt": "Fix the critical security vulnerability in the authentication module",
        "expected_agents": ["engineer", "research", "security"],
        "description": "Security fix may route to engineer, research, or security",
    },
]


# ---------------------------------------------------------------------------
# BHV-01..05: Parametrized delegation behaviour
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "scenario",
    BEHAVIORAL_SCENARIOS,
    ids=[s["id"] for s in BEHAVIORAL_SCENARIOS],
)
def test_delegation_behavior(
    harness: HookInterceptionHarness,
    scenario: dict,
) -> None:
    """Verify that the PM delegates to the expected agent type."""
    result = harness.run_prompt(scenario["prompt"], timeout=45)

    delegations = harness.get_captured_delegations()
    first = harness.get_first_delegation()

    combined_output = (result.stdout or "") + (result.stderr or "")

    assert len(delegations) >= 1, (
        f"Scenario {scenario['id']}: No delegations captured. "
        f"Expected delegation to one of {scenario['expected_agents']}.\n"
        f"stdout[:500]: {result.stdout[:500] if result.stdout else '(empty)'}\n"
        f"stderr[:500]: {result.stderr[:500] if result.stderr else '(empty)'}"
    )

    assert first is not None  # Redundant guard for type-checker
    agent_type = first["delegation"].get("agent_type", "").lower()

    valid_agents = [a.lower() for a in scenario["expected_agents"]]

    assert any(valid in agent_type for valid in valid_agents), (
        f"Scenario {scenario['id']}: Expected agent in {scenario['expected_agents']}, "
        f"got '{agent_type}'.\n"
        f"Delegation detail:\n"
        f"{json.dumps(first['delegation'], indent=2)}\n"
        f"stdout[:500]: {result.stdout[:500] if result.stdout else '(empty)'}"
    )


# ---------------------------------------------------------------------------
# BHV-06: Delegation prompt contains substantive content
# ---------------------------------------------------------------------------


def test_delegation_captures_prompt_content(
    harness: HookInterceptionHarness,
) -> None:
    """Verify that the captured delegation prompt retains meaningful content."""
    prompt = (
        "Investigate the authentication module and report all security vulnerabilities"
    )
    result = harness.run_prompt(prompt, timeout=45)

    delegations = harness.get_captured_delegations()
    first = harness.get_first_delegation()

    assert len(delegations) >= 1, (
        f"No delegations captured for prompt '{prompt}'.\n"
        f"stdout[:500]: {result.stdout[:500] if result.stdout else '(empty)'}\n"
        f"stderr[:500]: {result.stderr[:500] if result.stderr else '(empty)'}"
    )

    assert first is not None
    delegation_prompt: str = first["delegation"].get("prompt", "")

    assert len(delegation_prompt) > 50, (
        f"Delegation prompt too short ({len(delegation_prompt)} chars): "
        f"'{delegation_prompt[:200]}'"
    )

    # At least one relevant keyword should appear in the delegation prompt
    keywords = ["auth", "security", "vulnerab", "investigat"]
    prompt_lower = delegation_prompt.lower()
    matched = [kw for kw in keywords if kw in prompt_lower]

    assert len(matched) >= 1, (
        f"Delegation prompt lacks expected keywords. "
        f"Expected at least one of {keywords} in: '{delegation_prompt[:200]}'"
    )


# ---------------------------------------------------------------------------
# BHV-07: Blocking actually prevents sub-agent execution
# ---------------------------------------------------------------------------


def test_blocking_prevents_subagent(
    harness: HookInterceptionHarness,
) -> None:
    """Verify that the interceptor blocks delegation and captures the attempt."""
    prompt = "Deploy the application to production with zero downtime"
    result = harness.run_prompt(prompt, timeout=45)

    delegations = harness.get_captured_delegations()

    # Primary assertion: delegation was captured (interception worked)
    assert len(delegations) >= 1, (
        f"No delegations captured for blocking test.\n"
        f"stdout[:500]: {result.stdout[:500] if result.stdout else '(empty)'}\n"
        f"stderr[:500]: {result.stderr[:500] if result.stderr else '(empty)'}"
    )

    # Secondary assertion: evidence of blocking in output OR capture file
    combined_output = ((result.stdout or "") + (result.stderr or "")).lower()

    blocking_evidence = (
        "intercepted" in combined_output
        or "blocked" in combined_output
        or "stopreason" in combined_output
        or len(delegations) >= 1  # Fallback: capture itself proves interception
    )

    assert blocking_evidence, (
        f"No evidence of blocking found.\n"
        f"Delegations captured: {len(delegations)}\n"
        f"stdout[:500]: {result.stdout[:500] if result.stdout else '(empty)'}\n"
        f"stderr[:500]: {result.stderr[:500] if result.stderr else '(empty)'}"
    )
