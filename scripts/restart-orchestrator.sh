#!/usr/bin/env bash
# Restart the orchestrator tmux window to apply new auth credentials.
# Called by auth.py after login/logout/signup.
#
# Usage: ./scripts/restart-orchestrator.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="artemis"
TMUX_BIN="${TMUX_BIN:-$(command -v tmux || echo /opt/homebrew/bin/tmux)}"

# Check if tmux session exists
if ! "$TMUX_BIN" has-session -t "$SESSION" 2>/dev/null; then
  exit 0  # Session not running — nothing to restart
fi

# Check if orchestrator window exists and kill it
if "$TMUX_BIN" list-windows -t "$SESSION" -F '#{window_name}' 2>/dev/null | grep -qx "orchestrator"; then
  "$TMUX_BIN" kill-window -t "$SESSION:orchestrator"
fi

# Create new orchestrator window and launch Claude Code
"$TMUX_BIN" new-window -t "$SESSION" -n "orchestrator" -d
"$TMUX_BIN" send-keys -t "$SESSION:orchestrator" \
  "cd $PROJECT_ROOT && claude --dangerously-skip-permissions --plugin-dir $PROJECT_ROOT --channels plugin:telegram@claude-plugins-official --dangerously-load-development-channels plugin:artemis@inline" Enter

# Auto-accept both --dangerously-* prompts (send Enter at 3s, 6s, 9s)
for i in 1 2 3; do
  sleep 3
  "$TMUX_BIN" send-keys -t "$SESSION:orchestrator" "" Enter 2>/dev/null || true
done
