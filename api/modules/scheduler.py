import os
import shlex
import threading
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.modules.config import (
    CLAUDE_BIN, INTERACTIVE_SKILLS, PROJECT_ROOT, logger,
)
from api.modules.relay_queue import relay_queue
from api.modules.task_manager import task_manager
from api.modules.telegram import _send_telegram, _send_telegram_sync

scheduler = AsyncIOScheduler()
_schedule_job_ids: dict[str, str] = {}  # DB id -> APScheduler job id


_RELAY_INSTRUCTIONS = """

## IMPORTANT: You Are Running as a Background Task

You are running headless in a tmux window. The user CANNOT see your terminal output.
The ONLY way to communicate with the user is via the tools below.
Always send output to Telegram — never assume the user will check tmux.

## Telegram Output

Send curated results to the user's phone using the push tool:

    uv run python .claude/tools/push_to_telegram.py summary --job-name "{job_name}" --status success --body "Your summary here"

For longer output, pipe via stdin:

    echo "detailed findings..." | uv run python .claude/tools/push_to_telegram.py send --stdin

Format for mobile: short lines, numbered lists for actions, bold for titles. Keep under 4000 chars.
- Send progress updates for long-running operations (not just the final summary).
- At the end of your run, always send a summary of what you did and any pending actions.

## Relay (Ask the User)

If you need user input during this job (e.g., to confirm an action, choose between options,
or get approval before proceeding), use the relay tool:

    uv run python .claude/tools/relay_ask.py --job-name "{job_name}" --skill "{skill}" --question "Your question here" --timeout 300

The tool blocks until the user replies (via Telegram) or the timeout expires (default 5 min).
- Normal reply text → use it as the user's answer and continue.
- RELAY_TIMEOUT → the user did not respond. Proceed with the safest default: skip the
  action, save a draft for later review, or note it for the next run. Do not halt the job.
- Only ask questions that genuinely require a decision. Routine operations should not prompt.
"""


def _build_skill_command(skill: str, skill_args: str | None = None, job_name: str | None = None) -> list[str]:
    """Build the Claude CLI command for a skill invocation.

    Interactive skills (inbox, schedule, etc.) run without -p so Claude starts
    in interactive mode and inherits Claude.ai OAuth MCP connections. The prompt
    is passed via a bash here-string (<<<) so the session is still non-blocking.

    When job_name is provided (scheduled jobs), relay instructions are appended
    so the subprocess can ask the user questions via Telegram mid-job.
    """
    skill_name = skill.lstrip("/")
    skill_cmd = f"/{skill_name}"
    if skill_args:
        prompt = f"Follow the instructions for the `{skill_cmd}` command in SKILL.md for '{skill_args}'."
    else:
        prompt = f"Follow the instructions for the `{skill_cmd}` command in SKILL.md."

    if job_name:
        prompt += _RELAY_INSTRUCTIONS.format(job_name=job_name, skill=skill_name)

    extra_flags = [
        "--dangerously-skip-permissions",
        "--add-dir", os.path.join(PROJECT_ROOT, ".claude", "skills", "interview-coach"),
    ]
    portfolio_path = os.environ.get("PORTFOLIO_PATH")
    if portfolio_path:
        extra_flags.extend(["--add-dir", portfolio_path])

    if skill_name in INTERACTIVE_SKILLS:
        # Interactive mode (no -p) so Claude.ai OAuth MCPs (Gmail, Calendar) load.
        # Uses <<< (here-string) for the prompt. Interactive Claude doesn't exit on
        # stdin EOF, so _poll_and_notify handles idle detection and kills the process.
        claude_cmd = shlex.join([CLAUDE_BIN, *extra_flags])
        return ["sh", "-c", f"{claude_cmd} <<< {shlex.quote(prompt)}"]

    return [CLAUDE_BIN, "-p", prompt, "--verbose", *extra_flags]


async def _notify_relay_telegram(job_name: str, skill: str, question: str, token: str):
    """Send a relay question directly to Telegram via Bot API."""
    tg_msg = f"\u2753 {job_name} needs your input:\n\n{question}\n\nReply here and I'll relay your answer back."
    await _send_telegram(tg_msg)


