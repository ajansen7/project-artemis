#!/usr/bin/env bash
# Artemis — start all services in a single tmux session.
#
# Usage:
#   ./scripts/start.sh          # start everything
#   ./scripts/start.sh --no-frontend   # skip the React frontend
#
# Services started (each in its own tmux window):
#   api       — FastAPI backend (uvicorn, port 8000)
#   frontend  — React dashboard (vite, port 5173)
#   telegram  — Long-running Claude session for Telegram interaction
#
# The "artemis" tmux session is also used by the scheduler to spawn
# skill-run windows, so this script avoids recreating it if it exists.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="artemis"
TMUX_BIN="${TMUX_BIN:-$(command -v tmux || echo /opt/homebrew/bin/tmux)}"
SKIP_FRONTEND=false

for arg in "$@"; do
  case "$arg" in
    --no-frontend) SKIP_FRONTEND=true ;;
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
  start_window "frontend" "cd frontend && npm run dev"
fi

# The handler runs from channels/ so it picks up the Telegram plugin from
# channels/.claude/settings.json without competing with the main session.
# --add-dir gives it access to the main project's tools and skills.
start_window "telegram" "cd channels && claude --add-dir $PROJECT_ROOT --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official --append-system-prompt-file $PROJECT_ROOT/.claude/agents/telegram-handler.md"

# ─── Summary ─────────────────────────────────────────────────────

echo ""
echo "Artemis is running:"
echo "  API:       http://localhost:8000"
[ "$SKIP_FRONTEND" = false ] && echo "  Dashboard: http://localhost:5173"
echo "  Telegram:  handler session (plugin)"
echo ""
echo "Attach to tmux:  tmux attach -t $SESSION"
echo "Stop everything: ./scripts/stop.sh"
