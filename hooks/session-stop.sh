#!/bin/bash
# Session-end sync: auto-sync safe operations and clean up temp files.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Run comprehensive auto-sync (contacts pipeline, manifest update)
if command -v uv &>/dev/null; then
  cd "$PROJECT_ROOT" && uv run python .claude/tools/sync_state.py --auto 2>/dev/null
fi

# Clean up temp analysis files
find "$PROJECT_ROOT/output" -name "analysis*.md" -type f -delete 2>/dev/null

echo "Session sync complete."
