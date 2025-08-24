#!/bin/sh
set -eu

echo "[entrypoint] Starting backend container..."

RUN_MIGRATIONS=${RUN_MIGRATIONS:-1}

if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "[entrypoint] Running Alembic migrations..."
  i=0
  until alembic -c /app/alembic.ini upgrade head; do
    i=$((i+1))
    [ "$i" -ge 10 ] && { echo "[entrypoint] Migrations failed after retries. Exiting." >&2; exit 1; }
    echo "[entrypoint] Alembic failed, retrying in 3s..."
    sleep 3
  done
  echo "[entrypoint] Migrations applied."
else
  echo "[entrypoint] Skipping migrations (RUN_MIGRATIONS=$RUN_MIGRATIONS)."
fi

echo "[entrypoint] Launching application: $@"
exec "$@"
