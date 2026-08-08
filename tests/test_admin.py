from app.modules.admin import _warns


class Settings:
    async def get(self, *_args):
        return {"1:2": ["one"]}


class Context:
    user_id = 1
    services = type("Services", (), {"settings": Settings()})()


async def test_warn_storage_defaults_to_dict() -> None:
    assert await _warns(Context()) == {"1:2": ["one"]}
