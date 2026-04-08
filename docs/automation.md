# Automation Guide

Artemis can run scheduled jobs automatically -- scouting for jobs, checking your inbox, engaging on LinkedIn, proposing blog posts, and nudging you about interviews. This guide covers setup and configuration.

---

## Overview

The automation system has three parts:

1. **Scheduler** -- APScheduler runs inside the FastAPI server, triggering skills on a cron schedule by inserting into `task_queue`
2. **artemis-channel** -- a local MCP server that pushes `task_queue` inserts into the orchestrator session instantly (no polling)
3. **Orchestrator** (optional for Telegram) -- a persistent Claude session that executes skills and pushes results to your phone

**Claude Desktop users:** If you are using Claude Desktop instead of the CLI, start services with `./scripts/start.sh --no-orchestrator`. The API server and frontend will run, but the long-running CLI orchestrator session will not be started. Tasks will queue in Supabase and can be executed manually.

```
UI / Dashboard
      |
      v
POST /api/run-skill
      |
      v
 task_queue (Supabase)
      |
      v POST http://127.0.0.1:8790/task
 artemis-channel MCP
      | (notifications/claude/channel)
      v
 Orchestrator session (long-running Claude)
      |
      +-- executes skill via Skill tool
      +-- updates task_queue status
      +-- artemis-telegram → Your Phone


APScheduler (FastAPI)
      |
      +-- fires cron trigger
      +-- inserts into task_queue
      +-- notifies artemis-channel (same path as above)
```

---

## Prerequisites

