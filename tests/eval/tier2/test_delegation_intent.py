"""Tier 2: Delegation intent tests using structured output.

These tests verify the PM's delegation INTENT by sending prompts through
claude -p with --json-schema and --tools "" (no tool execution).

IMPORTANT: These tests CANNOT run from within a Claude session.
Run from terminal: uv run pytest tests/eval/tier2/ -xvs -p no:xdist

Cost: ~$0.07/test (with prompt caching after first call)
Speed: 3-8s/test
"""

import json
from pathlib import Path

import pytest

from tests.eval.adapters.structured_output_adapter import (
    DelegationIntentResult,
    DelegationTestError,
    InfrastructureError,
    StructuredOutputAdapter,
)

pytestmark = [
    pytest.mark.eval,
    pytest.mark.tier2,
]


# --- Load scenarios from JSON ------------------------------------------------

SCENARIOS_PATH = (
    Path(__file__).parent.parent / "scenarios" / "delegation_scenarios.json"
)


def _load_scenarios():
    with open(SCENARIOS_PATH) as f:
        data = json.load(f)
    return data["scenarios"]


_SCENARIOS = _load_scenarios()

DELEGATION_SCENARIOS = _SCENARIOS["delegation"]
NO_DELEGATION_SCENARIOS = _SCENARIOS["no_delegation"]
CONTEXT_QUALITY_SCENARIOS = _SCENARIOS["context_quality"]
CIRCUIT_BREAKER_SCENARIOS = _SCENARIOS["circuit_breaker"]


# --- Fixtures -----------------------------------------------------------------


@pytest.fixture(scope="module")
def adapter():
    """Module-scoped adapter for prompt caching benefit."""
    return StructuredOutputAdapter(max_budget_usd=0.50, timeout=45)


# --- Helpers ------------------------------------------------------------------


def _assert_delegates_to(
    result: DelegationIntentResult,
    expected: str,
    alternatives: list[str],
    scenario_id: str,
    prompt: str,
):
    """Assert PM delegates to expected agent (case-insensitive, flexible matching)."""
    assert result.would_delegate, (
        f"Scenario {scenario_id}: PM chose NOT to delegate for "
        f"'{prompt[:80]}...'\n"
        f"Reasoning: {result.reasoning}"
    )

    target = result.target_agent  # already lowered + hyphenated
    valid_agents = [expected.lower()] + [a.lower() for a in alternatives]

    assert any(valid in target for valid in valid_agents), (
        f"Scenario {scenario_id}: Expected agent '{expected}' "
        f"(or {alternatives}), got '{target}'\n"
        f"Reasoning: {result.reasoning}"
    )


# --- Delegation Routing Tests -------------------------------------------------


@pytest.mark.parametrize(
    "scenario",
    DELEGATION_SCENARIOS,
    ids=[s["id"] for s in DELEGATION_SCENARIOS],
)
def test_delegation_routing(adapter: StructuredOutputAdapter, scenario: dict):
    """Verify PM delegates to the correct agent for implementation/research/ops/qa tasks."""
    try:
        result = adapter.query_with_consensus(scenario["prompt"])
    except InfrastructureError as e:
        pytest.skip(f"Infrastructure error: {e}")

    _assert_delegates_to(
        result,
        scenario["expected_agent"],
        scenario.get("agent_alternatives", []),
        scenario["id"],
        scenario["prompt"],
    )


# --- No-Delegation Tests ------------------------------------------------------


@pytest.mark.parametrize(
    "scenario",
    NO_DELEGATION_SCENARIOS,
    ids=[s["id"] for s in NO_DELEGATION_SCENARIOS],
)
def test_no_delegation_when_trivial(adapter: StructuredOutputAdapter, scenario: dict):
    """Verify PM handles trivial PM-capability questions directly."""
    try:
        result = adapter.query_with_consensus(scenario["prompt"])
    except InfrastructureError as e:
        pytest.skip(f"Infrastructure error: {e}")

    # PM should either not delegate or explicitly say it handles directly
    assert not result.would_delegate or result.would_handle_directly, (
        f"Scenario {scenario['id']}: PM tried to delegate a trivial task: "
        f"'{scenario['prompt']}'\n"
        f"Target: {result.target_agent}\n"
        f"Reasoning: {result.reasoning}"
    )


