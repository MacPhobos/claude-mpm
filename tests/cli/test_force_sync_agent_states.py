"""Tests for --force-sync respecting agent_states.json (sparse override model).

``agent_states.json`` is a **sparse override** file — it only stores agents
that the user explicitly toggled in ``claude-mpm configure``.  Agents NOT in
the file are considered enabled by default.

The effective enabled set is computed as:
    currently_deployed_agents - explicitly_disabled_agents

The reconciler then unions this with ``required`` and ``universal`` agents.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from claude_mpm.services.agents.agent_states_loader import (
    load_disabled_agents_from_states,
    load_effective_enabled_agents,
    load_enabled_agents_from_states,  # backward-compat alias
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_deployed(tmp_path: Path, agent_names: list[str]) -> Path:
    """Create a fake .claude/agents/ directory with agent .md files."""
    deploy_dir = tmp_path / ".claude" / "agents"
    deploy_dir.mkdir(parents=True)
    for name in agent_names:
        (deploy_dir / f"{name}.md").write_text(f"# {name} agent")
    return deploy_dir


def _setup_states(tmp_path: Path, states: dict) -> None:
    """Write agent_states.json to .claude-mpm/."""
    config_dir = tmp_path / ".claude-mpm"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "agent_states.json").write_text(json.dumps(states))


# ---------------------------------------------------------------------------
# load_disabled_agents_from_states
# ---------------------------------------------------------------------------


class TestLoadDisabledAgentsFromStates:
    """Tests for the low-level disabled-agents reader."""

    def test_returns_disabled_agents(self, tmp_path: Path) -> None:
        _setup_states(
            tmp_path,
            {
                "engineer": {"enabled": True},
                "designer": {"enabled": False},
                "deprecated": {"enabled": False},
            },
        )
        found, disabled = load_disabled_agents_from_states(tmp_path)
        assert found is True
        assert disabled == {"designer", "deprecated"}

    def test_empty_states_returns_no_disabled(self, tmp_path: Path) -> None:
        _setup_states(tmp_path, {})
        found, disabled = load_disabled_agents_from_states(tmp_path)
        assert found is True
        assert disabled == set()

    def test_no_file_returns_not_found(self, tmp_path: Path) -> None:
        found, disabled = load_disabled_agents_from_states(tmp_path)
        assert found is False
        assert disabled == set()

    def test_corrupt_json_returns_not_found(self, tmp_path: Path) -> None:
        config_dir = tmp_path / ".claude-mpm"
        config_dir.mkdir()
        (config_dir / "agent_states.json").write_text("NOT JSON")
        found, disabled = load_disabled_agents_from_states(tmp_path)
        assert found is False
        assert disabled == set()

    def test_non_dict_json_returns_not_found(self, tmp_path: Path) -> None:
        config_dir = tmp_path / ".claude-mpm"
        config_dir.mkdir()
        (config_dir / "agent_states.json").write_text(json.dumps([1, 2, 3]))
        found, disabled = load_disabled_agents_from_states(tmp_path)
        assert found is False
        assert disabled == set()

    def test_missing_enabled_key_defaults_to_true(self, tmp_path: Path) -> None:
        _setup_states(
            tmp_path,
            {
                "engineer": {},  # no "enabled" key -> default True -> NOT disabled
                "research": {"enabled": False},
            },
        )
        found, disabled = load_disabled_agents_from_states(tmp_path)
        assert found is True
        assert disabled == {"research"}


# ---------------------------------------------------------------------------
# load_effective_enabled_agents (deployed - disabled)
# ---------------------------------------------------------------------------


class TestLoadEffectiveEnabledAgents:
    """Tests for the full computation: deployed - disabled."""

    def test_subtracts_disabled_from_deployed(self, tmp_path: Path) -> None:
        deploy_dir = _setup_deployed(
            tmp_path, ["engineer", "research", "qa", "designer"]
        )
        _setup_states(tmp_path, {"designer": {"enabled": False}})

        result = load_effective_enabled_agents(tmp_path, deploy_dir=deploy_dir)

        assert set(result) == {"engineer", "research", "qa"}
        assert "designer" not in result

    def test_empty_states_preserves_all_deployed(self, tmp_path: Path) -> None:
        """Empty states file (configure ran, nothing toggled) -> keep everything."""
        deploy_dir = _setup_deployed(tmp_path, ["engineer", "research", "qa"])
        _setup_states(tmp_path, {})

        result = load_effective_enabled_agents(tmp_path, deploy_dir=deploy_dir)

        assert set(result) == {"engineer", "research", "qa"}

    def test_no_states_file_returns_empty(self, tmp_path: Path) -> None:
        """No states file = configure never used -> return empty (use defaults)."""
        deploy_dir = _setup_deployed(tmp_path, ["engineer", "research"])

        result = load_effective_enabled_agents(tmp_path, deploy_dir=deploy_dir)

        assert result == []

    def test_no_deployed_agents_returns_empty(self, tmp_path: Path) -> None:
        """No deployed agents -> nothing to preserve."""
        _setup_states(tmp_path, {"engineer": {"enabled": True}})

        result = load_effective_enabled_agents(tmp_path, deploy_dir=tmp_path / "empty")

        assert result == []

    def test_output_is_sorted(self, tmp_path: Path) -> None:
        deploy_dir = _setup_deployed(tmp_path, ["zebra", "alpha", "middle"])
        _setup_states(tmp_path, {})

        result = load_effective_enabled_agents(tmp_path, deploy_dir=deploy_dir)

        assert result == ["alpha", "middle", "zebra"]

    def test_real_world_scenario_49_agents(self, tmp_path: Path) -> None:
        """Simulate the actual bug: 49 agents deployed, sparse states file."""
        agents = [f"agent-{i}" for i in range(49)]
        deploy_dir = _setup_deployed(tmp_path, agents)
        # User only toggled 2 agents in configure (sparse!)
        _setup_states(
            tmp_path,
            {
                "agent-0": {"enabled": True},  # Explicitly enabled (redundant)
                "agent-48": {"enabled": False},  # Explicitly disabled
            },
        )

        result = load_effective_enabled_agents(tmp_path, deploy_dir=deploy_dir)

        assert len(result) == 48  # 49 - 1 disabled
        assert "agent-48" not in result
        assert "agent-0" in result


# ---------------------------------------------------------------------------
# User-scope fallback
# ---------------------------------------------------------------------------


class TestLoadEffectiveEnabledAgentsUserScope:
    """Verify project-scope and user-scope paths work independently."""

    def test_falls_back_to_home_dir(self, tmp_path: Path) -> None:
        home_path = tmp_path / "fake-home"
        deploy_dir = _setup_deployed(tmp_path, ["engineer", "research"])

        # No states file in project
        project_path = tmp_path / "project"
        project_path.mkdir()

        # States file in "home"
        home_config = home_path / ".claude-mpm"
        home_config.mkdir(parents=True)
        (home_config / "agent_states.json").write_text(
            json.dumps({"research": {"enabled": False}})
        )

        # Project scope -> empty (no states file)
        assert load_effective_enabled_agents(project_path, deploy_dir=deploy_dir) == []

        # Home scope -> deployed minus disabled
        result = load_effective_enabled_agents(home_path, deploy_dir=deploy_dir)
        assert set(result) == {"engineer"}


# ---------------------------------------------------------------------------
# Profile override
# ---------------------------------------------------------------------------


class TestProfileOverridesAgentStates:
    """Profile should still take priority over agent_states.json."""

    def test_profile_takes_priority(self, tmp_path: Path) -> None:
        deploy_dir = _setup_deployed(
            tmp_path, ["engineer", "research", "qa", "security"]
        )
        _setup_states(tmp_path, {})

        states_enabled = load_effective_enabled_agents(tmp_path, deploy_dir=deploy_dir)
        assert len(states_enabled) == 4

        # Simulate startup.py: profile overrides
        mock_config = MagicMock()
        mock_config.agents.enabled = states_enabled
        profile_agents = {"engineer", "security"}
        mock_config.agents.enabled = list(profile_agents)

        assert set(mock_config.agents.enabled) == {"engineer", "security"}


# ---------------------------------------------------------------------------
# Backward-compat alias
# ---------------------------------------------------------------------------


class TestBackwardCompatAlias:
    """load_enabled_agents_from_states still works."""

    def test_alias_returns_empty_when_no_states(self, tmp_path: Path) -> None:
        result = load_enabled_agents_from_states(tmp_path)
        assert result == []
