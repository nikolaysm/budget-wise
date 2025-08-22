#!/bin/sh
set -eu

echo "[entrypoint] Starting backend container..."

# Optional: wait for the database to be ready if DATABASE_URL is provided
if [ -n "${DATABASE_URL:-}" ]; then
  echo "[entrypoint] Waiting for database to be ready..."
  python - <<'PY'
import os, sys, time
try:
    import psycopg
except Exception as e:
    # psycopg not installed? skip wait
    print("[entrypoint] psycopg not available; skipping DB wait", flush=True)
    sys.exit(0)

url = os.environ.get("DATABASE_URL")
if not url:
    sys.exit(0)

max_attempts = 30
for i in range(max_attempts):
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            print("[entrypoint] Database is ready.")
            break
    except Exception as e:
        print(f"[entrypoint] DB not ready yet ({i+1}/{max_attempts}): {e}")
        time.sleep(1)
else:
    print("[entrypoint] Database is still not ready after waiting; exiting.", file=sys.stderr)
    sys.exit(1)
PY
fi

# Run migrations (if any)
echo "[entrypoint] Applying migrations (if any)..."
alembic upgrade head || echo "[entrypoint] No migrations to apply"

echo "[entrypoint] Launching application: $@"
exec "$@"
