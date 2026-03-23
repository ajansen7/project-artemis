from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.modules.relay_queue import relay_queue
from api.modules.scheduler import _notify_relay_telegram

router = APIRouter()


class RelayAskRequest(BaseModel):
    job_name: str
    skill: str
    question: str


class RelayReplyRequest(BaseModel):
    token: str
    answer: str


@router.post("/api/relay/ask")
async def relay_ask(req: RelayAskRequest):
    """Called by relay_ask.py from a subprocess to send a question to the user."""
    token = relay_queue.ask(req.job_name, req.skill, req.question)
    await _notify_relay_telegram(req.job_name, req.skill, req.question, token)
    relay_queue.cleanup()  # housekeeping on each ask
    return {"token": token}


@router.get("/api/relay/answer/{token}")
async def relay_answer(token: str):
    """Polled by relay_ask.py waiting for the user's reply."""
    entry = relay_queue.get_answer(token)
    if entry is None:
        raise HTTPException(status_code=404, detail="Token not found")
    if entry.expired:
        return {"status": "expired", "token": token}
    if entry.answer is not None:
        return {"status": "answered", "token": token, "answer": entry.answer}
    return {"status": "pending", "token": token}


@router.get("/api/relay/pending")
async def relay_pending():
    """List pending (unanswered, unexpired) relay questions for the Telegram handler."""
    entries = relay_queue.pending()
    return {"pending": [
        {"token": e.token, "job_name": e.job_name, "skill": e.skill,
         "question": e.question, "created_at": e.created_at}
        for e in entries
    ]}


@router.post("/api/relay/reply")
async def relay_reply(req: RelayReplyRequest):
    """Called by the main session after receiving the user's Telegram reply."""
    success = relay_queue.reply(req.token, req.answer)
    if not success:
        raise HTTPException(status_code=410, detail="Token expired or not found")
    return {"status": "ok"}
