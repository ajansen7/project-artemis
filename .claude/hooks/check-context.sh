#!/bin/bash
# Check if candidate_context.md is stale relative to coaching_state.md.
# Prints a warning if context needs refreshing.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CONTEXT="$PROJECT_ROOT/.claude/skills/hunt/references/candidate_context.md"
COACHING="$PROJECT_ROOT/.claude/skills/interview-coach/coaching_state.md"

# Skip if context file doesn't exist yet
if [ ! -f "$CONTEXT" ]; then
  echo "WARNING: candidate_context.md does not exist. Run /context to build it."
  exit 0
fi

# Skip if coaching state doesn't exist
[ ! -f "$COACHING" ] && exit 0

# Compare modification times
if [ "$COACHING" -nt "$CONTEXT" ]; then
  echo "WARNING: candidate_context.md is stale (coaching_state.md was updated more recently). Consider running /context to refresh."
fi
