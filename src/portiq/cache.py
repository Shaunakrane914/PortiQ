"""Bounded exact-answer caching and database-version invalidation."""

import hashlib
import threading
import time
from collections import OrderedDict
from pathlib import Path

from portiq.answers import AgentResponse
from portiq.errors import PortiqError


def database_version(path: Path) -> str:
    before = path.stat()
    content = path.read_bytes()
    after = path.stat()
    before_identity = (before.st_ino, before.st_mtime_ns, before.st_size)
    after_identity = (after.st_ino, after.st_mtime_ns, after.st_size)
    if before_identity != after_identity:
        raise PortiqError("Database changed during version lookup; retry.")
    return hashlib.sha256(content + repr(after_identity).encode()).hexdigest()


class ExactCache:
    def __init__(self, capacity: int = 64, ttl: float = 300) -> None:
        self.capacity, self.ttl = capacity, ttl
        self.items: OrderedDict[str, tuple[float, AgentResponse]] = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> AgentResponse | None:
        with self.lock:
            item = self.items.pop(key, None)
            if item is None or time.monotonic() - item[0] > self.ttl:
                return None
            self.items[key] = item
            return item[1].model_copy(deep=True)

    def put(self, key: str, answer: AgentResponse) -> None:
        if answer.status != "answer" or any(t.error for t in answer.tools):
            return
        with self.lock:
            self.items[key] = (time.monotonic(), answer.model_copy(deep=True))
            self.items.move_to_end(key)
            while len(self.items) > self.capacity:
                self.items.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.items.clear()
