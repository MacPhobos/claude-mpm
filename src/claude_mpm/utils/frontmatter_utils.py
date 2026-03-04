"""Utility for reading agent type field from frontmatter/dicts.

Both 'agent_type' and 'type' may be present in agent frontmatter.
This module provides a single function to read the correct field,
preferring 'agent_type' and falling back to 'type'.

PERMANENT: This normalization must remain even after migration,
as a safety net for user-customized agents (preserve_user_agents flag).
"""


def read_agent_type(data: dict, default: str = "general") -> str:
    """Read agent type from dict, checking agent_type first, then type.

    Args:
        data: Frontmatter dict or agent data dict
        default: Fallback value if neither field exists

    Returns:
        The agent type string value
    """
    return data.get("agent_type", data.get("type", default))
