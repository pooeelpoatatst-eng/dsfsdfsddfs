import time
import pytest

from app.userbot.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_waits_between_actions() -> None:
    limiter = RateLimiter({"x": .03})
    await limiter.wait("x")
    started = time.monotonic(); await limiter.wait("x")
    assert time.monotonic() - started >= .02
