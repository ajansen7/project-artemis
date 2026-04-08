"""Supabase client initialization — shared across all db_modules."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Load .env from project root (tools/db_modules/ is 2 levels below root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
