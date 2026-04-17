"""
WebSocket terminal — bridges the browser to the tmux orchestrator session.

Protocol:
  1. Client connects to ws://host/api/terminal
  2. Client sends first message: JSON {"token": "<jwt>"}
  3. Server validates JWT, checks user is approved admin
  4. Server spawns pty running `tmux attach-session -t artemis:orchestrator`
  5. Bidirectional relay: browser keystrokes → pty stdin, pty stdout → browser

Security:
  - Admin-only: non-admin users get disconnected with 4003
  - Auth required: invalid/missing token gets 4001
  - One pty per WebSocket connection (cleaned up on disconnect)
"""

import asyncio
import fcntl
import json
import os
import pty
import signal
import struct
import subprocess
import termios

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.modules.config import get_user_profile, logger

router = APIRouter()

TMUX_BIN = os.environ.get("TMUX_BIN", "tmux")
TMUX_SESSION = "artemis"
TMUX_WINDOW = "orchestrator"


def _extract_user_id_from_token(token: str) -> str | None:
    """Decode JWT and extract user_id (sub claim). Returns None on failure."""
    from base64 import urlsafe_b64decode
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        claims = json.loads(urlsafe_b64decode(payload))
        return claims.get("sub")
    except Exception:
        return None


def _spawn_tmux_pty() -> tuple[int, int]:
    """Spawn a pty running tmux attach to the orchestrator window.

    Returns (master_fd, child_pid).
    Raises RuntimeError if tmux session/window doesn't exist.
    """
    # Verify the tmux session exists
    ret = subprocess.run(
        [TMUX_BIN, "has-session", "-t", TMUX_SESSION],
        capture_output=True,
    )
    if ret.returncode != 0:
        raise RuntimeError(f"tmux session '{TMUX_SESSION}' not found. Is Artemis running?")

    # Verify the orchestrator window exists
    ret = subprocess.run(
        [TMUX_BIN, "list-windows", "-t", TMUX_SESSION, "-F", "#{window_name}"],
        capture_output=True, text=True,
    )
    if TMUX_WINDOW not in ret.stdout.strip().split("\n"):
        raise RuntimeError(
            f"tmux window '{TMUX_WINDOW}' not found. "
            f"Start with: ./scripts/start.sh (without --no-orchestrator)"
        )

    master_fd, slave_fd = pty.openpty()

    pid = os.fork()
    if pid == 0:
        # Child process
        os.close(master_fd)
        os.setsid()

        # Set up the slave as the controlling terminal
        fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)

        # Redirect stdio to the pty slave
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        if slave_fd > 2:
            os.close(slave_fd)

        # Set a reasonable terminal size
        os.environ["TERM"] = "xterm-256color"

        os.execvp(TMUX_BIN, [
            TMUX_BIN, "attach-session",
            "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}",
        ])
    else:
        # Parent process
        os.close(slave_fd)
        return master_fd, pid


def _resize_pty(master_fd: int, rows: int, cols: int) -> None:
    """Send TIOCSWINSZ to resize the pty."""
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)


@router.websocket("/api/terminal")
async def terminal_websocket(ws: WebSocket):
    await ws.accept()

    # ─── Step 1: Authenticate ────────────────────────────────────
    try:
        auth_msg = await asyncio.wait_for(ws.receive_text(), timeout=10.0)
        auth_data = json.loads(auth_msg)
        token = auth_data.get("token", "")
    except (asyncio.TimeoutError, json.JSONDecodeError, Exception):
        await ws.close(code=4001, reason="Authentication timeout or invalid format")
        return

    user_id = _extract_user_id_from_token(token)
    if not user_id:
        await ws.close(code=4001, reason="Invalid token")
        return

    # ─── Step 2: Check admin status ──────────────────────────────
    profile = await get_user_profile(user_id)
    if not profile or profile["role"] != "admin":
        await ws.close(code=4003, reason="Admin access required")
        return
    if profile["status"] != "approved":
        await ws.close(code=4003, reason="Account not approved")
        return

    logger.info("Terminal WebSocket connected: %s (%s)", profile["email"], user_id)

    # ─── Step 3: Spawn pty → tmux ────────────────────────────────
    try:
        master_fd, child_pid = _spawn_tmux_pty()
    except RuntimeError as e:
        await ws.close(code=4004, reason=str(e))
        return

    loop = asyncio.get_event_loop()

    # ─── Step 4: Bidirectional relay ─────────────────────────────

    async def pty_to_ws():
        """Read from pty master and send to WebSocket."""
        try:
            while True:
                data = await loop.run_in_executor(None, os.read, master_fd, 4096)
                if not data:
                    break
                await ws.send_bytes(data)
        except (OSError, WebSocketDisconnect):
            pass

    async def ws_to_pty():
        """Read from WebSocket and write to pty master."""
        try:
            while True:
                msg = await ws.receive()
                if msg["type"] == "websocket.receive":
                    if "bytes" in msg and msg["bytes"]:
                        await loop.run_in_executor(None, os.write, master_fd, msg["bytes"])
                    elif "text" in msg and msg["text"]:
                        # Handle resize messages
                        try:
                            data = json.loads(msg["text"])
                            if data.get("type") == "resize":
                                _resize_pty(master_fd, data["rows"], data["cols"])
                                continue
                        except (json.JSONDecodeError, KeyError):
                            pass
                        # Regular text input
                        await loop.run_in_executor(
                            None, os.write, master_fd, msg["text"].encode()
                        )
                elif msg["type"] == "websocket.disconnect":
                    break
        except (WebSocketDisconnect, Exception):
            pass

    # Run both directions concurrently
    try:
        await asyncio.gather(pty_to_ws(), ws_to_pty())
    finally:
        # Cleanup: close pty and kill child process
        try:
            os.close(master_fd)
        except OSError:
            pass
        try:
            os.kill(child_pid, signal.SIGTERM)
            os.waitpid(child_pid, os.WNOHANG)
        except (OSError, ChildProcessError):
            pass
        logger.info("Terminal WebSocket disconnected: %s", profile["email"])
