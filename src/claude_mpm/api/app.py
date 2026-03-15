"""FastAPI application factory for claude-mpm.

Creates and configures the ASGI application, mounting:
- CORS middleware (permissive defaults; tighten in production)
- The user auth router (/auth/*)
- A /health liveness probe

Usage (uvicorn)::

    uvicorn claude_mpm.api.app:app --reload

Usage (programmatic)::

    from claude_mpm.api.app import create_app
    app = create_app()
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from claude_mpm.auth.user.router import router as auth_router


def create_app(
    *,
    title: str = "claude-mpm API",
    version: str = "1.0.0",
    description: str = (
        "User authentication and project management API for claude-mpm. "
        "Provides JWT-based auth via /auth/* endpoints."
    ),
    allow_origins: list[str] | None = None,
) -> FastAPI:
    """Construct and configure the FastAPI application.

    Args:
        title: OpenAPI document title.
        version: API version string shown in /docs.
        description: OpenAPI document description.
        allow_origins: CORS origins to permit. Defaults to ``["*"]``.

    Returns:
        A fully configured FastAPI instance ready to serve.
    """
    application = FastAPI(
        title=title,
        version=version,
        description=description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------
    # CORS middleware
    # ------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    application.include_router(auth_router)

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------
    @application.get(
        "/health",
        tags=["ops"],
        summary="Liveness probe",
    )
    async def health() -> dict[str, str]:
        """Return service health status.

        Returns:
            A JSON object ``{"status": "ok"}``.
        """
        return {"status": "ok"}

    return application


# Module-level default instance (used by uvicorn entry-point).
app: FastAPI = create_app()
