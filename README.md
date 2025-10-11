# Budget Wise

Monorepo for a budgeting & transaction categorization app:

- **Backend:** FastAPI + SQLModel + Alembic (PostgreSQL in production, SQLite dev fallback)
- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind CSS v4
- **Data:** CSV ingestion & categorisation, filters, summaries, category editing

---

## Quick Usage (TL;DR)
1. Start stack: `docker compose up --build` (or run backend + `pnpm dev` for frontend).
2. Go to http://localhost:3000.
3. (If upload page present) Upload / import your bank CSV; transactions appear in the table.
4. Open Dashboard → pick a date range (shortcuts available) to view spending by category.
5. Click a category card to drill into filtered transactions.
6. In Transactions view: refine with text & date filters, inline edit or bulk-assign categories, then Reset to clear.
7. Return to Dashboard—your last date range persists via URL params for easy sharing.

For more detail see Section 5 (Using the Application).

---

## Contents

1. Project Structure
2. Quick Start (Docker)
3. Local Development
4. Environment Variables
5. Using the Application
6. API Usage
7. Database & Migrations
8. Lint / Format / Quality
9. Versioning & Releases
10. Conventional Commits
11. Make / Scripts
12. Troubleshooting
13. Roadmap

---

## 1. Project Structure

```
.
├── backend/             # FastAPI app, models, services, migrations
├── frontend/            # Next.js 15 app router UI
├── docker-compose.yml   # Postgres + backend + frontend
├── Makefile             # Helper targets (uv & compose)
└── .github/workflows    # CI pipelines
```

Backend highlights: `app/models`, `app/daos`, `app/services`, `app/api/routes`, `alembic/versions`.
Frontend highlights: `src/app` routes, `src/components`, `src/services/api.ts`.

---

## 2. Quick Start (Docker)

```sh
docker compose up --build
```

Services:

- API: http://localhost:8000 (docs at /docs)
- UI: http://localhost:3000

Tear down:

```sh
docker compose down -v
```

---

## 3. Local Development (Manual)

### Backend

```sh
make uv-set      # create .venv & install deps via uv
make run-backend # uvicorn reload server on :8000
```

Or manual steps: create venv, `uv pip install -r requirements.txt`, run `uvicorn app.main:app --reload`.

### Frontend

```sh
cd frontend
pnpm install
pnpm dev  # http://localhost:3000
```

Ensure `NEXT_PUBLIC_API_BASE_URL` matches backend (default http://localhost:8000).

---

## 4. Environment Variables

Backend (`backend/.env`):

- `DATABASE_URL` (or `database_url`) – SQLAlchemy URL. Docker sets Postgres host.
- `DB_ECHO` – SQL logging (dev)
- `ALLOWED_ORIGINS` – CORS list
- `OPENAI_API_KEY` / embedding model vars (optional future classification)
- `SCHEDULER_ENABLED`, `SCHEDULER_TIMEZONE`

Frontend (`frontend/.env.local`):

- `NEXT_PUBLIC_API_BASE_URL` – base URL for API

---

## 5. Using the Application

1. Dashboard: Pick date range (shortcuts: last 30 days, last six months). See category totals.
2. Click a category → Transactions view filtered by that category + date range.
3. Transactions Table: text filters, category filter, date range, has/has not category, bulk & inline category editing, Reset clears state + URL params.
4. Single transaction page: inspect details & (future) suggestions.
5. Categories page (planned enhancements) for management.

URL query keeps date range for shareable links.

---

## 6. API Usage

Key endpoints:

- `GET /transactions` with filters: `counterparty_name_ilike`, `transaction_type_ilike`, `notes_ilike`, `booking_date_gte`, `booking_date_lte`, `category_id`, `has_category`.
- `POST /transactions/{id}/category` `{ "category": "Groceries" }`
- `POST /transactions/bulk/category` `{ "ids": [..], "category": "Fuel" }`
- `GET /categories/summary` date-range summary
- `GET /version`

Example:

```sh
curl 'http://localhost:8000/transactions?limit=20&booking_date_gte=2025-01-01&booking_date_lte=2025-01-31'
```

---

## 7. Database & Migrations

Generate & apply:

```sh
cd backend
alembic revision --autogenerate -m "add field"
alembic upgrade head
```

Inside containers:

```sh
docker compose exec backend alembic upgrade head
```

SQLite for quick dev; Postgres for production features (advisory locks, scheduler persistence).

---

## 8. Lint / Format / Quality

Backend: Ruff (format, import order). Frontend: ESLint 9 flat config (import ordering, 4-space indent, hooks). Conventional Commits enforced in CI.

---

## 9. Versioning & Releases

Semantic version bumps via commit messages; workflow updates backend `pyproject.toml` + frontend `package.json` and tags `vX.Y.Z`. Endpoints: `/version` and `/api/version`.

---

## 10. Conventional Commits

Format `type(scope)!: subject`. Types: feat, fix, perf, refactor, chore, docs, test, build, ci, style. Use `!` or `BREAKING CHANGE:` footer for majors.

Examples:

```
feat(frontend): add date range quick shortcuts
fix(backend): handle empty csv row gracefully
feat!: switch primary key type to ULID

BREAKING CHANGE: existing references to integer IDs must be migrated.
```

---

## 11. Make / Scripts

Make: `uv-set`, `run-backend`, `alembic-rev`, `alembic-up`, `compose-up`, `compose-down`.
Frontend: `pnpm dev|build|start|lint`.

---

## 12. Troubleshooting

| Issue                   | Cause                     | Resolution                            |
| ----------------------- | ------------------------- | ------------------------------------- |
| 404 from UI             | Wrong API base            | Set `NEXT_PUBLIC_API_BASE_URL`        |
| DB connect fail         | Postgres not up           | Start Docker or adjust `DATABASE_URL` |
| No migrations generated | Models not imported       | Ensure model imports in Alembic env   |
| ESLint plugin missing   | Dependencies stale        | `pnpm install` in `frontend`          |
| Slow dev responses      | DB echo + reload overhead | Disable `DB_ECHO`, use Postgres       |

---

## 13. Roadmap

- Category suggestion ML improvements
- Budgets & variance tracking
- Multi-user auth / roles
- Export / import enhancements
- Tagging (multi-label) & rules engine
- E2E tests (Playwright), API tests (Pytest)

---

Happy budgeting! 🎯
