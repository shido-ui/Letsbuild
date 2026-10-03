#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/backend"
mkdir -p data
python -m alembic upgrade head
(cd backend && python -m uvicorn moduleiq.main:app --reload --host 127.0.0.1 --port 8000) &
API_PID=$!
(cd frontend && npm install && npm run dev -- --host 127.0.0.1) &
WEB_PID=$!
trap 'kill "$WEB_PID" "$API_PID" 2>/dev/null || true' EXIT INT TERM
wait
