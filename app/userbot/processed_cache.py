from __future__ import annotations

import time


class ProcessedMessageCache:
    def __init__(self, ttl_seconds: float = 45) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[tuple[int, int], float] = {}

    def contains(self, chat_id: int, message_id: int) -> bool:
        self.cleanup()
        return (chat_id, message_id) in self._items

    def add(self, chat_id: int, message_id: int) -> None:
        self._items[(chat_id, message_id)] = time.monotonic() + self.ttl_seconds

    def cleanup(self) -> None:
        now = time.monotonic()
        self._items = {key: expires for key, expires in self._items.items() if expires > now}
