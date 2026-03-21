# Automation Guide

Artemis can run scheduled jobs automatically — scouting for jobs, checking your inbox, engaging on LinkedIn, proposing blog posts, and nudging you about interviews. This guide covers setup and configuration.

---

## Overview

The automation system has two parts:

1. **Scheduler** — APScheduler runs inside the FastAPI server, triggering skills on a cron schedule
2. **Claude Channel** (optional) — pushes job summaries to your phone via Telegram or Discord, so you can approve engagement actions on the go

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Server (api/server.py)                             │
│                                                             │
│  APScheduler                                                │
│    ├─ Daily Inbox Check ──────┐                             │
│    ├─ Daily Job Scout ────────┤                             │
│    ├─ Daily LinkedIn ─────────┤── tmux ── Claude CLI ──┐    │
│    ├─ Networking Follow-ups ──┤                        │    │
│    ├─ Interview Prep ─────────┤                        │    │
│    ├─ Weekly Blog Ideas ──────┤                        │    │
│    └─ Publish Reminder ───────┘                        │    │
│                                                        │    │
│  On completion: POST to webhook channel ──────────┐    │    │
│                                                   │    │    │
└───────────────────────────────────────────────────┼────┼────┘
                                                    │    │
┌───────────────────────────────────────────────────┼────┼────┐
│  Claude Code Session (--channels)                 │    │    │
│                                                   ▼    │    │
│  artemis-webhook channel ◄─── HTTP POST ──────────┘    │    │
│       │                                                │    │
│       ▼                                                │    │
│  Claude receives event, checks DB for pending items    │    │
│       │                                                │    │
│       ▼                                                │    │
│  Telegram/Discord reply tool ──► Your Phone            │    │
│       │                                                │    │
│       ▼                                                │    │
│  You reply: "approve 1 and 3, skip 2"                  │    │
│       │                                                │    │
│       ▼                                                │    │
│  Claude updates engagement_log in Supabase             │    │
└─────────────────────────────────────────────────────────────┘
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

## Part 2: Mobile Notifications via Claude Channels

This is optional. It enables push notifications to your phone and interactive approval of engagement actions.

### Step 1: Set up a Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`, choose a name and username (must end in `bot`)
3. Copy the bot token BotFather gives you

### Step 2: Install the Telegram channel plugin

In Claude Code:

```
/plugin install telegram@claude-plugins-official
/reload-plugins
/telegram:configure <your-bot-token>
```

### Step 3: Install the webhook channel dependencies

```bash
cd channels/artemis-webhook
bun install
```

### Step 4: Start Claude Code with channels

```bash
claude --channels plugin:telegram@claude-plugins-official \
       --dangerously-load-development-channels server:artemis-webhook
```

### Step 5: Pair your Telegram account

1. Open Telegram and message your bot
2. The bot replies with a pairing code
3. In Claude Code, run:
   ```
   /telegram:access pair <code>
   /telegram:access policy allowlist
   ```

### Step 6: Keep the session running

Claude Channels only push events while the session is running. Keep it open in a persistent tmux window:

```bash
tmux new-session -d -s artemis-channels \
  'claude --channels plugin:telegram@claude-plugins-official --dangerously-load-development-channels server:artemis-webhook'
```

### How it works

1. A scheduled job completes (e.g., Daily LinkedIn Engagement)
2. The FastAPI server POSTs a summary to `http://localhost:8790/notify`
3. The artemis-webhook channel pushes the event into the Claude Code session
4. Claude checks Supabase for pending engagement items, upcoming interviews, blog drafts
5. Claude sends a summary to your Telegram via the reply tool
6. You respond: "approve 1 and 3", "skip 2", or ask follow-up questions
7. Claude updates the database accordingly

### Using Discord instead

Replace `telegram` with `discord` in all commands above. See the [Discord channel setup](https://code.claude.com/docs/en/channels) for bot creation and permission details.

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

- Confirm the Claude Code session with `--channels` is running
- Confirm the webhook server is listening: `curl -X POST http://localhost:8790/notify -d '{"job":"test","status":"complete"}'`
- Check that the webhook event appeared in the Claude Code terminal
- Verify your Telegram bot is paired: `/telegram:access list`

### Channel blocked by org policy

If you see "blocked by org policy" when starting with `--channels`, your Team or Enterprise admin needs to enable channels in [admin settings](https://claude.ai/admin-settings/claude-code).

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

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ARTEMIS_WEBHOOK_URL` | `http://localhost:8790/notify` | Where to POST job completion events |
| `ARTEMIS_WEBHOOK_PORT` | `8790` | Port for the webhook channel server |
