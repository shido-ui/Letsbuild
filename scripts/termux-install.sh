#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
pkg update -y
pkg install -y python git sqlite nodejs-lts
python -m pip install --upgrade pip
python -m pip install -e ".[dev,document-engine]"
mkdir -p data/{uploads,processed,backups,models,logs,storage}
export PYTHONPATH="$ROOT/backend"
python -m alembic upgrade head
python scripts/seed.py
chmod +x scripts/start-local.sh scripts/termux-start.sh scripts/termux-stop.sh
echo "ModuleIQ installed. Start with ./scripts/termux-start.sh"
