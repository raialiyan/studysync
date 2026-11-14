#!/bin/sh
set -eu
cd "$HOME/Documents/studysync"
if ! docker compose --env-file .env.docker ps --status running --services | grep -qx 'db'; then
  echo 'Database container is not running; start StudySync via docker compose up -d first.' >&2
  exit 1
fi
if ! docker compose --env-file .env.docker ps --status running --services | grep -qx 'backend'; then
  echo 'Backend container is not running.' >&2
  exit 1
fi
if ! docker compose --env-file .env.docker ps --status running --services | grep -qx 'frontend'; then
  echo 'Frontend container is not running.' >&2
  exit 1
fi
# The first-week backend virtualenv already exists and is suitable for running a local smoke-test client.
"$HOME/Documents/studysync/backend/.venv/bin/python" -m pip install 'websockets>=14,<17' -q
"$HOME/Documents/studysync/backend/.venv/bin/python" "$HOME/Documents/studysync/smoke_test.py"
