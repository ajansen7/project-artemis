#!/bin/bash
# Load hot memory files at session start.
# Outputs content to stdout so Claude Code injects it into context.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOT_DIR="$SCRIPT_DIR/../memory/hot"

if [ -d "$HOT_DIR" ]; then
  for f in "$HOT_DIR"/*.md; do
    [ -f "$f" ] && cat "$f"
    echo ""
  done
fi
