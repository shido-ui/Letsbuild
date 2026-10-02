#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/backend"

if ! python -c 'import moduleiq, huey' >/dev/null 2>&1; then
  echo "ModuleIQ backend dependencies are missing. Run: pip install -e '.[dev,document-engine]'"
  exit 1
fi

mkdir -p data/logs
cleanup() {
  kill "${WORKER_PID:-}" "${API_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

python -m uvicorn moduleiq.main:app --host 0.0.0.0 --port 8000 >data/logs/api.log 2>&1 &
API_PID=$!

huey_consumer moduleiq.workers.ingestion.huey --workers 1 --worker-type thread >data/logs/worker.log 2>&1 &
WORKER_PID=$!

echo "ModuleIQ backend: http://127.0.0.1:8000"
echo "API log:    data/logs/api.log"
echo "Worker log: data/logs/worker.log"
echo "Press Ctrl+C to stop FastAPI and Huey."
wait -n "$API_PID" "$WORKER_PID"
