#!/usr/bin/env bash
# Artemis — start all services in a single tmux session.
#
# Usage:
#   ./scripts/start.sh                      # start everything
#   ./scripts/start.sh --no-frontend        # skip the React frontend
#   ./scripts/start.sh --no-orchestrator    # skip orchestrator (use with Claude Desktop)
#   ./scripts/start.sh --non-interactive    # fail if not authenticated (for CI/automation)
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
NON_INTERACTIVE=false

for arg in "$@"; do
  case "$arg" in
    --no-frontend) SKIP_FRONTEND=true ;;
    --no-orchestrator) SKIP_ORCHESTRATOR=true ;;
    --non-interactive) NON_INTERACTIVE=true ;;
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

# ─── Auth check ──────────────────────────────────────────────────

AUTH_STATUS=$(cd "$PROJECT_ROOT" && uv run python tools/auth.py whoami 2>/dev/null)
if echo "$AUTH_STATUS" | grep -q "^User:"; then
  USER_EMAIL=$(echo "$AUTH_STATUS" | grep "^User:" | cut -d' ' -f2-)
  echo "Authenticated as: $USER_EMAIL"
else
  if [ "$NON_INTERACTIVE" = true ]; then
    echo "ERROR: Not authenticated. Run: artemis-login login" >&2
    exit 1
  fi
  echo "Not signed in. Starting login..."
  (cd "$PROJECT_ROOT" && uv run python tools/auth.py login)
  AUTH_STATUS=$(cd "$PROJECT_ROOT" && uv run python tools/auth.py whoami 2>/dev/null)
  if ! echo "$AUTH_STATUS" | grep -q "^User:"; then
    echo "ERROR: Login failed or was cancelled." >&2
    exit 1
  fi
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
# --dangerously-skip-permissions and --dangerously-load-development-channels
# both show prompts that require Enter. We send Enter at 3s, 6s, 9s intervals
# to auto-accept both prompts in whatever order they appear.
if [ "$SKIP_ORCHESTRATOR" = false ]; then
  if ! window_exists "orchestrator"; then
    "$TMUX_BIN" new-window -t "$SESSION" -n "orchestrator" -d
    "$TMUX_BIN" send-keys -t "$SESSION:orchestrator" "cd $PROJECT_ROOT && claude --dangerously-skip-permissions --plugin-dir $PROJECT_ROOT --channels plugin:telegram@claude-plugins-official --dangerously-load-development-channels plugin:artemis@inline" Enter
    # Auto-accept both --dangerously-* prompts (send Enter at 3s, 6s, 9s)
    for i in 1 2 3; do
      sleep 3
      "$TMUX_BIN" send-keys -t "$SESSION:orchestrator" "" Enter 2>/dev/null || true
    done
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
