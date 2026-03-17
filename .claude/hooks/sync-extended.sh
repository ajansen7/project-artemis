#!/bin/bash
# Session-end sync: refresh contact pipeline and clean up temp files.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Sync contacts DB -> output/contacts_pipeline.md
if command -v uv &>/dev/null; then
  cd "$PROJECT_ROOT" && uv run python .claude/tools/sync_contacts.py 2>/dev/null
fi

# Clean up temp analysis files
find "$PROJECT_ROOT/output" -name "analysis*.md" -type f -delete 2>/dev/null

echo "Session sync complete."
