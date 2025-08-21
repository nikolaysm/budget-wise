"""
FastAPI application factory and router registration.

This module instantiates the FastAPI app, registers API routers, and
initializes the database on startup. It is separated into its own file
to avoid circular imports and to allow the `app` instance to be
imported from `app.__init__`.
"""

from fastapi import FastAPI

from app.api.endpoints import transactions
from app.db.init_db import init_db


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    application = FastAPI(title="BudgetWise API", version="0.1.0")

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

    return application


# Create a global app instance for Uvicorn to use. When testing, you can
# import and call `create_app()` directly to obtain a fresh application.
app = create_app()