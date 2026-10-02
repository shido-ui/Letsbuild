#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
exec python -m uvicorn moduleiq.main:app --host 0.0.0.0 --port 8000 --reload
