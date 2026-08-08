import pytest

from app.modules.online import always_online


class Settings:
    def __init__(self) -> None:
        self.value = False

    async def get(self, *_args):
        return self.value

    async def set(self, _user_id, _key, value):
        self.value = value


class Context:
    def __init__(self, args, settings) -> None:
        self.args = args
        self.user_id = 1
        self.services = type("Services", (), {"settings": settings})()

    async def edit(self, text):
        self.text = text


@pytest.mark.asyncio
async def test_always_online_saves_toggle() -> None:
    settings = Settings()
    await always_online(Context(["on"], settings))
    assert settings.value is True
