# Artemis Channel Architecture

This document describes how the API, scheduler, and orchestrator communicate.

> **Note:** This document supersedes the old relay-queue design. The relay queue (`relay_ask.py`, `/api/relay/*`) has been removed and replaced with the push-based channel architecture below.

---

## Overview

The core problem: when the API or scheduler wants to run a skill, how does the orchestrator (a long-running Claude session) find out immediately?

**Old approach (retired):** APScheduler spawned a new `claude` CLI subprocess in a tmux window per task. The "Telegram handler" was a separate session that polled the relay queue for mid-job questions.

**Current approach:** A single long-running orchestrator session handles everything. Tasks arrive via a push channel — no polling, no spawning new processes.

---

## Architecture

```
UI / Scheduler
      │
      ▼
 POST /api/run-skill   (or schedule fires, or blog/apply route queues a task)
      │
      ├── INSERT INTO task_queue (status = "queued")
      │
      └── POST http://127.0.0.1:8790/task
                    │
                    ▼
         artemis-channel (Bun MCP server)
         channels/artemis-channel/index.ts
                    │
                    │  notifications/claude/channel
                    ▼
         Orchestrator session (Claude Code, long-running)
         .claude/agents/artemis-orchestrator.md
                    │
                    ├── Skill tool: executes the skill
                    ├── db.py update-task --status complete
                    └── push_to_telegram.py → User's Phone
```

---

## Components

### task_queue (Supabase)

Every task — whether queued from the UI, a schedule, or an API route — gets inserted into `task_queue` first. This table is the durable execution bus. If the channel is down, tasks wait here and can be recovered.

Schema: `id, name, skill, skill_args, source, status, output_summary, error, created_at, started_at, ended_at, schedule_id`

### artemis-channel (MCP server)

A Bun/TypeScript MCP server running at `http://127.0.0.1:8790`. It:
- Accepts `POST /task` — fires a `notifications/claude/channel` event into Claude
- Accepts `POST /notify` — generic notification (schedule fired, etc.)
- Connects to Claude via MCP stdio transport (started as a subprocess by Claude Code via `.mcp.json`)

Claude Code loads it via `--dangerously-load-development-channels server:artemis-channel`. The `start.sh` script automatically confirms the one-time local-development prompt.

### Orchestrator (Claude Code session)

A single long-running Claude session with two channel sources:
- `plugin:telegram@claude-plugins-official` — receives Telegram messages from the user
- `server:artemis-channel` — receives task events from the API

When a task event arrives, the orchestrator:
1. Parses the task JSON (id, skill, skill_args, name, source)
2. Executes the skill via the `Skill` tool
3. Updates `task_queue` via `db.py update-task`
4. Sends a summary to Telegram via `push_to_telegram.py`

### API notify helper (api/modules/channel.py)

Every route that inserts into `task_queue` calls this after the insert:

```python
async def notify_task(task: dict) -> None:
    """Fire-and-forget POST to the orchestrator channel."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post("http://127.0.0.1:8790/task", json=task)
    except Exception:
        pass  # non-fatal — task remains in DB
```

The POST is fire-and-forget with a 2s timeout. If the channel is down, the task remains in Supabase.

---

## Telegram Communication

**Outbound (Artemis to phone):** After each task completes (or at any point during execution), the orchestrator calls `push_to_telegram.py` to send a summary via the Telegram Bot API. This is a direct API call — no relay or proxy.

**Inbound (phone to orchestrator):** The Telegram plugin delivers messages directly into the orchestrator's context as channel events. The orchestrator handles them inline — dispatching skills, answering queries, checking the pipeline.

There is no relay queue. The orchestrator can ask follow-up questions directly via Telegram mid-task if needed.

---

## Resilience

| Scenario | Behavior |
|----------|----------|
| artemis-channel is down | Tasks queue in Supabase. Orchestrator picks them up on next Telegram interaction or manual `db.py next-task` |
| Orchestrator restarts | Tasks remain in `task_queue` with `status = "queued"`. On restart, orchestrator can claim them |
| API server down | Tasks can't be inserted. User sees error in UI |
| Telegram down | Orchestrator still executes tasks; summaries fail silently |
