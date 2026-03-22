# Bidirectional Telegram Relay for Scheduled Jobs

## Problem

Scheduled jobs run as isolated `claude` subprocesses in tmux. When Claude needs
user input mid-job (clarifying questions, approval requests), there's no way to
route that interaction to Telegram and get a reply back into the running process.

## Architecture: Main Session as Relay Proxy

The Telegram plugin (long-polling) already runs in the main Claude session. Only
one process can poll a bot's updates, so the main session acts as the relay proxy.

```
Subprocess calls relay_ask.py
  → POST /api/relay/ask {job_name, skill, question}
    → FastAPI stores in RelayQueue, fires webhook notification
      → artemis-webhook MCP pushes to main Claude session
        → Main session sends question to Telegram

User replies on Telegram
  → Telegram plugin delivers reply to main Claude session
    → Main session POSTs to /api/relay/reply {token, answer}
      → FastAPI stores answer in RelayQueue

relay_ask.py (still polling GET /api/relay/answer/{token})
  → Gets answer → prints to stdout → subprocess continues
```

## Components

### 1. RelayQueue (`api/server.py`)

In-memory store with 5-minute timeout. Thread-safe via `threading.Lock`.

- `ask(job_name, skill, question) → token` (12-char hex)
- `get_answer(token) → RelayEntry` (checks expiry)
- `reply(token, answer) → bool` (False if expired)
- `cleanup()` prunes entries older than 2x timeout

### 2. API Endpoints (`api/server.py`)

| Endpoint | Called by | Purpose |
|----------|-----------|---------|
| `POST /api/relay/ask` | `relay_ask.py` | Store question, fire webhook |
| `GET /api/relay/answer/{token}` | `relay_ask.py` (polling) | Check for answer |
| `POST /api/relay/reply` | Main session (curl) | Deposit user's answer |

### 3. `relay_ask.py` (`.claude/tools/relay_ask.py`)

Blocking CLI tool for subprocesses:

```bash
uv run python .claude/tools/relay_ask.py \
  --job-name "Morning Scout" --skill "scout" \
  --question "Found 8 jobs. Save all or filter?" \
  --timeout 300
```

- Polls every 3 seconds
- Prints answer to stdout on success
- Prints `RELAY_TIMEOUT` on expiry (exit 0, not 1)
- Prints `RELAY_ERROR` to stderr on connection failure (exit 1)

### 4. Webhook Handler (`channels/artemis-webhook/index.ts`)

Discriminates on `type` field:
- `type === "relay_question"` → builds relay notification with token/question
- Default → existing completion handler

### 5. MCP Instructions

The webhook instructions tell the main session to:
1. Send relay questions to Telegram immediately
2. When the user replies, POST to `/api/relay/reply` via curl
3. Confirm relay completion to user

### 6. Skill Prompt Injection

`_build_skill_command(skill, skill_args, job_name)` appends relay instructions
to the prompt when `job_name` is provided (scheduled/manual-trigger runs).
Ad-hoc `/api/run-skill` calls from the frontend don't get relay instructions.

## Timeout Behavior

- Default: 5 minutes
- On timeout: `relay_ask.py` prints `RELAY_TIMEOUT`, subprocess proceeds with
  safest default (skip action, save draft, note for later)
- Expired tokens reject late replies with HTTP 410

## Limitations

- **Main session must be running.** If it's not, the webhook fails silently and
  `relay_ask.py` times out.
- **Reply routing relies on conversational context.** The main session matches
  Telegram replies to relay tokens by conversation flow. This works well for
  sequential questions but could be fragile with many concurrent relays.
- **In-memory queue.** Server restart loses pending questions. Acceptable for v1
  since questions have short timeouts anyway.