# --- Context Quality Tests ----------------------------------------------------


@pytest.mark.parametrize(
    "scenario",
    CONTEXT_QUALITY_SCENARIOS,
    ids=[s["id"] for s in CONTEXT_QUALITY_SCENARIOS],
)
def test_context_quality(adapter: StructuredOutputAdapter, scenario: dict):
    """Verify delegation reasoning contains relevant context from the prompt."""
    try:
        result = adapter.query_with_consensus(scenario["prompt"])
    except InfrastructureError as e:
        pytest.skip(f"Infrastructure error: {e}")

    # Must delegate
    _assert_delegates_to(
        result,
        scenario["expected_agent"],
        scenario.get("agent_alternatives", []),
        scenario["id"],
        scenario["prompt"],
    )

    # CTX-01: Check that reasoning references original task keywords
    if "expected_keywords" in scenario:
        reasoning_lower = result.reasoning.lower()
        matched = [kw for kw in scenario["expected_keywords"] if kw in reasoning_lower]
        assert len(matched) >= 2, (
            f"Scenario {scenario['id']}: Reasoning should reference task keywords. "
            f"Expected >= 2 of {scenario['expected_keywords']}, "
            f"found {matched} in: '{result.reasoning[:200]}'"
        )

    # CTX-02: Reasoning must be meaningful (not empty/trivial)
    assert len(result.reasoning) > 50, (
        f"Scenario {scenario['id']}: Reasoning too short ({len(result.reasoning)} chars): "
        f"'{result.reasoning}'"
    )


# --- Circuit Breaker Compliance Tests -----------------------------------------


@pytest.mark.parametrize(
    "scenario",
    CIRCUIT_BREAKER_SCENARIOS,
    ids=[s["id"] for s in CIRCUIT_BREAKER_SCENARIOS],
)
def test_circuit_breaker_compliance(adapter: StructuredOutputAdapter, scenario: dict):
    """Verify PM delegates tasks that would violate circuit breakers."""
    try:
        result = adapter.query_with_consensus(scenario["prompt"])
    except InfrastructureError as e:
        pytest.skip(f"Infrastructure error: {e}")

    # Circuit breaker scenarios MUST delegate (never handle directly)
    assert result.would_delegate, (
        f"Scenario {scenario['id']} (Circuit Breaker #{scenario['circuit_breaker']}): "
        f"PM chose to handle directly instead of delegating!\n"
        f"Prompt: '{scenario['prompt'][:100]}...'\n"
        f"Reasoning: {result.reasoning}"
    )

    assert not result.would_handle_directly, (
        f"Scenario {scenario['id']} (Circuit Breaker #{scenario['circuit_breaker']}): "
        f"PM said would_handle_directly=true for a circuit breaker scenario!\n"
        f"Justification: {result.delegation.get('direct_handling_justification', 'none')}"
    )

    # Verify correct agent routing
    _assert_delegates_to(
        result,
        scenario["expected_agent"],
        scenario.get("agent_alternatives", []),
        scenario["id"],
        scenario["prompt"],
    )


# --- Cost Tracking ------------------------------------------------------------


def test_cost_summary(adapter: StructuredOutputAdapter):
    """Report cost summary (always passes - informational only)."""
    stats = adapter.stats
    print(f"\n{'=' * 60}")
    print("Tier 2 Cost Summary:")
    print(f"  Invocations: {stats['invocation_count']}")
    print(f"  Total cost:  ${stats['total_cost_usd']:.4f}")
    print(f"  Avg cost:    ${stats['avg_cost_usd']:.4f}")
    print(f"{'=' * 60}")
    # This test always passes - it's for reporting only
