"""CLI entry point — argparse setup and command dispatch."""

import argparse
import subprocess
import sys
from pathlib import Path


def _run_state_sync(flag):
    """Delegate state sync to tools/state_sync.py."""
    tools_dir = Path(__file__).resolve().parent.parent
    project_root = tools_dir.parent
    subprocess.run(
        ["uv", "run", "python", str(tools_dir / "state_sync.py"), flag],
        cwd=str(project_root),
    )

from db_modules.jobs import add_job, list_jobs, update_job, get_job, save_application, mark_submitted, score_job, merge_jobs, find_job
from db_modules.companies import add_company, list_companies
from db_modules.contacts import batch_add_contacts, find_contact, update_contact
from db_modules.batch import batch_update, batch_add
from db_modules.engagements import add_engagement, update_engagement, list_engagements
from db_modules.blog import add_blog_post, update_blog_post, batch_import_blog_posts, list_blog_posts
from db_modules.status import status
from db_modules.tasks import next_task, update_task, list_tasks, notify_refresh


def main():
    parser = argparse.ArgumentParser(description="Artemis DB Helper")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add-job
    p = subparsers.add_parser("add-job", help="Add a job to the pipeline")
    p.add_argument("--title", required=True)
    p.add_argument("--company", required=True)
    p.add_argument("--url", default="")
    p.add_argument("--description", default="")
    p.add_argument("--status", default="scouted")
    p.add_argument("--source", default="scout")
    p.add_argument("--match-score", type=int, default=None)
    p.set_defaults(func=add_job)

    # list-jobs
    p = subparsers.add_parser("list-jobs", help="List jobs in the pipeline")
    p.add_argument("--status", default=None, help="Filter by status")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=list_jobs)

    # update-job
    p = subparsers.add_parser("update-job", help="Update a job")
    p.add_argument("--id", required=True)
    p.add_argument("--status", default=None)
    p.add_argument("--match-score", type=int, default=None)
    p.add_argument("--reason", default=None, help="Reason for not interested / rejection")
    p.add_argument("--analysis-file", default=None, help="Path to markdown file containing the analysis text")
    p.set_defaults(func=update_job)

    # get-job
    p = subparsers.add_parser("get-job", help="Get full details of a job")
    p.add_argument("--id", required=True)
    p.set_defaults(func=get_job)

    # add-company
    p = subparsers.add_parser("add-company", help="Add a target company")
    p.add_argument("--name", required=True)
    p.add_argument("--domain", default="")
    p.add_argument("--careers-url", default="")
    p.add_argument("--why", default="")
    p.add_argument("--priority", default="medium", choices=["high", "medium", "low"])
    p.set_defaults(func=add_company)

    # list-companies
    p = subparsers.add_parser("list-companies", help="List target companies")
    p.add_argument("--all", action="store_true", help="Show all companies, not just targets")
    p.set_defaults(func=list_companies)

    # score-job (convenience for single scoring)
    p = subparsers.add_parser("score-job", help="Set match score for a job")
    p.add_argument("--id", required=True)
    p.add_argument("--score", type=int, required=True, help="Match score 0-100")
    p.set_defaults(func=lambda args: score_job(args))

    # find-job
    p = subparsers.add_parser("find-job",
                               help="Search for jobs by company+title. Returns JSON. Use before add-job to check for duplicates and rejected entries.")
    p.add_argument("--company", default=None, help="Company name (partial match, case-insensitive)")
    p.add_argument("--title", default=None, help="Title fragment (partial match, case-insensitive)")
    p.set_defaults(func=find_job)

    # merge-jobs
    p = subparsers.add_parser("merge-jobs", help="Merge two jobs: keep one, absorb the other")
    p.add_argument("--keep", required=True, help="UUID of the job to keep")
    p.add_argument("--merge", required=True, help="UUID of the job to absorb and delete")
    p.set_defaults(func=merge_jobs)

    # batch-update (JSON via stdin)
    p = subparsers.add_parser("batch-update", help="Batch update jobs from JSON on stdin")
    p.set_defaults(func=batch_update)

    # batch-add (JSON via stdin)
    p = subparsers.add_parser("batch-add", help="Batch add jobs from JSON on stdin")
    p.set_defaults(func=batch_add)

    # batch-add-contacts (JSON via stdin)
    p = subparsers.add_parser("batch-add-contacts",
                              help="Batch add/update contacts from JSON on stdin. "
                                   "See docstring for full schema.")
    p.set_defaults(func=batch_add_contacts)

    # find-contact
    p = subparsers.add_parser("find-contact",
                               help="Search for contacts by name, company, or LinkedIn URL. Returns JSON.")
    p.add_argument("--name", default=None, help="Name (partial match, case-insensitive)")
    p.add_argument("--company", default=None, help="Company name (partial match, case-insensitive)")
    p.add_argument("--linkedin-url", default=None, help="LinkedIn URL (partial match)")
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(func=find_contact)

    # update-contact
    p = subparsers.add_parser("update-contact", help="Update a contact's status or notes")
    p.add_argument("--id", default=None, help="Contact UUID")
    p.add_argument("--linkedin-url", default=None, help="LinkedIn URL (used as lookup key)")
    p.add_argument("--status", default=None,
                   choices=["identified", "draft_ready", "sent", "connected",
                            "responded", "meeting_scheduled", "warm"],
                   help="New outreach status")
    p.add_argument("--notes", default=None, help="Replace notes field")
    p.add_argument("--message", default=None, help="Replace outreach_message_md field")
    p.add_argument("--last-contacted", default=None, help="ISO timestamp of last contact")
    p.set_defaults(func=update_contact)

    # save-application
    p = subparsers.add_parser("save-application", help="Save application materials to DB")
    p.add_argument("--id", required=True)
    p.add_argument("--resume", help="Path to resume markdown file")
    p.add_argument("--cover-letter", help="Path to cover letter markdown file")
    p.add_argument("--primer", help="Path to primer markdown file")
    p.add_argument("--form-fills", default=None, help="Path to form fills markdown file")
    p.add_argument("--pdf-path", default=None, help="Path to generated resume PDF")
    p.set_defaults(func=save_application)

    # mark-submitted
    p = subparsers.add_parser("mark-submitted", help="Mark application as submitted and advance job to 'applied'")
    p.add_argument("--id", required=True, help="Job UUID")
    p.set_defaults(func=mark_submitted)

    # status
    p = subparsers.add_parser("status", help="Show pipeline dashboard")
    p.set_defaults(func=status)

    # add-engagement
    p = subparsers.add_parser("add-engagement", help="Log an engagement action")
    p.add_argument("--action-type", required=True,
                   help="like, comment, share, connection_request, blog_post")
    p.add_argument("--platform", default="linkedin", help="linkedin, medium, personal_blog")
    p.add_argument("--target-url", default=None)
    p.add_argument("--target-person", default=None)
    p.add_argument("--content", default=None, help="Comment text or share note")
    p.add_argument("--status", default="drafted", choices=["drafted", "approved", "posted", "skipped"])
    p.set_defaults(func=add_engagement)

    # update-engagement
    p = subparsers.add_parser("update-engagement", help="Update an engagement's status")
    p.add_argument("--id", required=True)
    p.add_argument("--status", choices=["drafted", "approved", "posted", "skipped"])
    p.add_argument("--content", default=None)
    p.add_argument("--target-person", default=None)
    p.set_defaults(func=update_engagement)

    # list-engagements
    p = subparsers.add_parser("list-engagements", help="List engagement actions")
    p.add_argument("--platform", default=None)
    p.add_argument("--status", default=None)
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(func=list_engagements)

    # add-blog-post
    p = subparsers.add_parser("add-blog-post", help="Add a blog post idea or draft")
    p.add_argument("--title", required=True)
    p.add_argument("--slug", required=True, help="URL-friendly slug")
    p.add_argument("--status", default="idea", choices=["idea", "draft", "review", "published"])
    p.add_argument("--platform", default=None, help="linkedin, medium, personal")
    p.add_argument("--tags", default=None, help="Comma-separated tags")
    p.add_argument("--summary", default=None, help="Brief description of the post angle")
    p.add_argument("--draft-path", default=None, help="Path to local draft markdown")
    p.add_argument("--content", default=None, help="Full markdown body of the post")
    p.set_defaults(func=add_blog_post)

    # update-blog-post
    p = subparsers.add_parser("update-blog-post", help="Update a blog post")
    p.add_argument("--id", required=True)
    p.add_argument("--status", default=None, choices=["idea", "draft", "review", "published"])
    p.add_argument("--platform", default=None)
    p.add_argument("--published-url", default=None)
    p.add_argument("--draft-path", default=None)
    p.add_argument("--tags", default=None, help="Comma-separated tags")
    p.add_argument("--content", default=None, help="Full markdown body of the post")
    p.set_defaults(func=update_blog_post)

    # batch-import-blog-posts
    p = subparsers.add_parser("batch-import-blog-posts", help="Batch import/upsert blog posts from JSON on stdin")
    p.set_defaults(func=batch_import_blog_posts)

    # list-blog-posts
    p = subparsers.add_parser("list-blog-posts", help="List blog posts")
    p.add_argument("--status", default=None)
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(func=list_blog_posts)

    # next-task
    p = subparsers.add_parser("next-task", help="Claim and return oldest queued task as JSON")
    p.set_defaults(func=next_task)

    # update-task
    p = subparsers.add_parser("update-task", help="Update a task's status/output/error")
    p.add_argument("--id", required=True, help="Task UUID")
    p.add_argument("--status", default=None, choices=["queued", "running", "complete", "failed"])
    p.add_argument("--output-summary", default=None, help="Summary of task output")
    p.add_argument("--error", default=None, help="Error message if failed")
    p.set_defaults(func=update_task)

    # list-tasks
    p = subparsers.add_parser("list-tasks", help="List recent tasks from queue")
    p.add_argument("--status", default=None, choices=["queued", "running", "complete", "failed"])
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(func=list_tasks)

    # notify-refresh
    p = subparsers.add_parser("notify-refresh",
                               help="Signal the UI to refresh specific tables (best-effort)")
    p.add_argument("--tables", default="",
                   help="Comma-separated table names (e.g. tasks,scheduled_jobs). "
                        "Omit to trigger a full refresh.")
    p.set_defaults(func=notify_refresh)

    # state-pull
    p = subparsers.add_parser("state-pull", help="Pull state files from DB (newer wins)")
    p.set_defaults(func=lambda args: _run_state_sync("--pull"))

    # state-push
    p = subparsers.add_parser("state-push", help="Push state files to DB (newer wins)")
    p.set_defaults(func=lambda args: _run_state_sync("--push"))

    # state-seed
    p = subparsers.add_parser("state-seed", help="Force-push all local state to DB")
    p.set_defaults(func=lambda args: _run_state_sync("--seed"))

    # state-check
    p = subparsers.add_parser("state-check", help="Report state sync status")
    p.set_defaults(func=lambda args: _run_state_sync("--check"))

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)
