from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """Small independent per-client limiter; no user can consume another's budget."""
    def __init__(self, intervals: dict[str, float] | None = None) -> None:
        self.intervals = intervals or {"message_send": 0.4, "message_edit": 0.5, "profile_update": 300, "ai": 0.1, "download": 1, "media": 1}
        self._last: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def wait(self, category: str) -> None:
        lock = self._locks.setdefault(category, asyncio.Lock())
        async with lock:
            delay = self.intervals.get(category, 0)
            remaining = delay - (time.monotonic() - self._last.get(category, 0))
            if remaining > 0:
                await asyncio.sleep(remaining)
            self._last[category] = time.monotonic()