def _poll_and_notify(task_id: str, job_name: str, skill: str, schedule_id: str | None = None):
    """
    Poll a task to completion, then fire the webhook and optionally update
    the scheduled_jobs DB row.  Runs synchronously (call from a thread).

    Interactive Claude sessions don't exit on stdin EOF, so we detect idle
    output (no change for IDLE_KILL seconds) and kill the process.  Pending
    relay questions suppress idle-kill so the user has time to respond.
    """
    import time
    from api.modules.config import _get_supabase

    IDLE_KILL = 600  # seconds of unchanged output before killing
    HARD_TIMEOUT = 1800  # 30 min absolute ceiling

    last_output = ""
    idle_seconds = 0

    for tick in range(HARD_TIMEOUT // 5):
        time.sleep(5)
        task = task_manager.get(task_id)
        if task and task.status != "running":
            break

        # Idle detection: if output hasn't changed and no relay is pending,
        # assume Claude finished but didn't exit.
        if task:
            current_output = task.tail_output(40)
            if current_output and current_output == last_output:
                idle_seconds += 5
                has_pending_relay = any(
                    e.job_name == job_name for e in relay_queue.pending()
                )
                if idle_seconds >= IDLE_KILL and not has_pending_relay:
                    logger.info("Task %s idle for %ds — killing", task_id, idle_seconds)
                    # Capture output BEFORE killing the window
                    task._idle_output = task.tail_output(40)
                    task_manager.kill(task_id)
                    task.status = "complete"  # treat as success — work was done
                    break
            else:
                idle_seconds = 0
                last_output = current_output
    else:
        task = task_manager.get(task_id)

    final_status = "success" if (task and task.status == "complete") else "failed"
    # Use pre-kill capture if available (idle-killed tasks), otherwise capture now
    tail = getattr(task, "_idle_output", None) or (task.tail_output(40) if task else None)
    error_msg = tail if final_status == "failed" else None

    # Update schedule row if this was a scheduled/manual-trigger run
    if schedule_id:
        try:
            sb = _get_supabase()
            sb.table("scheduled_jobs").update({
                "last_status": final_status,
                "last_error": error_msg,
            }).eq("id", schedule_id).execute()
        except Exception:
            pass

    # Send fallback completion notification to Telegram (safety net in case
    # the job didn't call push_to_telegram.py itself)
    if tail:
        status_icon = "\u2705" if final_status == "success" else "\u274c"
        tg_msg = f"{status_icon} {job_name}\n\n{tail}"
        if len(tg_msg) > 4000:
            tg_msg = tg_msg[:4000] + "\n\n(truncated)"
        _send_telegram_sync(tg_msg)


def _run_scheduled_job(schedule_id: str, name: str, skill: str, skill_args: str | None):
    """
    Synchronous callback for APScheduler. Launches the skill in tmux,
    polls for completion, then updates DB and sends Telegram notification.
    """
    from api.modules.config import _get_supabase

    sb = _get_supabase()

    # Mark running
    sb.table("scheduled_jobs").update({
        "last_status": "running",
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_error": None,
    }).eq("id", schedule_id).execute()

    command = _build_skill_command(skill, skill_args, job_name=name)
    task_id = task_manager.start(f"Scheduled: {name}", command)

    _poll_and_notify(task_id, name, skill, schedule_id=schedule_id)


def _register_schedule(row: dict):
    """Register a single DB row with APScheduler."""
    schedule_id = row["id"]
    try:
        trigger = CronTrigger.from_crontab(row["cron_expr"], timezone="America/Denver")
    except ValueError as exc:
        logger.warning("Invalid cron for schedule %s: %s", schedule_id, exc)
        return

    job = scheduler.add_job(
        _run_scheduled_job,
        trigger=trigger,
        args=[schedule_id, row["name"], row["skill"], row.get("skill_args")],
        id=f"schedule_{schedule_id}",
        replace_existing=True,
    )
    _schedule_job_ids[schedule_id] = job.id


def _unregister_schedule(schedule_id: str):
    """Remove a schedule from APScheduler."""
    job_id = _schedule_job_ids.pop(schedule_id, None)
    if job_id:
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass


def _load_all_schedules():
    """Load all enabled schedules from Supabase into APScheduler."""
    from api.modules.config import _get_supabase

    try:
        sb = _get_supabase()
        res = sb.table("scheduled_jobs").select("*").eq("enabled", True).execute()
        for row in res.data or []:
            _register_schedule(row)
        logger.info("Loaded %d enabled schedules", len(res.data or []))
    except Exception as exc:
        logger.warning("Could not load schedules: %s", exc)
