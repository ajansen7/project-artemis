#!/usr/bin/env python3
"""
Artemis Artifact Sync — sync generated PDFs/DOCXs to/from Supabase Storage.

Manages binary artifacts (resumes, cover letters) in the cloud so they're
available on any machine without manual export/import.

Usage:
    uv run python tools/artifact_sync.py --pull                 # all artifacts
    uv run python tools/artifact_sync.py --pull --job-id <uuid> # specific job
    uv run python tools/artifact_sync.py --push                 # upload local artifacts not in storage
    uv run python tools/artifact_sync.py --list                 # show what's in storage vs local
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sb = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))

OUTPUT_DIR = PROJECT_ROOT / "output" / "applications"
STORAGE_BUCKET = "artifacts"


def _job_slug(job_id: str, company: str = "", title: str = "") -> str:
    """Generate storage slug: {job-slug}"""
    import re
    if company or title:
        slug = f"{company}-{title}".lower()
    else:
        slug = job_id[:12]
    return re.sub(r"[^a-z0-9-]", "-", slug)[:50].strip("-")


def _list_storage_artifacts() -> dict[str, list[str]]:
    """List all artifacts in storage. Returns {job_slug: [file_paths]}."""
    try:
        objects = sb.storage.from_(STORAGE_BUCKET).list("applications")
        artifacts = {}
        for obj in objects:
            path = obj.get("name", "")
            if "/" in path:
                job_slug = path.split("/")[0]
                artifacts.setdefault(job_slug, []).append(path)
        return artifacts
    except Exception as e:
        print(f"WARNING: Could not list storage: {e}", file=sys.stderr)
        return {}


def _list_local_artifacts() -> dict[str, list[Path]]:
    """List all local artifacts in output/applications/. Returns {dir_name: [file_paths]}."""
    local = {}
    if OUTPUT_DIR.exists():
        for job_dir in OUTPUT_DIR.iterdir():
            if job_dir.is_dir():
                files = [f for f in job_dir.glob("*") if f.is_file()]
                if files:
                    local[job_dir.name] = files
    return local


def _storage_path(job_slug: str, filename: str) -> str:
    """Build Supabase Storage path: applications/{job_slug}/{filename}"""
    return f"applications/{job_slug}/{filename}"


def pull(job_id: str = None):
    """Pull artifacts from storage to local."""
    storage = _list_storage_artifacts()
    if not storage:
        print("No artifacts in storage.")
        return

    pulled = []
    for job_slug, paths in storage.items():
        for path in paths:
            filename = path.split("/")[-1]
            job_dir = OUTPUT_DIR / job_slug
            job_dir.mkdir(parents=True, exist_ok=True)
            local_file = job_dir / filename

            try:
                content = sb.storage.from_(STORAGE_BUCKET).download(path)
                local_file.write_bytes(content)
                pulled.append(str(local_file))
            except Exception as e:
                print(f"WARNING: Could not download {path}: {e}", file=sys.stderr)

    if pulled:
        print(f"Pulled {len(pulled)} artifact(s):")
        for p in pulled:
            print(f"  {p}")


def push():
    """Push local artifacts not in storage."""
    local = _list_local_artifacts()
    storage = _list_storage_artifacts()

    pushed = []
    for job_slug, files in local.items():
        storage_files = set(
            p.split("/")[-1] for p in storage.get(job_slug, [])
        )

        for filepath in files:
            if filepath.name not in storage_files:
                path = _storage_path(job_slug, filepath.name)
                try:
                    with open(filepath, "rb") as f:
                        sb.storage.from_(STORAGE_BUCKET).upload(path, f.read())
                    pushed.append(path)
                except Exception as e:
                    print(f"WARNING: Could not upload {path}: {e}", file=sys.stderr)

    if pushed:
        print(f"Pushed {len(pushed)} artifact(s):")
        for p in pushed:
            print(f"  {p}")
    else:
        print("No new artifacts to push.")


def list_artifacts():
    """Show what's in storage vs local."""
    local = _list_local_artifacts()
    storage = _list_storage_artifacts()

    all_slugs = set(local.keys()) | set(storage.keys())

    if not all_slugs:
        print("No artifacts found.")
        return

    print("\nLocal vs Storage:")
    print("-" * 60)
    for slug in sorted(all_slugs):
        local_files = {f.name for f in local.get(slug, [])}
        storage_files = {p.split("/")[-1] for p in storage.get(slug, [])}

        all_files = sorted(local_files | storage_files)
        for filename in all_files:
            in_local = "✓" if filename in local_files else " "
            in_storage = "✓" if filename in storage_files else " "
            print(f"  [{in_local}] [{in_storage}]  {slug}/{filename}")

    print("\nLegend: [Local] [Storage]")


def main():
    parser = argparse.ArgumentParser(description="Artemis Artifact Sync")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pull", action="store_true", help="Pull artifacts from storage")
    group.add_argument("--push", action="store_true", help="Push local artifacts to storage")
    group.add_argument("--list", action="store_true", help="List artifacts (local vs storage)")
    parser.add_argument("--job-id", default=None, help="Filter to specific job (pull only)")
    args = parser.parse_args()

    if args.pull:
        pull(args.job_id)
    elif args.push:
        push()
    elif args.list:
        list_artifacts()


if __name__ == "__main__":
    main()
