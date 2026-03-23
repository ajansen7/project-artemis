# Getting Started with Artemis

This guide walks you through setting up Artemis from scratch, including all optional integrations.

---

## Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)**
- **Node.js 18+** and **npm** (for the dashboard)
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** (`npm install -g @anthropic-ai/claude-code`)
- **tmux** (`brew install tmux`)
- **Supabase** project ([supabase.com](https://supabase.com), free tier works)

Optional:
- **LibreOffice** for PDF resume generation: `brew install --cask libreoffice`
- **[Bun](https://bun.sh)** runtime (only if working with the legacy webhook channel)

---

## Step 1: Clone and Install

```bash
git clone <repo-url> project-artemis
cd project-artemis
git submodule update --init    # clones the interview-coach skill
uv sync                        # install Python dependencies
cd frontend && npm install && cd ..
```

---

## Step 2: Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Go to the SQL Editor and run migrations in order: `db/migrations/001_*.sql` through `db/migrations/016_*.sql`
3. Configure credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Supabase values:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Verify the connection:
```bash
uv run python .claude/tools/db.py status
```

---

## Step 3: Run the Setup Wizard

```bash
cd project-artemis
claude
```

On first launch, the session hook detects no candidate profile and prompts you. You can also trigger it manually:

```
/setup
```

The wizard walks you through:
1. Candidate identity (name, role, positioning, career arc)
2. Voice and tone preferences for communications
3. Search preferences (target roles, companies, deal-breakers)
4. Resume master (structured resume bullets, the source of truth for all applications)
5. Application form defaults (contact info, work authorization, etc.)
6. Optional: interview-coach kickoff for storybank and deeper profile analysis

---

## Step 4: Start Services

```bash
./scripts/start.sh
```

This creates a tmux session called `artemis` with three windows:

| Window | Service | What It Does |
|--------|---------|-------------|
| `api` | FastAPI (port 8000) | Backend: scheduler, task management, relay queue |
| `frontend` | Vite (port 5173) | React dashboard |
| `telegram` | Claude CLI session | Persistent Telegram handler (if configured) |

Useful commands:
```bash
tmux attach -t artemis          # see all windows
./scripts/stop.sh               # stop services, keep tmux session
./scripts/stop.sh --kill        # kill everything
./scripts/start.sh --no-frontend  # skip the dashboard
```

---

## Step 5: Configure the Dashboard

Open `http://localhost:5173` in your browser.

The dashboard has five tabs:
- **Pipeline** -- all jobs by status, match scores, application generation, sort/group controls, stale indicators
- **Networking** -- contacts, outreach status, interaction history
- **Engagement** -- LinkedIn/blog approval queue
- **Blog** -- content lifecycle from idea to published
- **Schedules** -- recurring automation configuration

To enable scheduled jobs, go to the **Schedules** tab and toggle on the ones you want.

---

## Optional: Telegram Setup

Telegram lets you interact with Artemis from your phone. Scheduled jobs push results to Telegram, you can reply to mid-job questions, and you can kick off tasks directly from the chat.

### 5a. Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`, choose a name and username (must end in `bot`)
3. Copy the bot token BotFather gives you

### 5b. Install the Telegram Plugin

In a Claude Code session (inside the project directory):

```
/install-plugin telegram@claude-plugins-official
```

When prompted, configure it:
```
/telegram:configure <your-bot-token>
```

### 5c. Pair Your Account

1. Open Telegram and send any message to your bot
2. The bot replies with a pairing request
3. In Claude Code, approve it:
   ```
   /telegram:access approve
   /telegram:access policy allowlist
   ```

### 5d. Verify It Works

Test sending a message directly:
```bash
uv run python .claude/tools/push_to_telegram.py send --text "Hello from Artemis!"
```

You should see the message on your phone.

### 5e. Start the Telegram Handler

The handler is started automatically by `./scripts/start.sh`. It runs as a persistent Claude session with the Telegram plugin enabled, listening for your messages.

Once running, you can message your bot from Telegram:
- `/scout` -- kicks off a job scouting run
- `/inbox` -- scans Gmail for recruiter activity
- `/status` -- shows your pipeline overview
- Reply to any job question and it gets relayed back to the running task

The Telegram plugin is configured to only load in the handler session (not your main interactive session) to avoid polling conflicts. This is controlled by `.claude/settings.json` -- the `enabledPlugins` section should be empty, and the handler's launch command passes the plugin via `--settings`.

---

## Optional: Gmail and Calendar MCP

These enable the `/inbox` skill (scanning for recruiter emails, interview scheduling, follow-up drafting).

Gmail and Calendar are Claude.ai OAuth integrations. They are configured through Claude Code's settings, not in this project.

1. In Claude Code, go to Settings and enable Gmail and Google Calendar integrations
2. Authorize with your Google account when prompted
3. Verify: run `/inbox` and confirm it can search your email

These integrations are only available in interactive Claude sessions (not headless `-p` mode). Scheduled jobs that need Gmail/Calendar run in interactive mode automatically.

---

## Optional: Claude in Chrome MCP

This enables the `/linkedin` and `/blogger` skills (LinkedIn browsing, engagement drafting, blog publishing).

1. Install the [Claude in Chrome extension](https://chromewebstore.google.com/detail/claude-in-chrome)
2. In Claude Code, enable it: Settings > Chrome integration
3. Verify: run `/linkedin` and confirm it can navigate to LinkedIn

---

## Optional: Supabase MCP

Direct database access for running migrations, ad-hoc queries, and schema changes.

1. In Claude Code, go to Settings and enable the Supabase integration
2. Connect it to your Supabase project
3. Verify: ask Claude to list your tables

---

## Scheduled Automation

With services running (`./scripts/start.sh`), the API server's scheduler triggers skills on a cron schedule. Default schedules (all disabled by default):

| Schedule | Skill | Default Time |
|----------|-------|-------------|
| Daily Inbox Check | `/inbox` | Weekdays 8am |
| Daily Job Scout | `/scout` | Weekdays 7am |
| Daily LinkedIn Engagement | `/linkedin` | Weekdays 9am |
| Networking Follow-ups | `/network` | Mon & Thu 10am |
| Interview Prep Reminder | `/prep` | Daily 6pm |
| Weekly Blog Ideas | `/blog-ideas` | Monday 10am |
| Draft Publish Reminder | `/blog-status` | Friday 9am |

Enable them in the Dashboard's Schedules tab. Results are pushed to Telegram (if configured) so you can review and respond from your phone.

Scheduled jobs can ask you questions mid-run. For example, the scout skill might ask "Found 8 jobs. Save all or filter to top 5?" The question appears on Telegram, you reply, and the job continues with your answer.

See [automation.md](automation.md) for advanced configuration.

---

## Verification Checklist

After setup, verify each layer is working:

- [ ] `uv run python .claude/tools/db.py status` -- Supabase connection
- [ ] `http://localhost:5173` -- Dashboard loads
- [ ] `http://localhost:8000/api/schedules` -- API is running
- [ ] `/scout` in Claude Code -- skill execution works
- [ ] `uv run python .claude/tools/push_to_telegram.py send --text "test"` -- Telegram delivery (if configured)
- [ ] Send `/status` from Telegram -- handler responds (if configured)

---

## Troubleshooting

### "uv not found"
Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Supabase connection fails
Check `.env` has the correct `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. The service role key (not anon key) is needed for the CLI tools.

### Scheduled jobs don't run
- Verify the API server is running: `curl http://localhost:8000/api/schedules`
- Check schedules are enabled in the Schedules tab
- Check tmux: `tmux attach -t artemis`

### Telegram messages not arriving
- Verify bot token: `uv run python .claude/tools/push_to_telegram.py send --text "test"`
- Check the handler session is running: look for the `telegram` window in tmux
- Make sure `enabledPlugins` in `.claude/settings.json` is empty (the handler manages the plugin)

### Gmail/Calendar not available in scheduled jobs
These skills require interactive Claude sessions. The scheduler handles this automatically by running inbox-related skills in interactive mode. If you see OAuth errors, verify the integrations are enabled in Claude Code settings.

### Two sessions fighting for Telegram
Only one process can poll Telegram's `getUpdates` at a time. If both your main Claude session and the handler are trying to use the Telegram plugin, you'll see missed messages. The fix: ensure `.claude/settings.json` has `"enabledPlugins": {}` (empty). Only the handler session should have the plugin, passed via its `--settings` flag.
