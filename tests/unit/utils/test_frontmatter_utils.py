"""Tests for frontmatter_utils module."""

from claude_mpm.utils.frontmatter_utils import read_agent_type


def test_read_agent_type_prefers_agent_type():
    """When both fields present, agent_type takes precedence."""
    data = {"agent_type": "engineer", "type": "core"}
    assert read_agent_type(data) == "engineer"


def test_read_agent_type_falls_back_to_type():
    """When only type present, falls back to type."""
    data = {"type": "research"}
    assert read_agent_type(data) == "research"


def test_read_agent_type_only_agent_type():
    """When only agent_type present, returns it."""
    data = {"agent_type": "ops"}
    assert read_agent_type(data) == "ops"


def test_read_agent_type_neither_present():
    """When neither field present, returns default."""
    data = {"name": "test"}
    assert read_agent_type(data) == "general"


def test_read_agent_type_custom_default():
    """Custom default value works."""
    data = {}
    assert read_agent_type(data, "custom") == "custom"
