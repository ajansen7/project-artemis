#!/usr/bin/env python3
"""
Relay Ask — send a question to the user via Telegram and wait for a reply.

Called by scheduled Claude subprocesses when they need user input mid-job.
The question is relayed through the Artemis API → webhook → main Claude
session → Telegram. The user replies on Telegram and the answer flows back.

Usage:
    uv run python .claude/tools/relay_ask.py \
        --job-name "Morning Scout" --skill "scout" \
        --question "Found 8 jobs. Save all or filter?" \
        --timeout 1800

Exit codes:
    0 — answer received (or timeout, printed as RELAY_TIMEOUT)
    1 — connection error
"""

import argparse
import sys
import time

import httpx

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Relay a question to the user via Telegram")
    parser.add_argument("--job-name", required=True, help="Name of the scheduled job")
    parser.add_argument("--skill", required=True, help="Skill that is asking")
    parser.add_argument("--question", required=True, help="Question for the user")
    parser.add_argument("--timeout", type=int, default=1800, help="Seconds to wait (default 1800)")
    parser.add_argument("--api-base", default=API_BASE, help="Artemis API base URL")
    args = parser.parse_args()

    base = args.api_base.rstrip("/")

    # Post the question
    try:
        resp = httpx.post(
            f"{base}/api/relay/ask",
            json={"job_name": args.job_name, "skill": args.skill, "question": args.question},
            timeout=10.0,
        )
        resp.raise_for_status()
        token = resp.json()["token"]
    except Exception as exc:
        print(f"RELAY_ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # Poll for the answer
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        time.sleep(3)
        try:
            resp = httpx.get(f"{base}/api/relay/answer/{token}", timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue  # transient error, keep polling

        if data["status"] == "answered":
            print(data["answer"])
            return
        if data["status"] == "expired":
            print("RELAY_TIMEOUT")
            return

    # Local timeout
    print("RELAY_TIMEOUT")


if __name__ == "__main__":
    main()
