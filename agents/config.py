"""
Project Artemis — Application settings loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration. Values are loaded from .env or environment."""

    # ── LLM ─────────────────────────────────────────────────────
    google_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # ── Supabase ────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # ── ChromaDB ────────────────────────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_persist_dir: str = "./data/chroma"

    # ── GitHub ──────────────────────────────────────────────────
    github_token: str = ""
    github_username: str = "ajansen7"

    # ── Google Workspace ────────────────────────────────────────
    google_credentials_path: str = "./credentials/google_oauth.json"

    # ── External APIs ───────────────────────────────────────────
    proxycurl_api_key: str = ""
    firecrawl_api_key: str = ""
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    serper_api_key: str = ""

    # ── Discord ─────────────────────────────────────────────────
    discord_bot_token: str = ""
    discord_guild_id: str = ""

    # ── Cost Controls ───────────────────────────────────────────
    max_daily_llm_spend_usd: float = 2.00
    max_weekly_proxycurl_lookups: int = 50

    # ── App ─────────────────────────────────────────────────────
    log_level: str = "INFO"
    environment: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton instance — import this throughout the app
settings = Settings()
