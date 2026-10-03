#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
pkill -f "uvicorn moduleiq.main:app" 2>/dev/null || true
pkill -f "huey_consumer moduleiq.workers.ingestion.huey" 2>/dev/null || true
echo "ModuleIQ backend and worker stopped."
