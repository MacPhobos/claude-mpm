"""Shared fixtures for Tier 1 structural tests."""

import pytest

from claude_mpm.core.framework_loader import FrameworkLoader


@pytest.fixture(scope="session")
def assembled_prompt():
    """Load the assembled PM prompt via FrameworkLoader.

    Session-scoped to avoid reloading for every test module.
    The prompt is deterministic, so caching is safe.
    """
    loader = FrameworkLoader(config={"validate_api_keys": False})
    return loader.get_framework_instructions()
