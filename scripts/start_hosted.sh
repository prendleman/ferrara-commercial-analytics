#!/usr/bin/env bash
# Always-on entrypoint: demo server, plus a Cloudflare tunnel when TUNNEL_TOKEN is set.
set -euo pipefail
cd "$(dirname "$0")/.."

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8772}"

python3 -m app.server --host "$HOST" --port "$PORT" &
APP_PID=$!

cleanup() {
  kill "$APP_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 40); do
  if curl -sf "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if [[ -z "${TUNNEL_TOKEN:-}" ]]; then
  echo "TUNNEL_TOKEN not set — serving only on ${HOST}:${PORT}." >&2
  wait "$APP_PID"
  exit $?
fi

echo "Starting Cloudflare Tunnel for ferrara.datasharkbi.com…"
exec cloudflared tunnel --no-autoupdate --url "http://127.0.0.1:${PORT}" run --token "$TUNNEL_TOKEN"
