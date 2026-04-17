#!/usr/bin/env bash
# Artemis — stop all services and clean up.
#
# Usage:
#   ./scripts/stop.sh           # stop services, keep tmux session
#   ./scripts/stop.sh --kill    # kill the entire tmux session
#
# This script:
#   1. Kills the api, frontend, and orchestrator tmux windows
#   2. Kills any stray processes on the service ports (8000, 5173)
#   3. Optionally kills the entire tmux session (--kill)

set -euo pipefail

SESSION="artemis"
TMUX_BIN="${TMUX_BIN:-$(command -v tmux || echo /opt/homebrew/bin/tmux)}"
KILL_SESSION=false

for arg in "$@"; do
  case "$arg" in
    --kill) KILL_SESSION=true ;;
  esac
done

# ─── Helpers ──────────────────────────────────────────────────────

kill_window() {
  local name="$1"
  if "$TMUX_BIN" list-windows -t "$SESSION" -F '#{window_name}' 2>/dev/null | grep -qx "$name"; then
    "$TMUX_BIN" kill-window -t "$SESSION:$name" 2>/dev/null && echo "  [$name] stopped" || true
  fi
}

kill_port() {
  local port="$1"
  local pids
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill -TERM 2>/dev/null || true
    echo "  Killed process(es) on port $port"
  fi
}

# ─── Stop service windows ────────────────────────────────────────

if "$TMUX_BIN" has-session -t "$SESSION" 2>/dev/null; then
  echo "Stopping service windows..."
  kill_window "api"
  kill_window "frontend"
  kill_window "orchestrator"
else
  echo "No tmux session '$SESSION' found."
fi

# ─── Kill stray port bindings ────────────────────────────────────

echo "Checking for stray processes on service ports..."
kill_port 8000
kill_port 5173
kill_port 8790

# ─── Optionally kill the full session ─────────────────────────────

if [ "$KILL_SESSION" = true ]; then
  if "$TMUX_BIN" has-session -t "$SESSION" 2>/dev/null; then
    "$TMUX_BIN" kill-session -t "$SESSION"
    echo "Killed tmux session '$SESSION'."
  fi
else
  echo ""
  echo "Service windows stopped. The '$SESSION' tmux session is still alive."
  echo "To kill everything: ./scripts/stop.sh --kill"
fi

# ─── Nginx note ───────────────────────────────────────────────────

if pgrep -x nginx &>/dev/null; then
  echo ""
  echo "Note: nginx is still running (shared service, not stopped automatically)."
  echo "  To stop: sudo nginx -s stop"
fi
