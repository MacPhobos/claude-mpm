"""Immutable context object for scope-aware deployment path resolution.

WHY: Provides a single, frozen value object that captures the deployment scope
and project path at the entry point (CLI command or API request), then gets passed
to services. Thread-safe for async API handlers. All path resolution delegates
to config_scope.py — no new path logic here.

Usage in CLI:
    ctx = DeploymentContext.from_project(project_dir)
    ctx = DeploymentContext.from_user()

Usage in API handlers:
    ctx = DeploymentContext.from_request_scope(body.get("scope", "project"))
    agents_dir = ctx.agents_dir
"""

from dataclasses import dataclass
from pathlib import Path

from .config_scope import (
    ConfigScope,
    resolve_agents_dir,
    resolve_archive_dir,
    resolve_config_dir,
    resolve_skills_dir,
)


@dataclass(frozen=True)
class DeploymentContext:
    """Immutable context capturing scope and project path.

    Created once at the request or command entry point and passed to
    services. Thread-safe (frozen dataclass) for use in async API handlers.
    """

    scope: ConfigScope
    project_path: Path

    @classmethod
    def from_project(cls, project_path: Path | None = None) -> "DeploymentContext":
        """Create a project-scoped context.

        Args:
            project_path: Root directory of the project. Defaults to cwd.
        """
        return cls(scope=ConfigScope.PROJECT, project_path=project_path or Path.cwd())

    @classmethod
    def from_user(cls) -> "DeploymentContext":
        """Create a user-scoped context (paths under ~/.claude/)."""
        return cls(scope=ConfigScope.USER, project_path=Path.cwd())

    @classmethod
    def from_request_scope(
        cls, scope_str: str, project_path: Path | None = None
    ) -> "DeploymentContext":
        """Create from an HTTP request scope string (API use only).

        Currently only "project" is supported by the API. "user" and other
        values raise ValueError. This design is intentionally scope-extensible:
        adding user scope requires only changing the validation tuple.

        Raises:
            ValueError: If scope_str is not "project".
        """
        if scope_str not in ("project",):
            raise ValueError(
                f"Invalid scope '{scope_str}'. Currently only 'project' is supported."
            )
        return cls(
            scope=ConfigScope(scope_str), project_path=project_path or Path.cwd()
        )

    @property
    def agents_dir(self) -> Path:
        """Resolve the Claude Code agents deployment directory."""
        return resolve_agents_dir(self.scope, self.project_path)

    @property
    def skills_dir(self) -> Path:
        """Resolve the Claude Code skills directory."""
        return resolve_skills_dir(self.scope, self.project_path)

    @property
    def archive_dir(self) -> Path:
        """Resolve the agent archive directory."""
        return resolve_archive_dir(self.scope, self.project_path)

    @property
    def config_dir(self) -> Path:
        """Resolve the MPM configuration directory."""
        return resolve_config_dir(self.scope, self.project_path)

    @property
    def configuration_yaml(self) -> Path:
        """Resolve the path to configuration.yaml."""
        return self.config_dir / "configuration.yaml"
