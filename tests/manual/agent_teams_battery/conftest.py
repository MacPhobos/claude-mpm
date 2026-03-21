"""Fixtures and skip conditions for Agent Teams battery tests."""

import os

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip all battery tests if Agent Teams env var is not set."""
    if os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") != "1":
        skip_marker = pytest.mark.skip(
            reason="Requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
        )
        for item in items:
            item.add_marker(skip_marker)
