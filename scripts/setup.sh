#!/usr/bin/env bash
# Artemis — interactive setup for new users.
#
# Usage:
#   ./scripts/setup.sh
#
# This script checks prerequisites, installs dependencies, configures
# environment variables, and prepares the project for first use.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ─── Colors ─────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${BLUE}→${NC} $1"; }

# ─── Prerequisite checks ───────────────────────────────────────

echo ""
echo "Artemis Setup"
echo "============="
echo ""
echo "Checking prerequisites..."
echo ""

MISSING=0

# Python 3.11+ — try versioned binaries first so system python3 (often 3.9 on macOS)
# doesn't shadow a newer install managed by Homebrew, uv, or mise.
PYTHON_BIN=""
for _py in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$_py" &>/dev/null; then
    _ver=$("$_py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null) || continue
    _major=$(echo "$_ver" | cut -d. -f1)
    _minor=$(echo "$_ver" | cut -d. -f2)
    if [ "$_major" -ge 3 ] && [ "$_minor" -ge 11 ]; then
      PYTHON_BIN="$_py"
      PY_VERSION="$_ver"
      break
    fi
  fi
done

if [ -n "$PYTHON_BIN" ]; then
  ok "Python $PY_VERSION ($PYTHON_BIN)"
else
  _sys_ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "not found")
  fail "Python 3.11+ not found (system python3 is $_sys_ver)"
  MISSING=1
fi

# uv
if command -v uv &>/dev/null; then
  ok "uv $(uv --version 2>/dev/null | head -1)"
else
  fail "uv not found — install from https://docs.astral.sh/uv/"
  MISSING=1
fi

# Node.js
if command -v node &>/dev/null; then
  ok "Node.js $(node --version)"
else
  fail "Node.js not found (needed for the dashboard)"
  MISSING=1
fi

# Bun
if command -v bun &>/dev/null; then
  ok "Bun $(bun --version 2>/dev/null)"
else
  fail "Bun not found — install from https://bun.sh"
  MISSING=1
fi

# tmux
if command -v tmux &>/dev/null; then
  ok "tmux $(tmux -V 2>/dev/null)"
else
  fail "tmux not found — brew install tmux"
  MISSING=1
fi

# Claude Code
if command -v claude &>/dev/null; then
  ok "Claude Code installed"
else
  fail "Claude Code not found — npm install -g @anthropic-ai/claude-code"
  MISSING=1
fi

# nginx (optional)
if command -v nginx &>/dev/null; then
  ok "nginx (optional, for HTTPS remote access)"
else
  warn "nginx not found (optional) — brew install nginx"
  warn "  Enables HTTPS remote access. Run ./scripts/setup-nginx.sh after installing."
fi

# LibreOffice (optional)
if command -v soffice &>/dev/null; then
  ok "LibreOffice (optional, for PDF generation)"
else
  warn "LibreOffice not found (optional) — brew install --cask libreoffice"
fi

echo ""

if [ "$MISSING" -ne 0 ]; then
  echo -e "${RED}Some prerequisites are missing. Install them and re-run this script.${NC}"
  exit 1
fi

# ─── State directory setup ─────────────────────────────────────

