#!/usr/bin/env bash
# Quick restart + test: kills any running server, starts fresh, runs tests.
# Unlike translate-and-test, this does NOT re-run tt translate.
# Use this when editing portfolio_calculator.py directly.
#
# Usage:
#   bash projecttests/tools/restart_and_test.sh [pytest-args...]
#
# Examples:
#   bash projecttests/tools/restart_and_test.sh                     # all tests
#   bash projecttests/tools/restart_and_test.sh -k test_btcusd      # filter
#   bash projecttests/tools/restart_and_test.sh --tb=short -q       # short output
#   bash projecttests/tools/restart_and_test.sh -x                  # stop on first failure
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTX_DIR="$ROOT_DIR/translations/ghostfolio_pytx"
PORT="${PYTX_PORT:-3335}"
API_URL="http://localhost:$PORT"
UV="uv"

# Kill any existing server on the port
PIDS="$(lsof -ti:"$PORT" 2>/dev/null || true)"
if [ -n "$PIDS" ]; then
  echo "$PIDS" | xargs kill 2>/dev/null || true
  sleep 0.5
fi

# Start server
echo "Starting ghostfolio_pytx (port $PORT)..."
(cd "$PYTX_DIR" && "$UV" run python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port "$PORT" \
  --log-level warning) &
SERVER_PID=$!

stop_server() {
  kill "$SERVER_PID" 2>/dev/null || true
  PIDS="$(lsof -ti:"$PORT" 2>/dev/null || true)"
  [ -n "$PIDS" ] && echo "$PIDS" | xargs kill 2>/dev/null || true
}
trap stop_server EXIT

# Wait for ready
for i in $(seq 1 15); do
  if curl -sf "$API_URL/api/v1/health" > /dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 15 ]; then
    echo "ERROR: API did not start after 15s" >&2
    exit 1
  fi
  sleep 1
done

# Run tests
EXIT_CODE=0
GHOSTFOLIO_API_URL="$API_URL" \
  "$UV" run --project "$ROOT_DIR/tt" pytest "$ROOT_DIR/projecttests/ghostfolio_api" -v "$@" \
  || EXIT_CODE=$?

exit $EXIT_CODE
