"""SSE push and notify endpoints for real-time UI refresh."""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# In-memory registry of connected SSE clients (one asyncio.Queue per client)
_clients: set[asyncio.Queue] = set()


class NotifyPayload(BaseModel):
    event: str
    data: dict = {}


@router.get("/api/events")
async def sse_stream():
    """SSE endpoint — browsers connect here to receive push notifications."""
    queue: asyncio.Queue = asyncio.Queue()
    _clients.add(queue)

    async def generate():
        try:
            yield "data: {\"event\": \"hello\"}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            _clients.discard(queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/api/notify")
async def notify(payload: NotifyPayload):
    """Broadcast a refresh event to all connected SSE clients."""
    msg = json.dumps({"event": payload.event, "data": payload.data})
    for q in list(_clients):
        await q.put(msg)
    return {"sent": len(_clients)}
