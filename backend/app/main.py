"""
FastAPI application factory and router registration.

This module instantiates the FastAPI app, registers API routers, and
initializes the database on startup. It is separated into its own file
to avoid circular imports and to allow the `app` instance to be
"""

from fastapi import FastAPI

from app.api.routes import transactions_router, version_router
from app.version import get_version


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    application = FastAPI(title="BudgetWise API", version=get_version())

    # Register routers with prefixes and tags
    application.include_router(
        transactions_router,
        prefix="/transactions",
        tags=["transactions"],
    )

    # Register version router without prefix
    application.include_router(version_router)

    return application


# Create a global app instance for Uvicorn to use. When testing, you can
# import and call `create_app()` directly to obtain a fresh application.
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
