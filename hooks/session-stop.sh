#!/bin/bash
# Session-end sync: auto-sync safe operations and clean up temp files.

# CLAUDE_PLUGIN_ROOT is set by Claude Code when running plugin hooks.
# Fall back to relative path for local development/testing.
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

# Push state changes to DB, then sync contacts pipeline
if command -v uv &>/dev/null; then
  cd "$PLUGIN_ROOT" && uv run python tools/state_sync.py --push 2>/dev/null
  cd "$PLUGIN_ROOT" && uv run python tools/sync_contacts.py 2>/dev/null
fi

# Clean up temp analysis files
find "$PLUGIN_ROOT/output" -name "analysis*.md" -type f -delete 2>/dev/null

exit 0
