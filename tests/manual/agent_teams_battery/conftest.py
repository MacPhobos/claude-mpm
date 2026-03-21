"""Fixtures and skip conditions for Agent Teams battery tests."""

import os

import pytest


def pytest_addoption(parser):
    """Add --live option for live Agent Teams battery."""
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run live Agent Teams battery (requires active Claude Code session)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip all battery tests if Agent Teams env var is not set."""
    if os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") != "1":
        skip_marker = pytest.mark.skip(
            reason="Requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
        )
        for item in items:
            item.add_marker(skip_marker)