echo "Setting up state directory..."
if [ -d "$PROJECT_ROOT/state/examples" ]; then
  for example in "$PROJECT_ROOT/state/examples"/*.example.md; do
    target="$PROJECT_ROOT/state/$(basename "$example" .example.md).md"
    if [ ! -f "$target" ]; then
      cp "$example" "$target"
      ok "Created $(basename "$target") from template"
    fi
  done
fi

# Check for old-structure files and offer migration
if [ -d "$PROJECT_ROOT/.claude/memory/hot" ] || [ -d "$PROJECT_ROOT/.claude/skills/hunt/references" ]; then
  echo ""
  warn "Detected files in old directory structure (.claude/)"
  info "Run migration: uv run python tools/migrate_state.py --dry-run"
  info "Then apply:    uv run python tools/migrate_state.py"
fi
echo ""

# ─── Python dependencies ───────────────────────────────────────

echo "Installing Python dependencies..."
cd "$PROJECT_ROOT" && uv sync
ok "Python dependencies installed"
echo ""

# ─── Frontend dependencies ──────────────────────────────────────

echo "Installing frontend dependencies..."
cd "$PROJECT_ROOT/frontend" && npm install --silent
ok "Frontend dependencies installed"
echo ""

# ─── Channels dependencies ──────────────────────────────────────

echo "Installing channel dependencies..."
cd "$PROJECT_ROOT/channels/artemis-channel" && bun install --silent 2>/dev/null
ok "Channel dependencies installed"
echo ""

# ─── Environment file ──────────────────────────────────────────

cd "$PROJECT_ROOT"
echo "Configuring environment..."

if [ -f "$PROJECT_ROOT/.env" ]; then
  ok ".env already exists"
else
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo ""
  echo "  A .env file has been created from .env.example."
  echo "  You need to fill in your Supabase credentials."
  echo ""
  echo "  Required values:"
  echo "    SUPABASE_URL=https://your-project.supabase.co"
  echo "    SUPABASE_ANON_KEY=your-anon-key"
  echo "    SUPABASE_SERVICE_ROLE_KEY=your-service-role-key"
  echo ""
  read -p "  Would you like to enter them now? [Y/n] " ENTER_ENV
  ENTER_ENV=${ENTER_ENV:-Y}

  if [[ "$ENTER_ENV" =~ ^[Yy] ]]; then
    echo ""
    read -p "  SUPABASE_URL: " SB_URL
    read -p "  SUPABASE_ANON_KEY: " SB_ANON
    read -p "  SUPABASE_SERVICE_ROLE_KEY: " SB_SERVICE

    if [ -n "$SB_URL" ]; then
      sed -i.bak "s|SUPABASE_URL=.*|SUPABASE_URL=$SB_URL|" "$PROJECT_ROOT/.env"
    fi
    if [ -n "$SB_ANON" ]; then
      sed -i.bak "s|SUPABASE_ANON_KEY=.*|SUPABASE_ANON_KEY=$SB_ANON|" "$PROJECT_ROOT/.env"
    fi
    if [ -n "$SB_SERVICE" ]; then
      sed -i.bak "s|SUPABASE_SERVICE_ROLE_KEY=.*|SUPABASE_SERVICE_ROLE_KEY=$SB_SERVICE|" "$PROJECT_ROOT/.env"
    fi
    rm -f "$PROJECT_ROOT/.env.bak"
    ok "Credentials saved to .env"
  else
    warn "Skipped — edit .env manually before starting services"
  fi
fi
echo ""

# ─── Local config template ─────────────────────────────────────

if [ ! -f "$PROJECT_ROOT/CLAUDE.local.md" ]; then
  if [ -f "$PROJECT_ROOT/CLAUDE.local.example.md" ]; then
    cp "$PROJECT_ROOT/CLAUDE.local.example.md" "$PROJECT_ROOT/CLAUDE.local.md"
    ok "Created CLAUDE.local.md from template (gitignored)"
  fi
else
  ok "CLAUDE.local.md already exists"
fi
echo ""

# ─── Supabase connection test ──────────────────────────────────

echo "Verifying Supabase connection..."
if uv run python tools/db.py status 2>/dev/null; then
  ok "Supabase connected"
else
  warn "Could not verify Supabase connection — check .env credentials"
  warn "You can verify later with: artemis-db status"
fi
echo ""

# ─── Summary ───────────────────────────────────────────────────

echo "============="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Open Claude Code with the Artemis plugin:"
echo "     cd $PROJECT_ROOT && claude --plugin-dir ."
echo "     (The session hook will detect a fresh install and prompt you)"
echo ""
echo "  2. Start all services:"
echo "     ./scripts/start.sh"
echo ""
echo "  3. Open the dashboard:"
echo "     http://localhost:5173"
echo ""
echo "  4. Sign in — the first user is automatically granted admin access."
echo "     Subsequent users will need admin approval via the Users tab."
echo ""
if command -v nginx &>/dev/null; then
  echo "  5. Enable HTTPS remote access (optional):"
  echo "     ./scripts/setup-nginx.sh"
  echo "     Then access via https://localhost or https://<your-ip>"
  echo ""
fi
echo "  For Claude Desktop: start services with --no-orchestrator flag,"
echo "  then add the plugin directory in Claude Desktop settings."
