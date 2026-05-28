#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "${API_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${DASHBOARD_PID:-}" ]]; then
    kill "${DASHBOARD_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

cd "${ROOT_DIR}"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

cd "${ROOT_DIR}/dashboard"
npm run dev -- --host 0.0.0.0 &
DASHBOARD_PID=$!

wait
