import threading
import time as _time
import uuid
from dataclasses import dataclass


@dataclass
class RelayEntry:
    token: str
    job_name: str
    skill: str
    question: str
    created_at: float
    answer: str | None = None
    expired: bool = False


class RelayQueue:
    """In-memory store for mid-job questions relayed to the user via Telegram."""

    def __init__(self, timeout_seconds: int = 1800):
        self._entries: dict[str, RelayEntry] = {}
        self._lock = threading.Lock()
        self._timeout = timeout_seconds

    def ask(self, job_name: str, skill: str, question: str) -> str:
        token = uuid.uuid4().hex[:12]
        with self._lock:
            self._entries[token] = RelayEntry(
                token=token, job_name=job_name, skill=skill,
                question=question, created_at=_time.time(),
            )
        return token

    def get_answer(self, token: str) -> RelayEntry | None:
        with self._lock:
            entry = self._entries.get(token)
            if entry is None:
                return None
            if entry.answer is None and _time.time() - entry.created_at > self._timeout:
                entry.expired = True
            return entry

    def reply(self, token: str, answer: str) -> bool:
        with self._lock:
            entry = self._entries.get(token)
            if entry is None or entry.expired:
                return False
            if entry.answer is not None:
                return False  # already answered
            entry.answer = answer
            return True

    def pending(self) -> list[RelayEntry]:
        """List unanswered, unexpired entries."""
        now = _time.time()
        with self._lock:
            return [e for e in self._entries.values()
                    if e.answer is None and not e.expired
                    and now - e.created_at <= self._timeout]

    def cleanup(self):
        cutoff = _time.time() - (self._timeout * 2)
        with self._lock:
            self._entries = {k: v for k, v in self._entries.items()
                            if v.created_at > cutoff}


relay_queue = RelayQueue()
