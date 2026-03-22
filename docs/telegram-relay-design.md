# Bidirectional Telegram Relay for Scheduled Jobs

## Problem

Scheduled jobs run as isolated `claude` subprocesses in tmux. When Claude needs
user input mid-job (clarifying questions, approval requests, etc.), there's no
way to route that interaction to Telegram and get a reply back into the running
process.

The current solution (Option 1) captures job output at completion and forwards it
to Telegram via the webhook. This covers end-of-job summaries and closing
questions, but cannot support true mid-job interaction.

## Option 2: Bidirectional Relay

### Architecture

```
Scheduled Claude subprocess
        |
        | HTTP POST /api/relay/ask
        v
FastAPI relay endpoint
        |
        | Telegram Bot API (direct)
        v
User's phone (Telegram)
        |
        | User replies to bot
        v
Telegram webhook → POST /api/relay/reply
        |
        | Stored in reply queue (in-memory or DB)
        v
Subprocess polls GET /api/relay/answer?token=...
        |
        | Returns reply when available
        v
Subprocess continues
```

### Components

#### 1. FastAPI relay endpoints (`api/server.py`)

```python
# POST /api/relay/ask
# Body: { "message": "...", "job_name": "...", "timeout": 300 }
# Returns: { "token": "<uuid>", "status": "waiting" }

# GET /api/relay/answer?token=<uuid>
# Returns: { "status": "waiting" | "answered", "reply": "..." }

# POST /api/relay/reply  (called by Telegram webhook)
# Body: { "token": "<uuid>", "reply": "..." }
```

The server maintains an in-memory dict `relay_queue: dict[str, str | None]` mapping
tokens to replies (None = still waiting).

#### 2. Telegram bot webhook

The Telegram bot needs to be configured to call `POST /api/relay/reply` when
the user replies to a relay message. The bot token lives in the environment as
`TELEGRAM_BOT_TOKEN`. The chat ID is stored in the existing access config.

The relay messages sent to Telegram should include the token in a way the bot
can route replies back (e.g., a hidden footer or by tracking the message_id).

#### 3. Relay helper script (`.claude/tools/relay_ask.py`)

A small Python script the scheduled Claude can call via bash:

```bash
uv run python .claude/tools/relay_ask.py --message "Should I apply to this job?" --timeout 120
# Blocks until reply or timeout. Prints reply to stdout.
```

The script:
1. POSTs to `/api/relay/ask`
2. Polls `/api/relay/answer?token=...` every 5s
3. Prints the reply and exits 0, or prints "TIMEOUT" and exits 1 after timeout

#### 4. Skill instructions update

Skills that may need user input would be taught to call the relay tool:

```
If you need user input, call:
  uv run python .claude/tools/relay_ask.py --message "your question here" --timeout 120
The reply will be printed to stdout. If it returns TIMEOUT, proceed with your best judgment.
```

### Telegram bot setup

The Telegram plugin already handles inbound messages to the main session. For
the relay, we need the bot to distinguish between:
- Normal messages → handled by the main Claude session as usual
- Replies to relay messages → routed to `/api/relay/reply`

One approach: relay messages include a reply keyboard with structured options, or
a unique prefix the bot can detect (`[RELAY:<token>]`). The Telegram webhook
handler checks for this prefix and routes accordingly.

### Timeout behavior

If no reply arrives within the timeout, `relay_ask.py` exits with "TIMEOUT". The
skill should proceed with a sensible default. This prevents jobs from hanging
indefinitely if the user is unavailable.

### Security

- Relay tokens are UUIDs, single-use, expire after timeout.
- `/api/relay/reply` should verify the token exists before accepting a reply.
- The Telegram webhook should validate the bot token to prevent spoofing.

### When to implement

This is worth building when:
- Skills start needing mid-job decisions (e.g., apply skill asking "this job is
  a 65/100 match — apply anyway?")
- The job output → Telegram notification flow isn't sufficient for the use case
- Latency of waiting for job completion is a problem

The current Option 1 flow (completion → webhook → Telegram) handles the majority
of use cases. Add this when interactive mid-job decisions become a real need.
