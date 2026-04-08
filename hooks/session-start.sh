#!/bin/bash
# Load hot memory files at session start.
# Outputs content to stdout so Claude Code injects it into context.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOT_DIR="$SCRIPT_DIR/../memory/hot"

# Fresh-install detection: if identity.md doesn't exist yet, this is a new setup.
# Inject a clear directive so Claude surfaces the setup flow immediately.
if [ ! -f "$HOT_DIR/identity.md" ]; then
  echo "# ARTEMIS SETUP REQUIRED"
  echo ""
  echo "No candidate profile found. This is a fresh installation."
  echo ""
  echo "IMPORTANT INSTRUCTION FOR CLAUDE: Before doing anything else, you must:"
  echo "1. Greet the user and explain that Artemis needs a one-time setup to function."
  echo "2. Check whether the interview-coach submodule is initialized:"
  echo "   - Run: git -C \"$PROJECT_ROOT\" submodule status .claude/skills/interview-coach"
  echo "   - If the output starts with '-', the submodule has not been cloned."
  echo "   - If not cloned, ask the user for permission to clone it (it contains the interview coaching system)."
  echo "   - If they say yes, run: git -C \"$PROJECT_ROOT\" submodule update --init .claude/skills/interview-coach"
  echo "3. Ask the user whether they want to start with the interview-coach kickoff (recommended — it extracts"
  echo "   stories, builds a storybank, and does a deep background capture that Artemis can learn from),"
  echo "   or go straight into the Artemis setup wizard."
  echo "4. Either way, invoke the artemis-setup skill immediately."
  echo ""
  echo "Do not wait for the user to ask. Surface this proactively at the start of this message."
  exit 0
fi

# Check if interview-coach submodule is initialized (SKILL.md is a reliable marker).
IC_SKILL="$PROJECT_ROOT/.claude/skills/interview-coach/SKILL.md"
if [ ! -f "$IC_SKILL" ]; then
  echo "# INTERVIEW COACH NOT INITIALIZED"
  echo ""
  echo "NOTE FOR CLAUDE: The interview-coach submodule does not appear to be cloned."
  echo "At a natural moment (not urgently), mention this to the user and offer to clone it:"
  echo "  git -C \"$PROJECT_ROOT\" submodule update --init .claude/skills/interview-coach"
  echo "The interview coach handles storybank building, mock interviews, and prep — it complements Artemis."
  echo ""
fi

if [ -d "$HOT_DIR" ]; then
  for f in "$HOT_DIR"/*.md; do
    # Skip example files
    [[ "$f" == *.example.md ]] && continue
    [ -f "$f" ] && cat "$f"
    echo ""
  done
fi
