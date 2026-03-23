import logging
import os
import shutil
from pathlib import Path

import httpx  # noqa: F401 — re-exported for modules that import from here
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Load Telegram bot credentials (optional — enables direct messaging)
_tg_env = Path.home() / ".claude" / "channels" / "telegram" / ".env"
if _tg_env.exists():
    load_dotenv(_tg_env)
_tg_access = Path.home() / ".claude" / "channels" / "telegram" / "access.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger("artemis.scheduler")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = ""
if _tg_access.exists():
    import json as _json
    try:
        _access = _json.loads(_tg_access.read_text())
        _allowed = _access.get("allowFrom", [])
        TELEGRAM_CHAT_ID = _allowed[0] if _allowed else ""
    except Exception:
        pass

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
TMUX_SESSION = "artemis"
TASK_LOG_DIR = "/tmp/artemis-tasks"
TMUX_BIN = os.environ.get("TMUX_BIN", shutil.which("tmux") or "/opt/homebrew/bin/tmux")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", shutil.which("claude") or "claude")
UV_BIN = os.environ.get("UV_BIN", shutil.which("uv") or "uv")

# Skills that require Claude.ai OAuth MCPs (Gmail, Calendar, etc.) — must run
# in interactive mode so the full MCP stack is available.
INTERACTIVE_SKILLS = frozenset({"inbox", "schedule", "draft", "inbox-linkedin", "linkedin"})


def _get_supabase():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured.")
    return create_client(url, key)
