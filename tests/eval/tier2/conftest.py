"""Tier 2 test fixtures - structured output delegation intent tests."""

import json
import shutil
from pathlib import Path

import pytest

from tests.eval.adapters.structured_output_adapter import StructuredOutputAdapter


@pytest.fixture(scope="module")
def adapter():
    """Module-scoped adapter to benefit from prompt caching across sequential tests."""
    return StructuredOutputAdapter(max_budget_usd=0.50, timeout=45)


@pytest.fixture(scope="session")
def delegation_scenarios():
    """Load delegation scenarios from JSON."""
    scenarios_path = (
        Path(__file__).parent.parent / "scenarios" / "delegation_scenarios.json"
    )
    with open(scenarios_path) as f:
        data = json.load(f)
    return data["scenarios"]


def pytest_collection_modifyitems(config, items):
    """Skip Tier 2 tests if claude CLI is not available."""
    if not shutil.which("claude"):
        skip_marker = pytest.mark.skip(reason="claude CLI not available")
        for item in items:
            if "tier2" in item.keywords:
                item.add_marker(skip_marker)
