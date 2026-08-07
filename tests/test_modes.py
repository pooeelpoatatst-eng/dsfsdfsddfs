import pytest

from app.userbot.modes import ModeManager

class Row:
    def __init__(self, mode: str, enabled: bool, config: dict | None = None) -> None:
        self.mode, self.enabled, self.config_json = mode, enabled, config or {}

class Repository:
    def __init__(self) -> None: self.rows = {}
    async def get(self, user_id: int, chat_id: int, mode: str): return self.rows.get((user_id, chat_id, mode))
    async def set(self, user_id: int, chat_id: int, mode: str, enabled: bool, config=None): self.rows[(user_id, chat_id, mode)] = Row(mode, enabled, config)
    async def enabled(self, user_id: int, chat_id: int): return [row for (uid, cid, _), row in self.rows.items() if uid == user_id and cid == chat_id and row.enabled]

@pytest.mark.asyncio
async def test_transform_modes_are_exclusive() -> None:
    repo = Repository(); modes = ModeManager(1, repo)
    await modes.set(10, "kawaii", True)
    await modes.set(10, "toxic", True)
    assert await modes.active(10) == ["toxic"]
