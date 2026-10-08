#!/usr/bin/env bash
# Local server launcher
set -euo pipefail

source .venv/bin/activate 2>/dev/null || true

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "Starting Real-Time Content Moderation Engine on http://${HOST}:${PORT}..."
exec uvicorn app.main:app --host "${HOST}" --port "${PORT}" --reload
