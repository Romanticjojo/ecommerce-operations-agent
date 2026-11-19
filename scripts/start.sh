#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
if [[ ! -x .venv/bin/python ]]; then
  if ! command -v "$PYTHON_BIN" >/dev/null; then
    echo "Install Python 3.11 or set PYTHON_BIN to its path." >&2
    exit 1
  fi
  "$PYTHON_BIN" -m venv .venv
fi
if ! cmp -s requirements.lock .venv/commerce-requirements.lock; then
  .venv/bin/python -m pip install -r requirements.txt
  cp requirements.lock .venv/commerce-requirements.lock
fi
if [[ ! -d frontend/dist || ! -f frontend/dist/index.html || ! -f frontend/dist/.source-hash ]] || [[ "$(cat frontend/dist/.source-hash)" != "$(.venv/bin/python scripts/frontend_hash.py)" ]]; then
  (cd frontend && npm ci --no-audit --no-fund && npm run build)
  .venv/bin/python scripts/frontend_hash.py > frontend/dist/.source-hash
fi
if ! .venv/bin/python -c 'from commerce.settings import database; raise SystemExit(not database().is_file())'; then
  .venv/bin/python -m commerce.cli demo
fi
exec .venv/bin/python -m uvicorn commerce.api:app --host 127.0.0.1 --port "${PORT:-8731}"
