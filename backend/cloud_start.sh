#!/bin/sh
set -eu
# Cloud deployments only: enable RUN_MIGRATIONS=true exclusively when the database
# has been prepared for Alembic (fresh empty DB or independently verified/stamped).
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running Alembic migrations (RUN_MIGRATIONS=true)"
  python -m alembic upgrade head
fi
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
