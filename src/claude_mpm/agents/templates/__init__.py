"""
Agent Delegation Templates Module (DEPRECATED)
===============================================

This module is deprecated. The AGENT_TEMPLATES dict references .md template files
(e.g., documentation_agent.md, engineer_agent.md) that no longer exist in this
directory. Agent definitions now live in .claude/agents/*.md as YAML-frontmatter
Markdown files deployed directly by Claude Code.

All public functions emit DeprecationWarning when called.
"""

import warnings
from pathlib import Path
from typing import Dict, Optional

# Template directory path
TEMPLATE_DIR = Path(__file__).parent

# Core agent template mappings (DEPRECATED - these .md files no longer exist)
AGENT_TEMPLATES = {
    "documentation": "documentation_agent.md",
    "engineer": "engineer_agent.md",
    "qa": "qa_agent.md",
    "api_qa": "api_qa_agent.md",
    "web_qa": "web_qa_agent.md",
    "version_control": "version_control_agent.md",
    "research": "research_agent.md",
    "ops": "ops_agent.md",
    "security": "security_agent.md",
    "data_engineer": "data_engineer_agent.md",
}

# Agent nicknames for reference
AGENT_NICKNAMES = {
    "documentation": "Documenter",
    "engineer": "Engineer",
    "qa": "QA",
    "api_qa": "API QA",
    "web_qa": "Web QA",
    "version_control": "Versioner",
    "research": "Researcher",
    "ops": "Ops",
    "security": "Security",
    "data_engineer": "Data Engineer",
}


def get_template_path(agent_type: str) -> Optional[Path]:
    """
    Get the path to a specific agent's delegation template.

    .. deprecated::
        Template .md files no longer exist in this directory.
        Agent definitions now live in .claude/agents/*.md.

    Args:
        agent_type: The type of agent (e.g., 'documentation', 'engineer')

    Returns:
        Path to the template file or None if not found
    """
    warnings.warn(
        "get_template_path() is deprecated. Template .md files no longer exist "
        "in this directory. Agent definitions now live in .claude/agents/*.md.",
        DeprecationWarning,
        stacklevel=2,
    )
    template_file = AGENT_TEMPLATES.get(agent_type)
    if template_file:
        template_path = TEMPLATE_DIR / template_file
        if template_path.exists():
            return template_path
    return None


def load_template(agent_type: str) -> Optional[str]:
    """
    Load the delegation template content for a specific agent.

    .. deprecated::
        Template .md files no longer exist in this directory.
        Agent definitions now live in .claude/agents/*.md.

    Args:
        agent_type: The type of agent (e.g., 'documentation', 'engineer')

    Returns:
        Template content as string or None if not found
    """
    warnings.warn(
        "load_template() is deprecated. Template .md files no longer exist "
        "in this directory. Agent definitions now live in .claude/agents/*.md.",
        DeprecationWarning,
        stacklevel=2,
    )
    template_path = get_template_path(agent_type)
    if template_path:
        try:
            return template_path.read_text()
        except Exception as e:
            print(f"Error loading template for {agent_type}: {e}")
    return None


def get_available_templates() -> Dict[str, str]:
    """
    Get a dictionary of all available agent templates.

    .. deprecated::
        Template .md files no longer exist in this directory.
        Agent definitions now live in .claude/agents/*.md.

    Returns:
        Dictionary mapping agent types to their template filenames
    """
    warnings.warn(
        "get_available_templates() is deprecated. Template .md files no longer "
        "exist in this directory. Agent definitions now live in .claude/agents/*.md.",
        DeprecationWarning,
        stacklevel=2,
    )
    available = {}
    for agent_type, filename in AGENT_TEMPLATES.items():
        if (TEMPLATE_DIR / filename).exists():
            available[agent_type] = filename
    return available


def get_agent_nickname(agent_type: str) -> Optional[str]:
    """
    Get the nickname for a specific agent type.

    .. deprecated::
        This module is deprecated. Agent definitions now live in
        .claude/agents/*.md with name: field in YAML frontmatter.

    Args:
        agent_type: The type of agent

    Returns:
        Agent nickname or None if not found
    """
    warnings.warn(
        "get_agent_nickname() is deprecated. Agent definitions now live in "
        ".claude/agents/*.md with name: field in YAML frontmatter.",
        DeprecationWarning,
        stacklevel=2,
    )
    return AGENT_NICKNAMES.get(agent_type)
