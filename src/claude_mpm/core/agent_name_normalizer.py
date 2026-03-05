"""Agent name normalization utilities for consistent naming across the system."""

from typing import Optional

from claude_mpm.core.logging_utils import get_logger

logger = get_logger(__name__)


class AgentNameNormalizer:
    """
    Handles agent name normalization to ensure consistency across:
    - TodoWrite prefixes
    - Task tool display
    - Agent type identification
    - Color coding
    """

    # Canonical agent names (standardized format)
    # These are the display names used in TodoWrite prefixes
    CANONICAL_NAMES = {
        "research": "Research",
        "engineer": "Engineer",
        "qa": "QA",
        "security": "Security",
        "documentation": "Documentation",
        "ops": "Ops",
        "version-control": "Version Control",
        "data-engineer": "Data Engineer",
        "architect": "Architect",
        "pm": "PM",
        # Additional agent types from deployed agents
        "python-engineer": "Python Engineer",
        "golang-engineer": "Golang Engineer",
        "java-engineer": "Java Engineer",
        "javascript-engineer": "JavaScript Engineer",
        "typescript-engineer": "TypeScript Engineer",
        "rust-engineer": "Rust Engineer",
        "ruby-engineer": "Ruby Engineer",
        "php-engineer": "PHP Engineer",
        "phoenix-engineer": "Phoenix Engineer",
        "nestjs-engineer": "NestJS Engineer",
        "react-engineer": "React Engineer",
        "nextjs-engineer": "NextJS Engineer",
        "svelte-engineer": "Svelte Engineer",
        "dart-engineer": "Dart Engineer",
        "tauri-engineer": "Tauri Engineer",
        "prompt-engineer": "Prompt Engineer",
        "refactoring-engineer": "Refactoring Engineer",
        # QA variants
        "api-qa": "API QA",
        "web-qa": "Web QA",
        "real-user": "Real User",
        # Ops variants
        "clerk-ops": "Clerk Ops",
        "digitalocean-ops": "DigitalOcean Ops",
        "gcp-ops": "GCP Ops",
        "local-ops": "Local Ops",
        "vercel-ops": "Vercel Ops",
        "project-organizer": "Project Organizer",
        "agentic-coder-optimizer": "Agentic Coder Optimizer",
        "tmux": "Tmux",
        # Universal agents
        "code-analyzer": "Code Analyzer",
        "content": "Content",
        "memory-manager": "Memory Manager",
        "product-owner": "Product Owner",
        "web-ui": "Web UI",
        "imagemagick": "ImageMagick",
        "ticketing": "Ticketing",
        # MPM-specific agents
        "mpm-agent-manager": "MPM Agent Manager",
        "mpm-skills-manager": "MPM Skills Manager",
        "tavily-research": "Research",  # Maps to Research
    }

    # Aliases and variations that map to canonical names
    # Keys are normalized (lowercase, underscores) and map to canonical keys
    ALIASES = {
        # Research variations
        "research": "research",
        "researcher": "research",
        "tavily-research": "research",
        # Engineer variations
        "engineer": "engineer",
        "engineering": "engineer",
        "dev": "engineer",
        "developer": "engineer",
        # Language-specific engineers
        "python-engineer": "python-engineer",
        "python": "python-engineer",
        "golang-engineer": "golang-engineer",
        "golang": "golang-engineer",
        "go-engineer": "golang-engineer",
        "java-engineer": "java-engineer",
        "java": "java-engineer",
        "javascript-engineer": "javascript-engineer",
        "javascript": "javascript-engineer",
        "js-engineer": "javascript-engineer",
        "typescript-engineer": "typescript-engineer",
        "typescript": "typescript-engineer",
        "ts-engineer": "typescript-engineer",
        "rust-engineer": "rust-engineer",
        "rust": "rust-engineer",
        "ruby-engineer": "ruby-engineer",
        "ruby": "ruby-engineer",
        "php-engineer": "php-engineer",
        "php": "php-engineer",
        "phoenix-engineer": "phoenix-engineer",
        "phoenix": "phoenix-engineer",
        "elixir-engineer": "phoenix-engineer",
        "nestjs-engineer": "nestjs-engineer",
        "nestjs": "nestjs-engineer",
        # Frontend engineers
        "react-engineer": "react-engineer",
        "react": "react-engineer",
        "nextjs-engineer": "nextjs-engineer",
        "nextjs": "nextjs-engineer",
        "next": "nextjs-engineer",
        "svelte-engineer": "svelte-engineer",
        "svelte": "svelte-engineer",
        "web-ui": "web-ui",
        # Mobile/Desktop engineers
        "dart-engineer": "dart-engineer",
        "dart": "dart-engineer",
        "flutter-engineer": "dart-engineer",
        "flutter": "dart-engineer",
        "tauri-engineer": "tauri-engineer",
        "tauri": "tauri-engineer",
        # Specialized engineers
        "prompt-engineer": "prompt-engineer",
        "refactoring-engineer": "refactoring-engineer",
        "refactoring": "refactoring-engineer",
        # QA variations
        "qa": "qa",
        "quality": "qa",
        "testing": "qa",
        "test": "qa",
        "api-qa": "api-qa",
        "web-qa": "web-qa",
        "real-user": "real-user",
        # Security variations
        "security": "security",
        "sec": "security",
        # Documentation variations
        "documentation": "documentation",
        "docs": "documentation",
        "doc": "documentation",
        "ticketing": "ticketing",
        # Ops variations
        "ops": "ops",
        "operations": "ops",
        "devops": "ops",
        "clerk-ops": "clerk-ops",
        "clerk": "clerk-ops",
        "digitalocean-ops": "digitalocean-ops",
        "digitalocean": "digitalocean-ops",
        "do-ops": "digitalocean-ops",
        "gcp-ops": "gcp-ops",
        "gcp": "gcp-ops",
        "google-cloud": "gcp-ops",
        "local-ops": "local-ops",
        "local": "local-ops",
        "vercel-ops": "vercel-ops",
        "vercel": "vercel-ops",
        "project-organizer": "project-organizer",
        "agentic-coder-optimizer": "agentic-coder-optimizer",
        "tmux": "tmux",
        "tmux-agent": "tmux",
        # Version Control variations
        "version-control": "version-control",
        "git": "version-control",
        "vcs": "version-control",
        # Data Engineer variations
        "data-engineer": "data-engineer",
        "data": "data-engineer",
        # Architect variations
        "architect": "architect",
        "architecture": "architect",
        "arch": "architect",
        # PM variations
        "pm": "pm",
        "project-manager": "pm",
        # Universal agents
        "code-analyzer": "code-analyzer",
        "analyzer": "code-analyzer",
        "content": "content",
        "content-agent": "content",
        "memory-manager": "memory-manager",
        "memory-manager-agent": "memory-manager",
        "product-owner": "product-owner",
        "po": "product-owner",
        "imagemagick": "imagemagick",
        # MPM-specific agents
        "mpm-agent-manager": "mpm-agent-manager",
        "agent-manager": "mpm-agent-manager",
        "mpm-skills-manager": "mpm-skills-manager",
        "skills-manager": "mpm-skills-manager",
    }

    # Agent colors for consistent display
    # Base agent colors
    AGENT_COLORS = {
        # Core agents
        "research": "\033[36m",  # Cyan
        "engineer": "\033[32m",  # Green
        "qa": "\033[33m",  # Yellow
        "security": "\033[31m",  # Red
        "documentation": "\033[34m",  # Blue
        "ops": "\033[35m",  # Magenta
        "version-control": "\033[37m",  # White
        "data-engineer": "\033[96m",  # Bright Cyan
        "architect": "\033[95m",  # Bright Magenta
        "pm": "\033[92m",  # Bright Green
        # Language-specific engineers (all use green variants)
        "python-engineer": "\033[32m",  # Green
        "golang-engineer": "\033[32m",  # Green
        "java-engineer": "\033[32m",  # Green
        "javascript-engineer": "\033[32m",  # Green
        "typescript-engineer": "\033[32m",  # Green
        "rust-engineer": "\033[32m",  # Green
        "ruby-engineer": "\033[32m",  # Green
        "php-engineer": "\033[32m",  # Green
        "phoenix-engineer": "\033[32m",  # Green
        "nestjs-engineer": "\033[32m",  # Green
        "react-engineer": "\033[32m",  # Green
        "nextjs-engineer": "\033[32m",  # Green
        "svelte-engineer": "\033[32m",  # Green
        "dart-engineer": "\033[32m",  # Green
        "tauri-engineer": "\033[32m",  # Green
        "prompt-engineer": "\033[32m",  # Green
        "refactoring-engineer": "\033[32m",  # Green
        "web-ui": "\033[32m",  # Green
        "imagemagick": "\033[32m",  # Green
        # QA variants (all use yellow)
        "api-qa": "\033[33m",  # Yellow
        "web-qa": "\033[33m",  # Yellow
        "real-user": "\033[33m",  # Yellow
        # Ops variants (all use magenta)
        "clerk-ops": "\033[35m",  # Magenta
        "digitalocean-ops": "\033[35m",  # Magenta
        "gcp-ops": "\033[35m",  # Magenta
        "local-ops": "\033[35m",  # Magenta
        "vercel-ops": "\033[35m",  # Magenta
        "project-organizer": "\033[35m",  # Magenta
        "agentic-coder-optimizer": "\033[35m",  # Magenta
        "tmux": "\033[35m",  # Magenta
        # Universal agents
        "code-analyzer": "\033[36m",  # Cyan (like research)
        "content": "\033[34m",  # Blue (like documentation)
        "memory-manager": "\033[36m",  # Cyan
        "product-owner": "\033[92m",  # Bright Green (like PM)
        "ticketing": "\033[34m",  # Blue (like documentation)
        # MPM-specific agents
        "mpm-agent-manager": "\033[95m",  # Bright Magenta
        "mpm-skills-manager": "\033[95m",  # Bright Magenta
    }

    COLOR_RESET = "\033[0m"

    @classmethod
    def normalize(cls, agent_name: str) -> str:
        """
        Normalize an agent name to its canonical form.

        Args:
            agent_name: The agent name to normalize

        Returns:
            The canonical agent name
        """
        if not agent_name:
            return "Engineer"  # Default

        # Clean the input: strip whitespace, convert to lowercase
        cleaned = agent_name.strip().lower()

        # Return default for whitespace-only input
        if not cleaned:
            return "Engineer"

        # Replace underscores and spaces with hyphens for consistent lookup
        cleaned = cleaned.replace("_", "-").replace(" ", "-")

        # Strip common suffixes before alias lookup
        # This handles cases like "research-agent" -> "research" or "python-engineer-agent" -> "python-engineer"
        for suffix in ("-agent", "-agent-agent"):
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)]
                break

        # Check aliases first (exact match)
        if cleaned in cls.ALIASES:
            canonical_key = cls.ALIASES[cleaned]
            return cls.CANONICAL_NAMES.get(canonical_key, "Engineer")

        # Check if it's already a canonical key (exact match)
        if cleaned in cls.CANONICAL_NAMES:
            return cls.CANONICAL_NAMES[cleaned]

        # Try partial matching - but only if the cleaned name contains the alias as a word boundary
        # This prevents "python-engineer" from matching just "engineer"
        # Sort aliases by length (longest first) to ensure more specific matches take priority
        sorted_aliases = sorted(
            cls.ALIASES.items(), key=lambda x: len(x[0]), reverse=True
        )
        for alias, canonical_key in sorted_aliases:
            # Only match if the cleaned name starts with or ends with the alias
            # Or if the alias is a complete match (already handled above)
            if cleaned == alias:
                return cls.CANONICAL_NAMES.get(canonical_key, "Engineer")
            # Allow partial match only for generic aliases (single words like "python", "react")
            # Don't allow "engineer" to match inside "python-engineer"
            if "-" not in alias and alias in cleaned.split("-"):
                return cls.CANONICAL_NAMES.get(canonical_key, "Engineer")

        logger.warning(f"Unknown agent name '{agent_name}', defaulting to Engineer")
        return "Engineer"

    @classmethod
    def to_key(cls, agent_name: str) -> str:
        """
        Convert an agent name to its key format (lowercase with hyphens).

        Args:
            agent_name: The agent name to convert

        Returns:
            The key format of the agent name
        """
        normalized = cls.normalize(agent_name)
        return normalized.lower().replace(" ", "-")

    @classmethod
    def to_todo_prefix(cls, agent_name: str) -> str:
        """
        Format agent name for TODO prefix (e.g., [Research]).

        Args:
            agent_name: The agent name to format

        Returns:
            The formatted TODO prefix
        """
        normalized = cls.normalize(agent_name)
        return f"[{normalized}]"

    @classmethod
    def colorize(cls, agent_name: str, text: Optional[str] = None) -> str:
        """
        Apply consistent color coding to agent names.

        Args:
            agent_name: The agent name to colorize
            text: Optional text to colorize (defaults to agent name)

        Returns:
            The colorized text
        """
        key = cls.to_key(agent_name)
        color = cls.AGENT_COLORS.get(key, "")
        display_text = text if text else cls.normalize(agent_name)

        if color:
            return f"{color}{display_text}{cls.COLOR_RESET}"
        return display_text

    @classmethod
    def extract_from_todo(cls, todo_text: str) -> Optional[str]:
        """
        Extract agent name from a TODO line.

        Args:
            todo_text: The TODO text (e.g., "[Research] Analyze patterns")

        Returns:
            The normalized agent name, or None if not found
        """
        import re

        # Match [Agent] at the beginning
        match = re.match(r"^\[([^\]]+)\]", todo_text.strip())
        if match:
            return cls.normalize(match.group(1))

        # Try to find agent mentions in the text
        text_lower = todo_text.lower()
        for alias, canonical_key in cls.ALIASES.items():
            if alias in text_lower:
                return cls.CANONICAL_NAMES.get(canonical_key)

        return None

    @classmethod
    def validate_todo_format(cls, todo_text: str) -> tuple[bool, Optional[str]]:
        """
        Validate that a TODO has proper agent prefix.

        Args:
            todo_text: The TODO text to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        agent = cls.extract_from_todo(todo_text)
        if not agent:
            return (
                False,
                "TODO must start with [Agent] prefix (e.g., [Research], [Engineer])",
            )

        # Check if it's a valid agent
        if cls.to_key(agent) not in cls.CANONICAL_NAMES:
            return (
                False,
                f"Unknown agent '{agent}'. Valid agents: {', '.join(cls.CANONICAL_NAMES.values())}",
            )

        return True, None

    @classmethod
    def to_task_format(cls, agent_name: str) -> str:
        """
        Convert agent name from TodoWrite format to Task tool format.

        Args:
            agent_name: The agent name in TodoWrite format (e.g., "Research", "Version Control")

        Returns:
            The agent name in Task tool format (e.g., "research", "version-control")

        Examples:
            "Research" → "research"
            "Version Control" → "version-control"
            "Data Engineer" → "data-engineer"
            "QA" → "qa"
        """
        # First normalize to canonical form
        normalized = cls.normalize(agent_name)
        # Convert to lowercase and replace spaces with hyphens
        return normalized.lower().replace(" ", "-")

    @classmethod
    def from_task_format(cls, task_format: str) -> str:
        """
        Convert agent name from Task tool format to TodoWrite format.

        Args:
            task_format: The agent name in Task tool format (e.g., "research", "version-control")

        Returns:
            The agent name in TodoWrite format (e.g., "Research", "Version Control")

        Examples:
            "research" → "Research"
            "version-control" → "Version Control"
            "data-engineer" → "Data Engineer"
            "qa" → "QA"
        """
        # Hyphen format matches canonical keys directly now
        lookup_key = task_format.lower()

        # Check if it's a valid canonical key
        if lookup_key in cls.CANONICAL_NAMES:
            return cls.CANONICAL_NAMES[lookup_key]

        # Try normalizing as-is
        return cls.normalize(task_format)


# Global instance for easy access
agent_name_normalizer = AgentNameNormalizer()
