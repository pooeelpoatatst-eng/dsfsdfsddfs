import pytest

from app.modules.afk import afk_ai


class Settings:
    def __init__(self) -> None: self.values = {}
    async def get(self, user_id, key, default=None): return self.values.get((user_id, key), default)
    async def set(self, user_id, key, value): self.values[(user_id, key)] = value

class Context:
    def __init__(self, args, chat_id, settings) -> None:
        self.args, self.chat_id = args, chat_id
        self.user_id, self.services = 1, type("Services", (), {"settings": settings})()
        self.deleted = False
    async def delete(self): self.deleted = True
    async def edit(self, text): self.error = text

@pytest.mark.asyncio
async def test_afkai_only_enables_current_chat() -> None:
    settings = Settings(); context = Context(["on"], 100, settings)
    await afk_ai(context)
    assert settings.values[(1, "afk_ai_chats")] == [100]
    assert context.deleted

@pytest.mark.asyncio
async def test_afkai_off_keeps_other_chats() -> None:
    settings = Settings(); settings.values[(1, "afk_ai_chats")] = [100, 200]
    await afk_ai(Context(["off"], 100, settings))
    assert settings.values[(1, "afk_ai_chats")] == [200]
