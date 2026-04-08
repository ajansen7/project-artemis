#!/bin/bash
# Load hot state files at session start (or after compaction).
# Outputs content to stdout so Claude Code injects it into context.
#
# Used by both SessionStart and SessionStart (compact matcher) hooks.

# CLAUDE_PLUGIN_ROOT is set by Claude Code when running plugin hooks.
# Fall back to relative path for local development/testing.
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
STATE_DIR="$PLUGIN_ROOT/state"

# Fresh-install detection: if identity.md doesn't exist, this is a new setup.
if [ ! -f "$STATE_DIR/identity.md" ]; then
  cat <<'SETUP'
# ARTEMIS SETUP REQUIRED

No candidate profile found. This is a fresh installation.

Before doing anything else:
1. Greet the user and explain that Artemis needs a one-time setup.
2. Invoke the setup skill (`/artemis:setup`) immediately.
3. Do not wait for the user to ask. Surface this proactively.
SETUP
  exit 0
fi

# Load all state .md files (skip examples)
for f in "$STATE_DIR"/*.md; do
  [[ "$f" == *.example.md ]] && continue
  # Only load hot files (identity, voice, active_loops, lessons)
  basename="$(basename "$f")"
  case "$basename" in
    identity.md|voice.md|active_loops.md|lessons.md)
      [ -f "$f" ] && cat "$f"
      echo ""
      ;;
  esac
done
