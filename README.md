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
- Commit messages: Conventional Commits enforced by commitlint (`.github/workflows/commitlint.yml`).
	- Types used for versioning: `feat` → minor, `fix`/`perf`/`refactor`/`chore`/`docs`/`test`/`build`/`ci`/`style` → patch, add `!` or `BREAKING CHANGE:` for major.
	- Examples:
		- `feat: add budgets page`
		- `fix(upload): handle semicolon delimiter`
		- `feat!: change upload API` with body containing `BREAKING CHANGE: ...`

## Commit message guidelines

We use Conventional Commits so releases can be automated. Keep messages small and descriptive:

- Format: `type(scope)!: subject`
	- `type`: one of `feat`, `fix`, `perf`, `refactor`, `chore`, `docs`, `test`, `build`, `ci`, `style`.
	- `scope` (optional): area like `frontend`, `backend`, `upload`, `db`, `pipeline`.
	- `!` marks a breaking change (also add a `BREAKING CHANGE:` line in the body).
- Header rules (enforced):
	- Max 100 characters
	- No trailing period
- Body (optional but recommended):
	- Leave a blank line between header and body
	- Explain what and why, wrap lines around ~72–100 chars
- Breaking changes:
	- Use either `feat(scope)!: ...` or add a footer line: `BREAKING CHANGE: describe impact and migration`

Quick examples:
- `feat(frontend): add dropzone upload with progress`
- `fix(backend): parse CSV with semicolon delimiter`
- `chore(ci): add commitlint workflow`
- `docs: update README with versioning instructions`
- `refactor(api): simplify upload handler`
- `perf(db): speed up transaction listing query`
- `test: add unit tests for version endpoint`

## Versioning & releases

This repo uses Semantic Versioning (SemVer) and tags releases automatically:

- Auto-bump on default branch merges: `.github/workflows/release.yml` reads commit messages since the last tag and bumps versions in:
	- `frontend/package.json` (source for `/api/version` in the frontend)
	- `backend/pyproject.toml` (source for the FastAPI app version and `/version` endpoint)
- The workflow commits the bump and tags `vX.Y.Z`. A second job validates versions match the tag.
- Manual release: trigger the "Release" workflow with `bump=major|minor|patch` or `set 1.2.3`.

Endpoints:
- Backend: `GET /version` → `{ "version": "X.Y.Z" }`
- Frontend: `GET /api/version` → `{ "version": "X.Y.Z" }`

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
