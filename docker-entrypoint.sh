#!/bin/bash
set -euo pipefail

if [[ "${RUN_GETDATA:-false}" == "true" ]]; then
  echo "[entrypoint] Running getdata.sh to fetch dataset..."
  if ! command -v unzip >/dev/null 2>&1; then
    echo "[entrypoint] unzip not found; cannot extract archive.zip" >&2
  fi
  chmod +x /app/backend/getdata.sh || true
  if ! /app/backend/getdata.sh; then
    echo "[entrypoint] getdata.sh failed; continuing startup" >&2
  fi
else
  echo "[entrypoint] Skipping getdata.sh (set RUN_GETDATA=true to enable)"
fi

exec conda run -n slop python /app/backend/server.py