- **Artemis** fully set up (profile, Supabase, skills working)
- **tmux** installed (`brew install tmux`)
- **Bun** runtime (`curl -fsSL https://bun.sh/install | bash`) -- needed by the artemis-channel
- For mobile notifications: Telegram bot configured (see [getting-started.md](getting-started.md#optional-telegram-setup))

---

## Part 1: Scheduler Setup

The scheduler is built into the FastAPI server. No extra services needed.

### Start the API server

```bash
uv run uvicorn api.server:app --reload
```

On startup, the server loads all enabled schedules from Supabase and registers them with APScheduler. You'll see in the logs:

```
INFO:     artemis.scheduler - Loaded N enabled schedules
INFO:     artemis.scheduler - Scheduler started
```

### Configure schedules from the dashboard

Open `http://localhost:5173` and click the **Schedules** tab. You'll see the default schedules (all disabled):

| Schedule | Skill | Default Cron | Description |
|----------|-------|-------------|-------------|
| Daily Inbox Check | `/artemis:inbox` | Weekdays 8am | Scan Gmail for recruiter emails |
| Daily LinkedIn Engagement | `/artemis:linkedin-scout` | Weekdays 9am | Find posts to engage with |
| Daily Job Scout | `/artemis:scout` | Weekdays 7am | Search for new postings |
| Networking Follow-ups | `/artemis:network` | Mon & Thu 10am | Surface stale contacts |
| Interview Prep Reminder | `/artemis:prep` | Daily 6pm | Check upcoming interviews |
| Weekly Blog Ideas | `/artemis:blog-ideas` | Monday 10am | Propose blog topics |
| Draft Publish Reminder | `/artemis:blog-status` | Friday 9am | Remind about ready drafts |

**To enable a schedule:** Toggle the checkbox on the card. The scheduler picks it up immediately.

**To change the schedule:** Click the card to expand, click Edit, modify the cron expression or other fields.

**To add a custom schedule:** Click "+ Add Schedule" at the top. Pick a skill, set the cron, give it a name.

**To run a job immediately:** Expand the card, click "Run Now". The task appears in the floating TasksPanel.

### Cron expression reference

| Pattern | Meaning |
|---------|---------|
| `0 8 * * 1-5` | Weekdays at 8:00 AM |
| `0 9 * * *` | Every day at 9:00 AM |
| `0 10 * * 1,4` | Monday and Thursday at 10:00 AM |
| `0 10 * * 1` | Every Monday at 10:00 AM |
| `*/30 * * * *` | Every 30 minutes |

Times are in your local timezone (America/Denver by default -- change in `api/modules/scheduler.py`).

### How jobs execute

Each scheduled job:
1. Inserts a row into `task_queue` (Supabase) with `status = "queued"`
2. POSTs the task to `http://127.0.0.1:8790/task` (the artemis-channel)
3. The artemis-channel MCP pushes the event into the orchestrator's context
4. The orchestrator executes the skill immediately
5. On completion, updates `task_queue` with `status = "complete"` and an output summary
6. Pushes a brief summary to Telegram (if configured)

Task pickup is sub-second. If the artemis-channel is temporarily down, tasks remain in Supabase with `status = "queued"` and can be recovered.

You can monitor tasks via the floating TasksPanel in the dashboard or by running:

```bash
artemis-db list-tasks
artemis-db list-tasks --status running
```

---

## Part 2: Telegram Integration

This is optional. It enables push notifications to your phone and the ability to kick off tasks from Telegram.

For full Telegram setup instructions, see [getting-started.md](getting-started.md#optional-telegram-setup).

### How it works

The orchestrator (`agents/orchestrator.md`) is a single Claude session that handles both Telegram and task execution:

**Outbound (Artemis to phone):** After each task completes, the orchestrator calls `artemis-telegram` to send a summary via the Telegram Bot API. Direct sends from skills also use `artemis-telegram`.

**Inbound (phone to Artemis):** The orchestrator listens for Telegram messages via the Telegram plugin. It dispatches skills, answers quick queries (pipeline status, running tasks), and responds directly.

### Commands from Telegram

| Message | Action |
|---------|--------|
| `/scout` | Run the scout skill |
| `/inbox` | Check Gmail for recruiter activity |
| `/status` | Pipeline overview |
| `/review` | Triage the pipeline |
| `/network` | Networking pipeline |
| `/prep <company>` | Interview prep for a company |
| `/blog-ideas` | Generate blog ideas |
| `/blog-status` | Check blog drafts |

---

## Troubleshooting

### Scheduler not running

- Verify the API server is running: `curl http://localhost:8000/api/schedules`
- Check that schedules are enabled in the Schedules tab
- Check server logs for scheduler errors

### Tasks stuck in "queued"

- Check that the artemis-channel is up: `curl -X POST http://127.0.0.1:8790/notify -H "Content-Type: application/json" -d '{"message":"test"}'` -- should return "ok"
- Check the orchestrator is running and shows `server:artemis-channel` in its channel list: `tmux attach -t artemis` and look at the `orchestrator` window header
- If the orchestrator is running but the channel isn't listed, restart with `./scripts/stop.sh && ./scripts/start.sh`

### No Telegram notifications

- Test direct send: `artemis-telegram send --text "test"`
- Check the orchestrator is running: `tmux attach -t artemis` -> `orchestrator` window
- Verify bot is paired: `/telegram:access list` in the orchestrator session

### Orchestrator not responding to Telegram messages

- Check the orchestrator shows Telegram in its channel list: header should read `Listening for channel messages from: plugin:telegram@claude-plugins-official, server:artemis-channel`
- Restart the orchestrator: `./scripts/stop.sh && ./scripts/start.sh`

---

## API Reference

### Schedule endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/schedules` | List all schedules |
| `POST` | `/api/schedules` | Create a schedule |
| `PUT` | `/api/schedules/{id}` | Update a schedule |
| `DELETE` | `/api/schedules/{id}` | Delete a schedule |
| `POST` | `/api/schedules/{id}/run-now` | Trigger immediately |

### Task endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/run-skill` | Queue a skill (body: `{"skill": "scout", "target": "..."}`) |
| `GET` | `/api/tasks` | List recent tasks |
| `GET` | `/api/tasks/{id}` | Get task status + output summary |
