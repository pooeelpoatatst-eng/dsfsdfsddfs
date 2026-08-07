import pytest

from app.database.repositories import SettingsRepository

class Session:
    async def scalar(self, query): return None
    def add(self, item): self.item = item
class Context:
    def __init__(self): self.session_value = Session()
    async def __aenter__(self): return self.session_value
    async def __aexit__(self, *args): pass
class DB:
    def session(self): return Context()

@pytest.mark.asyncio
async def test_settings_returns_default_when_not_configured() -> None:
    repository = SettingsRepository(DB())
    assert await repository.get(1, "missing", {"enabled": True}) == {"enabled": True}
