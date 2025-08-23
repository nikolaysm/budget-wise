"""
FastAPI application factory and router registration.

This module instantiates the FastAPI app, registers API routers, and
initializes the database on startup. It is separated into its own file
to avoid circular imports and to allow the `app` instance to be
imported from `app.__init__`.
"""

from fastapi import FastAPI
from fastapi.routing import APIRouter

from app.api.endpoints import transactions
from app.version import get_version
from app.db.init_db import init_db


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    application = FastAPI(title="BudgetWise API", version=get_version())

    @application.on_event("startup")
    def on_startup() -> None:
        """Initialize resources on application startup.

        This function will create database tables if they do not already
        exist. Alembic should be used for migrations when the schema
        changes; this is purely for initial bootstrap.
        """

        init_db()

    # Register routers with prefixes and tags
    application.include_router(
        transactions,
        prefix="/transactions",
        tags=["transactions"],
    )

    # Lightweight version endpoint
    version_router = APIRouter()

    @version_router.get("/version", tags=["meta"])  # type: ignore[misc]
    def version() -> dict[str, str]:
        return {"version": get_version()}

    application.include_router(version_router)

    return application


# Create a global app instance for Uvicorn to use. When testing, you can
# import and call `create_app()` directly to obtain a fresh application.
app = create_app()