#!/usr/bin/env python3
"""
Push to Telegram — send formatted messages to the user via Telegram Bot API.

Called by scheduled Claude subprocesses to send curated, mobile-formatted
output directly to the user's phone. No proxy or webhook chain required.

Usage:
    uv run python .claude/tools/push_to_telegram.py send --text "Hello from Artemis"
    uv run python .claude/tools/push_to_telegram.py summary --job-name "Morning Scout" --status success --body "Found 3 roles"
    uv run python .claude/tools/push_to_telegram.py question --job-name "Morning Scout" --token abc123 --question "Save all 8 jobs?"
    echo "long message..." | uv run python .claude/tools/push_to_telegram.py send --stdin

Exit codes:
    0 — message sent (prints message_id to stdout)
    1 — send failed
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# ─── Credential loading ────────────────────────────────────────────

_tg_env = Path.home() / ".claude" / "channels" / "telegram" / ".env"
if _tg_env.exists():
    load_dotenv(_tg_env)

_tg_access = Path.home() / ".claude" / "channels" / "telegram" / "access.json"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = ""
if _tg_access.exists():
    try:
        _access = json.loads(_tg_access.read_text())
        _allowed = _access.get("allowFrom", [])
        CHAT_ID = str(_allowed[0]) if _allowed else ""
    except Exception:
        pass

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
MAX_LEN = 4096


# ─── Helpers ────────────────────────────────────────────────────────

def _send(text: str, parse_mode: str | None = None) -> int:
    """Send a message via Telegram Bot API. Returns message_id or raises."""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    if not CHAT_ID:
        print("ERROR: No chat_id found in access.json", file=sys.stderr)
        sys.exit(1)

    # Enforce Telegram's message length limit
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 20] + "\n\n(truncated)"

    payload: dict = {"chat_id": CHAT_ID, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    last_exc: Exception | None = None
    for attempt in range(3):
        if attempt:
            time.sleep(2 ** attempt)  # 2s, 4s
        try:
            resp = httpx.post(API_URL, json=payload, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Telegram API error: {data}")
            return data["result"]["message_id"]
        except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError) as exc:
            last_exc = exc
            print(f"WARNING: Telegram send attempt {attempt + 1} failed ({type(exc).__name__}), retrying…", file=sys.stderr)
    raise last_exc  # type: ignore[misc]


def _read_stdin_or_arg(args) -> str:
    """Read message body from --stdin flag (stdin) or --body/--text arg."""
    if getattr(args, "stdin", False):
        return sys.stdin.read().strip()
    for attr in ("body", "text"):
        val = getattr(args, attr, None)
        if val:
            return val
    return ""


# ─── Subcommands ────────────────────────────────────────────────────

def cmd_send(args):
    """Send a generic text message."""
    text = _read_stdin_or_arg(args)
    if not text:
        print("ERROR: No message text provided", file=sys.stderr)
        sys.exit(1)
    msg_id = _send(text, parse_mode=args.parse_mode)
    print(msg_id)


def cmd_summary(args):
    """Send a formatted job completion summary."""
    body = _read_stdin_or_arg(args)
    status = (args.status or "done").lower()
    icon = {"success": "\u2705", "failed": "\u274c", "done": "\u2705"}.get(status, "\u2139\ufe0f")

    job_name = args.job_name or "Job"
    text = f"{icon} {job_name}\n\n{body}" if body else f"{icon} {job_name} completed."

    msg_id = _send(text)
    print(msg_id)


def cmd_question(args):
    """Send a relay question formatted for mobile reply."""
    job_name = args.job_name or "Job"
    question = args.question
    if not question:
        print("ERROR: --question is required", file=sys.stderr)
        sys.exit(1)

    text = f"\u2753 {job_name} needs your input:\n\n{question}\n\nReply here and I'll relay your answer back."

    msg_id = _send(text)
    print(msg_id)


# ─── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Send formatted messages to Telegram",
        prog="push_to_telegram.py",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # send
    p_send = sub.add_parser("send", help="Send a generic message")
    p_send.add_argument("--text", help="Message text")
    p_send.add_argument("--stdin", action="store_true", help="Read message from stdin")
    p_send.add_argument("--parse-mode", choices=["MarkdownV2", "HTML"], default=None, help="Telegram parse mode")
    p_send.set_defaults(func=cmd_send)

    # summary
    p_summary = sub.add_parser("summary", help="Send a job completion summary")
    p_summary.add_argument("--job-name", required=True, help="Name of the job")
    p_summary.add_argument("--status", default="success", help="success, failed, or done")
    p_summary.add_argument("--body", help="Summary body text")
    p_summary.add_argument("--stdin", action="store_true", help="Read body from stdin")
    p_summary.set_defaults(func=cmd_summary)

    # question
    p_question = sub.add_parser("question", help="Send a relay question")
    p_question.add_argument("--job-name", required=True, help="Name of the job")
    p_question.add_argument("--token", help="Relay token (for reference)")
    p_question.add_argument("--question", required=True, help="Question for the user")
    p_question.set_defaults(func=cmd_question)

    args = parser.parse_args()
    try:
        args.func(args)
    except httpx.HTTPStatusError as exc:
        print(f"ERROR: Telegram API returned {exc.response.status_code}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
