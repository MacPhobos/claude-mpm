"""Load agent configuration state from agent_states.json.

This module reads the sparse override file written by ``claude-mpm configure``.
The file only tracks agents whose state was explicitly changed — agents NOT in
the file are considered enabled by default (matching ``SimpleAgentManager``).

The key function is ``load_effective_enabled_agents()`` which preserves
currently deployed agents minus any explicitly disabled in the states file.

Design rationale:
  ``agent_states.json`` is a *sparse override* — it records only the agents
  a user explicitly toggled.  Agents absent from the file default to enabled.
  We therefore cannot enumerate "all enabled" from the file alone.

  Instead we use the **deployed** set (files already in ``.claude/agents/``)
  as the baseline of what the user intends to keep, subtract any agents the
  user explicitly disabled, and return that as the configured list.  The
  reconciler then adds ``required`` and ``universal`` on top.
"""

import json
import logging
from pathlib import Path

try:
    from claude_mpm.utils.agent_filters import normalize_agent_id
except ImportError:

    def normalize_agent_id(name: str) -> str:  # type: ignore[misc]
        return name


logger = logging.getLogger(__name__)


def _load_agent_states(project_path: Path) -> dict | None:
    """Load raw agent_states.json, returning None if not found/corrupt."""
    states_file = project_path / ".claude-mpm" / "agent_states.json"

    if not states_file.exists():
        return None

    try:
        with states_file.open() as f:
            states = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read agent_states.json, skipping: %s", exc)
        return None

    if not isinstance(states, dict):
        logger.warning(
            "agent_states.json has unexpected format (expected dict), skipping"
        )
        return None

    return states


def load_disabled_agents_from_states(
    project_path: Path,
) -> tuple[bool, set[str]]:
    """Return (file_exists, set of explicitly disabled agent names).

    Args:
        project_path: Root directory containing ``.claude-mpm/``.

    Returns:
        ``(True, {disabled_ids})`` when the file exists, or
        ``(False, set())`` when it does not (or is corrupt).
    """
    states = _load_agent_states(project_path)
    if states is None:
        return (False, set())

    disabled: set[str] = set()
    for agent_name, agent_data in states.items():
        normalized = normalize_agent_id(agent_name)
        if isinstance(agent_data, dict) and not agent_data.get("enabled", True):
            disabled.add(normalized)

    return (True, disabled)


def load_effective_enabled_agents(
    project_path: Path,
    deploy_dir: Path | None = None,
) -> list[str]:
    """Compute the configured agent list: deployed - explicitly_disabled.

    Since ``agent_states.json`` is a sparse override we cannot derive the
    full enabled set from the file alone.  Instead we read the agents that
    are **currently deployed** (already in ``.claude/agents/``) and remove
    any that the user explicitly disabled.  The reconciler later unions this
    with ``required`` and ``universal`` agents.

    Args:
        project_path: Project root (for ``.claude-mpm/agent_states.json``
            and ``.claude/agents/``).
        deploy_dir: Override for the deployed-agents directory (testing).

    Returns:
        Sorted list of agent IDs to keep, or empty list when the states
        file does not exist (i.e. ``configure`` was never run).
    """
    if deploy_dir is None:
        deploy_dir = project_path / ".claude" / "agents"

    # 1. Read the sparse override file
    found, disabled = load_disabled_agents_from_states(project_path)
    if not found:
        return []

    # 2. Read currently deployed agents as the baseline
    deployed: set[str] = set()
    if deploy_dir.exists():
        for agent_file in deploy_dir.glob("*.md"):
            agent_id = normalize_agent_id(agent_file.stem)
            if agent_id:
                deployed.add(agent_id)

    if not deployed:
        logger.debug("No deployed agents found in %s", deploy_dir)
        return []

    # 3. Subtract explicitly disabled agents
    enabled = sorted(deployed - disabled)

    if not enabled and deployed:
        logger.debug(
            "agent_states.json disables all %d deployed agents",
            len(deployed),
        )

    return enabled


# Backward-compatible alias
def load_enabled_agents_from_states(project_path: Path) -> list[str]:
    """Legacy wrapper — delegates to :func:`load_effective_enabled_agents`.

    .. deprecated:: Use ``load_effective_enabled_agents()`` directly.
    """
    return load_effective_enabled_agents(project_path)
