import asyncio

import httpx

from api.modules.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, logger


async def _send_telegram(text: str, chat_id: str | None = None):
    """Send a message directly via the Telegram Bot API (best-effort)."""
    token = TELEGRAM_BOT_TOKEN
    cid = chat_id or TELEGRAM_CHAT_ID
    if not token or not cid:
        logger.debug("Telegram not configured — skipping send")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": cid, "text": text},
            )
    except Exception as exc:
        logger.debug("Telegram send failed (non-fatal): %s", exc)


def _send_telegram_sync(text: str, chat_id: str | None = None):
    """Synchronous wrapper for _send_telegram (for use from threads)."""
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_send_telegram(text, chat_id))
        loop.close()
    except Exception:
        pass
