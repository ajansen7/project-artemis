#!/bin/bash
# Bidirectional sync checker — runs sync_state.py to detect stale data across skills.
# Replaces the previous single-direction coaching_state → candidate_context check.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use sync_state.py for comprehensive checking
if command -v uv &>/dev/null; then
  cd "$PROJECT_ROOT" && uv run python .claude/tools/sync_state.py --check 2>/dev/null
fi
