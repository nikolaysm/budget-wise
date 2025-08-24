SHELL := /bin/sh

# Virtual environment path
VENV := backend/.venv
PY := $(VENV)/bin/python
UV := uv
UVICORN := $(VENV)/bin/uvicorn
ALEMBIC := $(VENV)/bin/alembic
FRONTEND_DIR := frontend
PNPM := pnpm

.PHONY: help
help:
	@echo "Targets:"
	@echo "  uv-setup        Create venv and install backend deps with uv"
	@echo "  uv-update       Update/sync deps from requirements.txt"
	@echo "  run-backend     Run FastAPI with reload (local)"
	@echo "  alembic-rev     Create Alembic revision (AUTOGEN=message)"
	@echo "  alembic-up      Apply migrations (upgrade head)"
	@echo "  compose-up      docker compose up --build"
	@echo "  compose-down    docker compose down -v"
	@echo "  compose-watch   docker compose up --watch --build (dev)"
	@echo "  compose-down-watch docker compose down --remove-orphans (dev)"
	@echo "  run-db          Start Postgres database (docker compose up -d postgres
	@echo "  frontend-install Install frontend deps with pnpm"
	@echo "  frontend-dev     Run Next.js dev server"
	@echo "  frontend-build   Build Next.js production bundle"
	@echo "  frontend-lint    Run ESLint on frontend"
	@echo "  frontend-typecheck Run TypeScript type check (no emit)"

$(VENV):
	@echo "[uv] Creating project venv inside backend and syncing deps"
	command -v uv >/dev/null 2>&1 || (echo "[uv] Installing uv" && curl -LsSf https://astral.sh/uv/install.sh | sh)
	# Load uv installer env (if present) and ensure ~/.local/bin on PATH for this shell
	[ -f "$$HOME/.local/bin/env" ] && . "$$HOME/.local/bin/env" || true; export PATH="$$HOME/.local/bin:$$PATH"; \
	cd backend && uv venv && uv sync

.PHONY: uv-setup
uv-setup: $(VENV)
	@echo "[uv] Project synced (pyproject.toml)"

.PHONY: uv-set
uv-set: uv-setup

.PHONY: uv-update
uv-update: $(VENV)
	@echo "[uv] Syncing backend project dependencies"
	[ -f "$$HOME/.local/bin/env" ] && . "$$HOME/.local/bin/env" || true; export PATH="$$HOME/.local/bin:$$PATH"; \
	cd backend && $(UV) sync

.PHONY: run-backend
run-backend: uv-setup uv-update
	@echo "[run] Starting FastAPI (reload)"
	[ -f "$$HOME/.local/bin/env" ] && . "$$HOME/.local/bin/env" || true; export PATH="$$HOME/.local/bin:$$PATH"; \
	cd backend && $(UV) run uvicorn app.main:app --reload

.PHONY: alembic-rev
alembic-rev: uv-setup
	@if [ -z "$(AUTOGEN)" ]; then echo "Usage: make alembic-rev AUTOGEN=message"; exit 1; fi
	[ -f "$$HOME/.local/bin/env" ] && . "$$HOME/.local/bin/env" || true; export PATH="$$HOME/.local/bin:$$PATH"; \
	cd backend && $(UV) run alembic revision --autogenerate -m "$(AUTOGEN)"

.PHONY: alembic-up
alembic-up: uv-setup
	[ -f "$$HOME/.local/bin/env" ] && . "$$HOME/.local/bin/env" || true; export PATH="$$HOME/.local/bin:$$PATH"; \
	cd backend && $(UV) run alembic upgrade head

.PHONY: compose-up
compose-up:
	@echo "[docker] Building and starting services"
	docker compose up --build

.PHONY: compose-down
compose-down:
	@echo "[docker] Stopping and removing services + orphans"
	docker compose down --remove-orphans

.PHONY: compose-watch
compose-watch:
	@echo "[docker] Building and starting services with watchers"
	docker compose -f docker-compose.dev.yml up --watch --build

.PHONY: compose-watch-down
compose-watch-down:
	@echo "[docker] Stopping and removing services + orphans"
	docker compose -f docker-compose.dev.yml down --remove-orphans

# Frontend (pnpm) helpers
.PHONY: frontend-install
frontend-install:
	@echo "[frontend] Installing dependencies (pnpm)"
	cd $(FRONTEND_DIR) && $(PNPM) install

.PHONY: frontend-dev
frontend-dev: frontend-install
	@echo "[frontend] Starting Next.js dev server"
	cd $(FRONTEND_DIR) && $(PNPM) dev

.PHONY: frontend-build
frontend-build: frontend-install
	@echo "[frontend] Building Next.js production bundle"
	cd $(FRONTEND_DIR) && $(PNPM) build

.PHONY: frontend-lint
frontend-lint: frontend-install
	@echo "[frontend] Linting"
	cd $(FRONTEND_DIR) && $(PNPM) lint

.PHONY: frontend-typecheck
frontend-typecheck: frontend-install
	@echo "[frontend] Type checking"
	cd $(FRONTEND_DIR) && $(PNPM) exec tsc --noEmit --project tsconfig.json

.PHONY: run-db
run-db:
	@echo "[docker] Starting Postgres database"
	docker compose -f docker-compose.dev.yml up -d postgres