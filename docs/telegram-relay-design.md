# Telegram Integration Architecture

## Overview

Artemis uses Telegram as its primary mobile interface. The architecture has two communication paths:

**Outbound (Artemis to user):** Scheduled jobs call `push_to_telegram.py` directly via the Telegram Bot API to send curated, mobile-formatted messages. No proxy or webhook chain.

**Inbound (user to Artemis):** A persistent Claude CLI session (the "Telegram handler") runs with the Telegram plugin, receiving all incoming messages. It dispatches skills, answers queries, and routes relay replies.

## Architecture Diagram

```
Scheduled Job (Claude CLI in tmux)
  │
  ├─ push_to_telegram.py ──► Telegram Bot API ──► User's Phone
  │
  └─ relay_ask.py ──► POST /api/relay/ask
                         │
                         ├─ Stores question in RelayQueue
                         └─ Sends to Telegram via Bot API
                                     │
                                     ▼
                              User replies on Telegram
                                     │
                                     ▼
                         Telegram Handler Session
                         (receives via plugin getUpdates)
                                     │
                         GET /api/relay/pending → match token
                         POST /api/relay/reply → deposit answer
                                     │
                                     ▼
                         relay_ask.py polls /api/relay/answer/{token}
                         Gets answer → prints to stdout → job continues
```

## Components

### 1. `push_to_telegram.py` (`.claude/tools/push_to_telegram.py`)

CLI tool for sending formatted messages directly via Bot API.

```bash
uv run python .claude/tools/push_to_telegram.py summary \
  --job-name "Morning Scout" --status success \
  --body "Found 3 new roles..."

uv run python .claude/tools/push_to_telegram.py question \
  --job-name "Morning Scout" --token abc123 \
  --question "Save all 8 jobs or filter to top 5?"

echo "long content" | uv run python .claude/tools/push_to_telegram.py send --stdin
```

### 2. `relay_ask.py` (`.claude/tools/relay_ask.py`)

Blocking CLI tool for subprocesses that need user input:

```bash
uv run python .claude/tools/relay_ask.py \
  --job-name "Morning Scout" --skill "scout" \
  --question "Found 8 jobs. Save all or filter?" \
  --timeout 300
```

- Polls `/api/relay/answer/{token}` every 3 seconds
- Prints answer to stdout on success
- Prints `RELAY_TIMEOUT` on expiry (exit 0, not 1)

### 3. Telegram Handler Session (`.claude/agents/telegram-handler.md`)

A persistent Claude CLI session that owns the Telegram plugin (sole `getUpdates` consumer).

**Capabilities:**
- Dispatch skills via `POST /api/run-skill`
- Answer quick queries by running `db.py` directly
- Route relay replies by checking `/api/relay/pending` and posting to `/api/relay/reply`

**Launched by `scripts/start.sh`:**
```bash
claude --agent telegram-handler --dangerously-skip-permissions \
  --settings '{"enabledPlugins":{"telegram@claude-plugins-official":true}}'
```

### 4. RelayQueue (`api/server.py`)

In-memory store with 5-minute timeout. Thread-safe via `threading.Lock`.

- `ask(job_name, skill, question) -> token` (12-char hex)
- `get_answer(token) -> RelayEntry` (checks expiry)
- `reply(token, answer) -> bool` (False if expired)
- `pending() -> list[RelayEntry]` (unanswered, unexpired)
- `cleanup()` prunes entries older than 2x timeout

### 5. API Endpoints (`api/server.py`)

| Endpoint | Called by | Purpose |
|----------|-----------|---------|
| `POST /api/relay/ask` | `relay_ask.py` | Store question, send to Telegram |
| `GET /api/relay/answer/{token}` | `relay_ask.py` (polling) | Check for answer |
| `GET /api/relay/pending` | Telegram handler | List unanswered questions |
| `POST /api/relay/reply` | Telegram handler | Deposit user's answer |

## Plugin Ownership

The Telegram plugin uses long-polling (`getUpdates`). Only one consumer can poll at a time.

- `.claude/settings.json` has `"enabledPlugins": {}` (empty) so the main interactive session does NOT load the plugin
- The handler session enables it via `--settings '{"enabledPlugins":{"telegram@claude-plugins-official":true}}'`
- This ensures the handler is the sole consumer

## Timeout Behavior

- Default: 5 minutes
- On timeout: `relay_ask.py` prints `RELAY_TIMEOUT`, subprocess proceeds with safest default
- Expired tokens reject late replies with HTTP 410

## Limitations

- **Handler session can hit context limits.** It's stateless (all state in API + Supabase), so restarting is safe. Long-term: add a watchdog.
- **Reply routing is sequential.** The handler matches replies to the most recent pending question. Multiple concurrent relay questions could cause mismatches.
- **In-memory queue.** Server restart loses pending questions. Acceptable since questions have short timeouts.
