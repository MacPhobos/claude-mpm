"""FastAPI application package for claude-mpm.

Exposes the application factory ``create_app`` and the default ``app``
instance for use with uvicorn or other ASGI servers.
"""

from claude_mpm.api.app import app, create_app

__all__ = ["app", "create_app"]
