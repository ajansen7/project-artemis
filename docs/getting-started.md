# Getting Started with Artemis

This guide walks you through setting up Artemis from scratch, including all optional integrations.

---

## Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Node.js 18+** and **npm** (for the dashboard)
- **[Bun](https://bun.sh)** runtime (used by the channels webhook layer)
  ```bash
  curl -fsSL https://bun.sh/install | bash
  ```
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)**
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
- **tmux** (`brew install tmux`)
- **Supabase** project ([supabase.com](https://supabase.com), free tier works)

Optional:
- **LibreOffice** for PDF resume generation: `brew install --cask libreoffice`

---

## Step 1: Clone and Run Setup

```bash
git clone <repo-url> project-artemis
cd project-artemis
./scripts/setup.sh
```

The setup script handles everything:
- Checks prerequisites (Python 3.11+, uv, Node.js, Bun, tmux, Claude Code)
- Initializes git submodules (interview-coach)
- Installs Python, Node, and Bun dependencies
- Creates `.env` from template and prompts for Supabase credentials
- Verifies the Supabase connection

### Supabase Setup

Before running setup, create a Supabase project:

1. Create a project at [supabase.com](https://supabase.com)
2. Go to the SQL Editor and run migrations in order: `db/migrations/001_*.sql` through `db/migrations/017_*.sql`
3. Have your Supabase URL, anon key, and service role key ready for the setup script

If you skipped entering credentials during setup, edit `.env` manually:
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

## Step 2: Run the Profile Setup Wizard

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

## Step 3: Start Services

```bash
./scripts/start.sh
```

This creates a tmux session called `artemis` with three windows:

| Window | Service | What It Does |
|--------|---------|-------------|
| `api` | FastAPI (port 8000) | Backend: scheduler, task queue, PDF generation |
| `frontend` | Vite (port 5173) | React dashboard |
| `orchestrator` | Claude CLI session | Unified Telegram interface + task executor |

The startup output shows both localhost and local-network URLs:
```
Artemis is running:
  API:       http://localhost:8000
  Dashboard: http://localhost:5173

On your local network:
  API:       http://192.168.1.x:8000
  Dashboard: http://192.168.1.x:5173
```

Open the local-network URL on your phone or any device on the same Wi-Fi to access the dashboard without any extra configuration.

Useful commands:
```bash
tmux attach -t artemis          # see all windows
./scripts/stop.sh               # stop services, keep tmux session
./scripts/stop.sh --kill        # kill everything
./scripts/start.sh --no-frontend  # skip the dashboard
```

---

## Step 4: Configure the Dashboard

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

### 5e. Start the Orchestrator

The orchestrator is started automatically by `./scripts/start.sh`. It runs as a single long-running Claude session that handles both Telegram messages and skill execution. There is no separate "Telegram handler" — the orchestrator does both.

Once running, you can message your bot from Telegram:
- `/scout` -- kicks off a job scouting run
- `/inbox` -- scans Gmail for recruiter activity
- `/status` -- shows your pipeline overview
- `/prep <company>` -- generates interview prep for a company

The Telegram plugin is enabled in `.claude/settings.json` so it loads automatically in the orchestrator session. Your main interactive Claude session does not use the Telegram plugin — only the orchestrator does.

---

## Optional: Gmail and Calendar MCP

These enable the `/inbox` skill (scanning for recruiter emails, interview scheduling, follow-up drafting).

Gmail and Calendar are Claude.ai OAuth integrations added directly through Claude Code.

1. In a Claude Code session, run:
   ```
   /mcp
   ```
   This opens the MCP management panel.

2. Search for **Gmail** and **Google Calendar** in the integrations list and click **Connect** on each.

3. Complete the Google OAuth flow in the browser window that opens. You'll be asked to grant read/compose access to Gmail and read/write access to Calendar.

4. Verify the connection — in Claude Code, ask:
   ```
   List my Gmail labels
   ```
   If it returns label names, the integration is live. Then run `/inbox` to confirm the skill works end-to-end.

These integrations are only available in interactive Claude sessions (not headless `-p` mode). Scheduled jobs that need Gmail/Calendar run in interactive mode automatically.

---

## Optional: Claude in Chrome MCP

This enables the `/linkedin` and `/blogger` skills (LinkedIn browsing, engagement drafting, blog publishing).

### Install the extension

1. Install [Claude in Chrome](https://chromewebstore.google.com/detail/claude-in-chrome) from the Chrome Web Store
2. Click the extension icon in Chrome's toolbar and sign in with the same Anthropic account you use for Claude Code
3. Make sure Chrome is open and the extension is active before starting a Claude Code session that needs it

### Connect it to Claude Code

4. In a Claude Code session, run `/mcp` and look for **Claude in Chrome** in the integrations list, then enable it

   Alternatively, Claude Code auto-detects the extension when Chrome is open — you'll see `mcp__claude-in-chrome__*` tools available in sessions where the extension is running.

5. Verify: in Claude Code, ask Claude to navigate to a URL. If it can control the browser tab, the connection is working.

6. Run `/linkedin` to confirm the full skill works.

**Note:** Chrome must be open with the extension active for browser tools to work. If you see "Extension not found" errors, reload the extension from `chrome://extensions` or restart Chrome.

---

## Optional: Supabase MCP

Direct database access for running migrations, ad-hoc queries, and schema changes without leaving Claude Code.

1. In a Claude Code session, run `/mcp` and connect the **Supabase** integration
2. When prompted, paste your Supabase project URL and service role key (same values from your `.env`)
3. Verify: ask Claude to list your tables — it should return the Artemis schema (jobs, contacts, applications, etc.)

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
- [ ] `http://localhost:5173` -- Dashboard loads (also test on your phone via the LAN URL printed by start.sh)
- [ ] `http://localhost:8000/api/schedules` -- API is running
- [ ] `/scout` in Claude Code -- skill execution works
- [ ] `curl -X POST http://127.0.0.1:8790/notify -H "Content-Type: application/json" -d '{"message":"ping"}'` -- artemis-channel is up (if services running)
- [ ] `uv run python .claude/tools/push_to_telegram.py send --text "test"` -- Telegram delivery (if configured)
- [ ] Send `/status` from Telegram -- orchestrator responds (if configured)

---

## Troubleshooting

### "uv not found"
Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Supabase connection fails
Check `.env` has the correct `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. The service role key (not anon key) is needed for the CLI tools.

### Scheduled jobs don't run
- Verify the API server is running: `curl http://localhost:8000/api/schedules`
- Check schedules are enabled in the Schedules tab
- Check that the orchestrator is running: `tmux attach -t artemis` and look for the `orchestrator` window
- Check the task queue: `uv run python .claude/tools/db.py list-tasks --status queued`

### Telegram messages not arriving
- Verify bot token: `uv run python .claude/tools/push_to_telegram.py send --text "test"`
- Check the orchestrator is running: look for the `orchestrator` window in tmux
- Confirm the Telegram plugin is listed: the orchestrator startup line should include `--channels plugin:telegram@claude-plugins-official`

### Tasks stuck in "queued"
- Check the artemis-channel is running: `curl -X POST http://127.0.0.1:8790/notify -H "Content-Type: application/json" -d '{"message":"test"}'` — should return "ok"
- If the channel is down, restart with `./scripts/stop.sh && ./scripts/start.sh`
- Tasks remain in Supabase even if the channel is down; the orchestrator will pick them up on next interaction

### Gmail/Calendar not available in scheduled jobs
These skills require an interactive Claude session with the Gmail/Calendar MCP connected. Verify the integrations are enabled in Claude Code's `/mcp` settings for your main interactive session. Scheduled jobs run through the orchestrator, which inherits MCP settings from the project's `.mcp.json`.
