"""Tier 3 test fixtures -- hook interception behavioral delegation tests."""

from __future__ import annotations

import shutil

import pytest

from tests.eval.adapters.hook_interception_harness import HookInterceptionHarness


def pytest_collection_modifyitems(config, items):
    """Skip Tier 3 tests if claude CLI is not available."""
    if not shutil.which("claude"):
        skip_marker = pytest.mark.skip(reason="claude CLI not available")
        for item in items:
            if "tier3" in item.keywords:
                item.add_marker(skip_marker)


@pytest.fixture()
def harness(tmp_path):
    """Create a HookInterceptionHarness in a fresh temporary directory.

    Calls ``setup()`` before the test and ``cleanup()`` after.
    """
    h = HookInterceptionHarness(workspace_dir=tmp_path)
    h.setup()
    yield h
    h.cleanup()
