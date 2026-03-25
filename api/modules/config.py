import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger("artemis.api")

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])


def _get_supabase():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured.")
    return create_client(url, key)


async def run_db(fn):
    """Run a synchronous Supabase call in a thread pool.

    The sync httpx client blocks on DNS resolution when called directly from an
    async handler on Python 3.14+/macOS. Running it in a thread avoids that.
    """
    return await asyncio.to_thread(fn)
