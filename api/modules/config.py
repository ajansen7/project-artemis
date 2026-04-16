import asyncio
import json
import logging
import os
from base64 import urlsafe_b64decode
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException, Request

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger("artemis.api")

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])


_supabase_client = None


def _get_supabase():
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise HTTPException(status_code=500, detail="Supabase credentials not configured.")
        _supabase_client = create_client(url, key)
    return _supabase_client


async def run_db(fn):
    """Run a synchronous Supabase call in a thread pool.

    The sync httpx client blocks on DNS resolution when called directly from an
    async handler on Python 3.14+/macOS. Running it in a thread avoids that.
    """
    return await asyncio.to_thread(fn)


def get_user_id_from_request(request: Request) -> str:
    """Extract user_id from JWT token in Authorization header.

    Supabase JWTs have the user_id in the 'sub' claim.
    Returns the user_id or raises HTTPException if not found.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]  # Remove "Bearer " prefix
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        # Decode payload (add padding if needed)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding

        decoded = urlsafe_b64decode(payload)
        claims = json.loads(decoded)
        user_id = claims.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID")

        return user_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to decode JWT: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token")
