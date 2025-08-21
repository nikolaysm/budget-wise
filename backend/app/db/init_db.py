"""
Initialize the database by creating tables defined via SQLModel metadata.

Call this function on application startup to ensure all tables exist. It will
not drop or modify existing tables. Use Alembic for schema migrations.
"""

from sqlmodel import SQLModel

from app.db.session import engine


def init_db() -> None:
    """Create all tables in the database using SQLModel metadata."""
    # Import models to register them with SQLModel metadata
    import app.models.user  # noqa: F401
    import app.models.account  # noqa: F401
    import app.models.category  # noqa: F401
    import app.models.transaction  # noqa: F401
    SQLModel.metadata.create_all(bind=engine)