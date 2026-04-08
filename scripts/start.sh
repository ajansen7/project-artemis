#!/usr/bin/env bash
# Artemis — start all services in a single tmux session.
#
# Usage:
#   ./scripts/start.sh                   # start everything
#   ./scripts/start.sh --no-frontend     # skip the React frontend
#   ./scripts/start.sh --no-orchestrator # skip orchestrator (use with Claude Desktop)
#
# Services started (each in its own tmux window):
#   api           — FastAPI backend (uvicorn, port 8000)
#   frontend      — React dashboard (vite, port 5173)  [optional]
#   orchestrator  — Long-running Claude session: Telegram interface + task executor [optional]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="artemis"
TMUX_BIN="${TMUX_BIN:-$(command -v tmux || echo /opt/homebrew/bin/tmux)}"
SKIP_FRONTEND=false
SKIP_ORCHESTRATOR=false

for arg in "$@"; do
  case "$arg" in
    --no-frontend) SKIP_FRONTEND=true ;;
    --no-orchestrator) SKIP_ORCHESTRATOR=true ;;
  esac
done

# ─── Preflight checks ────────────────────────────────────────────

if ! command -v "$TMUX_BIN" &>/dev/null; then
  echo "ERROR: tmux not found. Install with: brew install tmux" >&2
  exit 1
fi

if ! command -v uv &>/dev/null; then
  echo "ERROR: uv not found. Install from https://docs.astral.sh/uv/" >&2
  exit 1
fi

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  echo "WARNING: .env not found in $PROJECT_ROOT — Supabase may not connect." >&2
fi

# ─── Helpers ──────────────────────────────────────────────────────

session_exists() {
  "$TMUX_BIN" has-session -t "$SESSION" 2>/dev/null
}

window_exists() {
  "$TMUX_BIN" list-windows -t "$SESSION" -F '#{window_name}' 2>/dev/null | grep -qx "$1"
}

# Start a named window if it doesn't already exist.
# Usage: start_window <name> <command>
start_window() {
  local name="$1"
  local cmd="$2"

  if window_exists "$name"; then
    echo "  [$name] already running — skipped"
    return
  fi

  "$TMUX_BIN" new-window -t "$SESSION" -n "$name" -d
  "$TMUX_BIN" send-keys -t "$SESSION:$name" "cd $PROJECT_ROOT && $cmd" Enter
  echo "  [$name] started"
}

# ─── Create tmux session ─────────────────────────────────────────

if session_exists; then
  echo "tmux session '$SESSION' already exists — reusing it."
else
  "$TMUX_BIN" new-session -d -s "$SESSION" -x 220 -y 50
  # Rename the default window so it's not left empty
  "$TMUX_BIN" rename-window -t "$SESSION:0" "home"
  echo "Created tmux session '$SESSION'."
fi

# ─── Start services ──────────────────────────────────────────────

echo "Starting services..."

start_window "api" "uv run uvicorn api.server:app --reload --host 0.0.0.0 --port 8000"

if [ "$SKIP_FRONTEND" = false ]; then
  start_window "frontend" "cd frontend && npm run dev -- --host 0.0.0.0"
fi

# The orchestrator is the unified Telegram interface + task executor.
# The artemis-channel MCP (loaded via --plugin-dir) pushes task events in
# directly from the API — no polling loop needed.
#
# --dangerously-load-development-channels requires a one-time interactive confirmation.
# We send Enter after a brief delay to auto-accept (option 1: "local development").
if [ "$SKIP_ORCHESTRATOR" = false ]; then
  if ! window_exists "orchestrator"; then
    "$TMUX_BIN" new-window -t "$SESSION" -n "orchestrator" -d
    "$TMUX_BIN" send-keys -t "$SESSION:orchestrator" "cd $PROJECT_ROOT && claude --dangerously-skip-permissions --plugin-dir $PROJECT_ROOT --channels plugin:telegram@claude-plugins-official --dangerously-load-development-channels plugin:artemis@inline" Enter
    # Auto-confirm the "local development" prompt that --dangerously-load-development-channels shows
    sleep 3
    "$TMUX_BIN" send-keys -t "$SESSION:orchestrator" "" Enter
    echo "  [orchestrator] started"
  else
    echo "  [orchestrator] already running — skipped"
  fi
fi

# ─── Summary ─────────────────────────────────────────────────────

LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ip route get 1 2>/dev/null | awk '{print $7; exit}' || echo "")

echo ""
echo "Artemis is running:"
echo "  API:          http://localhost:8000"
[ "$SKIP_FRONTEND" = false ] && echo "  Dashboard:    http://localhost:5173"
if [ -n "$LOCAL_IP" ]; then
  echo ""
  echo "On your local network:"
  echo "  API:          http://$LOCAL_IP:8000"
  [ "$SKIP_FRONTEND" = false ] && echo "  Dashboard:    http://$LOCAL_IP:5173"
fi
[ "$SKIP_ORCHESTRATOR" = false ] && echo "" && echo "  Orchestrator: tmux window 'orchestrator' (Telegram + task queue)"
echo ""
echo "Attach to tmux:  tmux attach -t $SESSION"
echo "Stop everything: ./scripts/stop.sh"
