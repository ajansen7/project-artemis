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
