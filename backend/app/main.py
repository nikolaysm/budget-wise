"""
FastAPI application factory and router registration.

This module instantiates the FastAPI app, registers API routers, and
initializes the database on startup. It is separated into its own file
to avoid circular imports and to allow the `app` instance to be
"""

import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import transactions_router, version_router
from app.api.routes.categories import router as categories_router
from app.core.config import LOGGING_CONFIG, get_settings
from app.services.scheduler import shutdown_scheduler, start_scheduler
from app.version import get_version

# Set logging configuration
logging.config.dictConfig(LOGGING_CONFIG)


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - simple resource mgmt
    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    settings = get_settings()
    application = FastAPI(title="BudgetWise API", version=get_version(), lifespan=lifespan)

    # CORS
    if settings.allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Register routers with prefixes and tags
    application.include_router(
        transactions_router,
        prefix="/transactions",
        tags=["transactions"],
    )

    application.include_router(
        categories_router,
        prefix="/categories",
        tags=["categories"],
    )

    # Register version router without prefix
    application.include_router(version_router)

    # Scheduler now handled via lifespan

    return application


# Create a global app instance for Uvicorn to use. When testing, you can
# import and call `create_app()` directly to obtain a fresh application.
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
