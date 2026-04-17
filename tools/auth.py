#!/usr/bin/env python3
"""
Artemis Auth — manage JWT session for CLI/tools access.

Stores session in ~/.artemis/credentials.json. Auto-refreshes on expiry.

Usage:
    uv run python tools/auth.py signup             # create new account (requires SERVICE_ROLE_KEY)
    uv run python tools/auth.py login              # email+password sign-in
    uv run python tools/auth.py login --magic-link # email magic link sign-in
    uv run python tools/auth.py logout             # clear stored session
    uv run python tools/auth.py whoami             # show current user
    uv run python tools/auth.py refresh            # refresh expired token
"""

import argparse
import getpass
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

CREDS_FILE = Path.home() / ".artemis" / "credentials.json"


def _read_creds() -> dict:
    """Load stored credentials, or return empty dict."""
    if CREDS_FILE.exists():
        try:
            return json.loads(CREDS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_creds(creds: dict) -> None:
    """Save credentials to disk."""
    CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDS_FILE.write_text(json.dumps(creds, indent=2))
    CREDS_FILE.chmod(0o600)  # Only user can read


def _get_client():
    """Create Supabase client for auth operations."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def login(use_magic_link: bool = False):
    """Sign in via email/password or magic link."""
    sb = _get_client()

    email = input("Email: ").strip()
    if not email:
        print("❌ Email required")
        return

    if use_magic_link:
        try:
            res = sb.auth.sign_in_with_otp({"email": email})
            print(f"✅ Check your email for the magic link")
            return
        except Exception as e:
            print(f"❌ Magic link failed: {e}")
            sys.exit(1)
    else:
        password = getpass.getpass("Password: ")
        if not password:
            print("❌ Password required")
            return

        try:
            res = sb.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as e:
            print(f"❌ Sign-in failed: {e}")
            sys.exit(1)

    session = res.session
    user = res.user

    if not session or not session.access_token:
        print("❌ No session returned from sign-in")
        sys.exit(1)

    creds = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at,
        "user_id": user.id,
        "email": user.email,
        "signed_in_at": datetime.now(timezone.utc).isoformat(),
    }

    _save_creds(creds)
    print(f"✅ Signed in as {user.email}")

    _restart_orchestrator_if_running()


def logout():
    """Clear stored credentials."""
    if CREDS_FILE.exists():
        CREDS_FILE.unlink()
        print("✅ Signed out")
        _restart_orchestrator_if_running()
    else:
        print("⚠️  Not signed in")


def whoami():
    """Show current user."""
    creds = _read_creds()
    if not creds.get("user_id"):
        print("Not signed in")
        return

    print(f"User: {creds.get('email')}")
    print(f"ID: {creds.get('user_id')}")
    signed_in = creds.get("signed_in_at")
    if signed_in:
        print(f"Signed in: {signed_in}")


def refresh():
    """Refresh expired token."""
    creds = _read_creds()
    if not creds.get("refresh_token"):
        print("❌ Not signed in")
        sys.exit(1)

    sb = _get_client()
    try:
        res = sb.auth.refresh_session(creds["refresh_token"])
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
        sys.exit(1)

    session = res.session
    if not session or not session.access_token:
        print("❌ Refresh failed — please sign in again")
        sys.exit(1)

    creds.update({
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at,
    })

    _save_creds(creds)
    print(f"✅ Token refreshed for {creds.get('email')}")


def signup():
    """Create a new account (requires SUPABASE_SERVICE_ROLE_KEY)."""
    if not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY not set in .env — required for signup")
        print("   Contact your administrator to enable account creation")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email:
        print("❌ Email required")
        return

    while True:
        password = getpass.getpass("Password: ")
        if not password:
            print("❌ Password required")
            return
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            continue
        break

    # Create user via admin API
    try:
        sb_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        user_data = {
            "email": email,
            "password": password,
            "email_confirm": True,  # Skip email verification for CLI-managed accounts
        }
        user = sb_admin.auth.admin.create_user(user_data)
    except Exception as e:
        print(f"❌ Account creation failed: {e}")
        sys.exit(1)

    print(f"✅ Account created for {email}")
    print(f"   User ID: {user.user.id}")

    # Automatically sign in with the new account
    try:
        sb = _get_client()
        res = sb.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        print(f"⚠️  Account created but sign-in failed: {e}")
        print("   Try: artemis-login login")
        return

    session = res.session
    if not session or not session.access_token:
        print("⚠️  Account created but no session returned")
        return

    creds = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at,
        "user_id": user.user.id,
        "email": user.user.email,
        "signed_in_at": datetime.now(timezone.utc).isoformat(),
    }

    _save_creds(creds)
    print(f"✅ Signed in as {email}")

    _restart_orchestrator_if_running()


def _restart_orchestrator_if_running() -> None:
    """Restart orchestrator tmux window if artemis session is active."""
    result = subprocess.run(
        ["tmux", "list-windows", "-t", "artemis", "-F", "#{window_name}"],
        capture_output=True, text=True
    )
    if "orchestrator" in result.stdout.splitlines():
        print("Restarting orchestrator to apply new credentials...")
        script = PROJECT_ROOT / "scripts" / "restart-orchestrator.sh"
        subprocess.run(["bash", str(script)], check=False)


def main():
    parser = argparse.ArgumentParser(description="Artemis Auth — manage JWT session")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("signup", help="Create a new account (requires SERVICE_ROLE_KEY)")
    login_parser = subparsers.add_parser("login", help="Sign in with email/password")
    login_parser.add_argument("--magic-link", action="store_true", help="Use email magic link instead of password")

    subparsers.add_parser("logout", help="Clear stored credentials")
    subparsers.add_parser("whoami", help="Show current user")
    subparsers.add_parser("refresh", help="Refresh expired token")

    args = parser.parse_args()

    if args.command == "signup":
        signup()
    elif args.command == "login":
        login(args.magic_link if hasattr(args, "magic_link") else False)
    elif args.command == "logout":
        logout()
    elif args.command == "whoami":
        whoami()
    elif args.command == "refresh":
        refresh()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
