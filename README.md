# Budget Wise

Monorepo for a budgeting app with a FastAPI + SQLModel backend and a Next.js frontend. The stack is containerized with Docker Compose and uses PostgreSQL by default.

## Project structure

```
.
├── backend/          # FastAPI API, SQLModel models, Alembic migrations
├── frontend/         # Next.js app (TypeScript)
├── docker-compose.yml
├── Makefile          # uv-powered local tasks
└── .github/workflows # CI (pylint)
```

## Prerequisites
- Docker & Docker Compose (recommended to run the full stack)
- Or Python 3.11 with [uv](https://docs.astral.sh/uv/) for local backend dev
- Node.js 20+ for local frontend dev (if not using Docker)

## Quick start (Docker)

This builds and runs Postgres, the backend, and the frontend.

```sh
# from repo root
docker compose up --build
```

- Backend: http://localhost:8000 (OpenAPI docs: http://localhost:8000/docs)
- Frontend: http://localhost:3000

## Local development (uv + Node)

Backend (FastAPI):
```sh
# create venv and install deps with uv
make uv-set
# run FastAPI in reload mode
make run-backend
```

Environment variables:
- Copy `backend/.env.example` to `backend/.env` and adjust as needed.
- Default uses Postgres: `database_url=postgresql+psycopg://budget_user:budget_pass@localhost:5432/budget_db`
- Docker overrides the database host to the `postgres` service automatically.

Frontend (Next.js + pnpm):
```sh
cd frontend
corepack enable   # if not already
pnpm install
pnpm dev
```
- Ensure `NEXT_PUBLIC_API_BASE_URL` points to your backend (defaults to http://localhost:8000 in Docker).
- This project now uses **pnpm** (lockfile: `pnpm-lock.yaml`).

## Makefile targets
Useful helpers (run from repo root):
- `make uv-set` – create venv and install backend deps with uv
- `make run-backend` – run FastAPI with reload
- `make alembic-rev AUTOGEN="message"` – create Alembic migration
- `make alembic-up` – upgrade DB to head
- `make compose-up` / `make compose-down` – Docker lifecycle

## CI
- Backend: Pylint on push/PR to `main` (`.github/workflows/pylint.yml`).
- Frontend: Build + lint with pnpm (`.github/workflows/frontend-build.yml`).

## Notes
- Package managers: Backend uses `uv`, frontend uses `pnpm`.
- Tailwind CSS v4 (using `@tailwindcss/postcss` plugin) and Next.js 15.
- The project uses Pydantic v2 and `pydantic-settings`.
- PostgreSQL driver: `psycopg` (v3).
- Alembic reads the database URL from app settings; compose and `.env` control it.

## Troubleshooting
- Missing imports in editor: run `make uv-set` to populate the venv.
- DB connection errors locally: ensure Postgres is running or use Docker Compose.
- Alembic “no revisions” warning is normal until you create your first migration.
