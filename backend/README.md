# Backend: FastAPI with SQLModel

This backend provides a JSON API for parsing uploaded CSV or Excel files containing bank transactions, storing them in a relational database, and exposing them via a RESTful interface.

## Key components

- **FastAPI** – a modern, high‑performance web framework for building APIs.
- **SQLModel** – combines the ease of Pydantic models with SQLAlchemy’s ORM for type‑safe database models.
- **Alembic** – database migrations to evolve the schema over time.
- **Typed code** – all functions and models use Python type hints for better developer experience and static analysis.

## Project structure

```
backend/
├── alembic.ini            # Alembic configuration
├── alembic/               # Migration environment and generated revisions
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── __init__.py        # Mark app as a package
│   ├── main.py            # FastAPI application factory
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py      # Pydantic settings
│   ├── db/
│   │   ├── __init__.py
│   │   ├── init_db.py     # Create tables on startup
│   │   └── session.py     # Database engine and session dependency
│   ├── models/
│   │   ├── __init__.py
│   │   └── transaction.py # SQLModel definitions
│   ├── crud/
│   │   ├── __init__.py
│   │   └── transaction.py # CRUD utilities
│   └── api/
│       ├── __init__.py
│       ├── deps.py        # Dependency overrides
│       └── endpoints/
│           ├── __init__.py
│           └── transactions.py # API routes for transaction upload and retrieval
├── requirements.txt        # Python dependencies
└── .env.example            # Example environment variables
```

Run migrations with `alembic revision --autogenerate -m "message" && alembic upgrade head`. See `alembic/env.py` for configuration.

## Local development (with uv)

You can use uv for fast, reproducible installs.

1. Install uv (macOS/Linux):
	- `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Create and activate a virtualenv:
	- `uv venv .venv_budget`
	- `source .venv_budget/bin/activate`
3. Install dependencies:
	- `uv pip install -r requirements.txt`
4. Configure environment (copy `.env.example` to `.env` and edit as needed).
5. Run the app:
	- `uvicorn app.main:app --reload`

Note: The Dockerfile also uses uv to install dependencies inside the container.