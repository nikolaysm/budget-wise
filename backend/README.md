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

## Background scheduler (category suggestions)

The project includes an APScheduler-based background job that periodically attempts to assign / suggest categories to uncategorized transactions using the ML hybrid classifier.

Job details:

- ID: `auto_category_suggestions`
- Default schedule: every 30 minutes (`CronTrigger(minute="*/30")`)
- Jitter: 30s (helps avoid thundering herd after restarts)
- Persistence: Jobs stored in the database via `SQLAlchemyJobStore` so schedule survives restarts.

Environment settings (see `app/core/config.py`):

- `SCHEDULER_ENABLED` (bool, default: `true`)
- `SCHEDULER_TIMEZONE` (default: `UTC`)

### Running the scheduler manually

Run a single suggestion pass (useful for testing):

```bash
cd backend
python -m app.services.scheduler suggest-once
```

Programmatic one-off inside Python:

```python
from app.services.scheduler import run_suggestions_once
run_suggestions_once()
```

### How locking works

When using PostgreSQL the job acquires a session-level advisory lock so only one instance (e.g. in a multi-replica deployment) performs the work. On non-Postgres databases (like local SQLite) the advisory lock is skipped automatically and the job just runs.

### Integrating with FastAPI (lifespan)

This project uses FastAPI's lifespan context to manage the scheduler. Example pattern:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
	start_scheduler()      # startup
	yield
	shutdown_scheduler()   # shutdown

app = FastAPI(lifespan=lifespan)
```

Advantages:

- Unified startup/shutdown logic in one place
- Clean test isolation (lifespan executed per app instance)

Note: The CLI now only supports a single run (`suggest-once`). Continuous scheduling happens automatically inside the FastAPI process via the lifespan context.

### Logs

Each run logs how many transactions received a non-null suggestion: `Scheduler: category suggestions produced X/Y non-null`.

### Adjusting frequency

Change the cron expression in `app/services/scheduler.py` inside the `sched.add_job` call (e.g. to run every 5 minutes use `CronTrigger(minute="*/5")`).
