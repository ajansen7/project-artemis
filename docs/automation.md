# Automation Guide

Artemis can run scheduled jobs automatically — scouting for jobs, checking your inbox, engaging on LinkedIn, proposing blog posts, and nudging you about interviews. This guide covers setup and configuration.

---

## Overview

The automation system has two parts:

1. **Scheduler** — APScheduler runs inside the FastAPI server, triggering skills on a cron schedule
2. **Telegram handler** (optional) — a persistent Claude session that pushes results to your phone and lets you interact with running jobs

```
┌──────────────────────────────────────────────────────────────┐
│  FastAPI Server (api/server.py)                              │
│                                                              │
│  APScheduler                                                 │
│    ├─ Daily Inbox Check ──────┐                              │
│    ├─ Daily Job Scout ────────┤                              │
│    ├─ Daily LinkedIn ─────────┤── tmux ── Claude CLI ──┐     │
│    ├─ Networking Follow-ups ──┤                        │     │
│    ├─ Interview Prep ─────────┤                        │     │
│    ├─ Weekly Blog Ideas ──────┤                 push_to_tg   │
│    └─ Publish Reminder ───────┘                   │    │     │
│                                                   ▼    │     │
│  Relay Queue ◄─────── relay_ask.py ◄─────────── Job    │     │
│       │                                                │     │
└───────┼────────────────────────────────────────────────┼─────┘
        │                                                │
        │              ┌─────────────────────────────┐   │
        │              │  Telegram Handler Session    │   │
        │              │  (.claude/agents/telegram-   │   │
        │              │   handler.md)                │   │
        ▼              │                              │   │
  /api/relay/reply ◄───│  Receives user replies       │   │
                       │  Dispatches new skills       │   │
                       │  Answers quick queries       │   │
                       └──────────┬──────────────────┘   │
                                  │                      │
                                  ▼                      │
                           Your Phone ◄──────────────────┘
                         (Telegram Bot)    (direct Bot API)
```

---

## Prerequisites

- **Artemis** fully set up (profile, Supabase, skills working)
- **tmux** installed (`brew install tmux`)
- For mobile notifications:
  - **[Bun](https://bun.sh)** runtime (`curl -fsSL https://bun.sh/install | bash`)
  - **Telegram** or **Discord** account for the chat bridge

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
| Daily Inbox Check | `/inbox` | Weekdays 8am | Scan Gmail for recruiter emails |
| Daily LinkedIn Engagement | `/linkedin` | Weekdays 9am | Find posts to engage with |
| Daily Job Scout | `/scout` | Weekdays 7am | Search for new postings |
| Networking Follow-ups | `/network` | Mon & Thu 10am | Surface stale contacts |
| Interview Prep Reminder | `/prep` | Daily 6pm | Check upcoming interviews |
| Weekly Blog Ideas | `/blog-ideas` | Monday 10am | Propose blog topics |
| Draft Publish Reminder | `/blog-status` | Friday 9am | Remind about ready drafts |

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

Times are in your local timezone.

### How jobs execute

Each scheduled job:
1. Launches a Claude CLI instance in a tmux window (same as manual skill runs)
2. Runs the skill (e.g., `/scout`, `/inbox`)
3. On completion, updates `last_run_at` and `last_status` in the `scheduled_jobs` table
4. If the webhook channel is running, POSTs a summary to it

You can monitor running jobs via `tmux attach -t artemis` or the TasksPanel in the dashboard.

---

## Part 2: Telegram Integration

This is optional. It enables push notifications to your phone, interactive mid-job questions, and the ability to kick off tasks from Telegram.

For full Telegram setup instructions, see [getting-started.md](getting-started.md#optional-telegram-setup).

### How it works

Artemis uses two paths for Telegram communication:

**Outbound (job to phone):** Scheduled jobs call `push_to_telegram.py` directly to send curated, mobile-formatted messages via the Telegram Bot API. The API server also sends a fallback notification on job completion.

**Inbound (phone to Artemis):** A persistent Claude session (the "Telegram handler") runs with the Telegram plugin and receives all incoming messages. It can:
- Dispatch skills (`/scout`, `/inbox`, etc.) via the API
- Answer quick queries (pipeline status, running tasks)
- Route relay replies back to jobs waiting for user input

### Relay questions

When a scheduled job needs user input mid-run, it calls `relay_ask.py` which:
1. Posts the question to the API's relay queue
2. The API sends the question to Telegram via Bot API
3. The user replies on Telegram
4. The handler session routes the reply back via `/api/relay/reply`
5. `relay_ask.py` (still polling) picks up the answer and the job continues

Questions time out after 5 minutes. On timeout, the job proceeds with the safest default.

---

## Troubleshooting

### Scheduler not running

- Verify the API server is running: `curl http://localhost:8000/api/schedules`
- Check that schedules are enabled in the Schedules tab
- Check server logs for scheduler errors

### Job fails immediately

- Ensure `claude` CLI is on PATH: `which claude`
- Ensure tmux is installed: `which tmux`
- Check the tmux session: `tmux attach -t artemis`
- Look at `last_error` in the schedule card (expand to see)

### No Telegram notifications

- Test direct send: `uv run python .claude/tools/push_to_telegram.py send --text "test"`
- If that works but scheduled jobs don't send: check that `_RELAY_INSTRUCTIONS` are being injected (the job prompt should mention `push_to_telegram.py`)
- Check the handler session is running: look for the `telegram` window in tmux
- Verify bot is paired: `/telegram:access list`

### Telegram handler not responding to messages

- Make sure `.claude/settings.json` has `"enabledPlugins": {}` (empty). The handler session passes the plugin via `--settings` flag so only it polls `getUpdates`.
- Restart the handler: `./scripts/stop.sh && ./scripts/start.sh`

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

### Relay endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/relay/ask` | Subprocess posts a question, gets a token |
| `GET` | `/api/relay/answer/{token}` | Subprocess polls for the user's reply |
| `GET` | `/api/relay/pending` | Handler checks for pending questions |
| `POST` | `/api/relay/reply` | Handler posts the user's answer back |

### Skill execution

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/run-skill` | Start a skill (body: `{"skill": "scout", "target": "..."}`) |
| `GET` | `/api/tasks` | List running tasks |
| `GET` | `/api/tasks/{id}` | Get task status + output |
