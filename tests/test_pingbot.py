from app.modules.pingbot import KEY


def test_pingbot_key_is_stable() -> None:
    assert KEY == "ping_bots"
