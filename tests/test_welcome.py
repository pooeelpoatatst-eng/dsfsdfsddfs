from app.modules.welcome import KEY


def test_welcome_key_is_stable() -> None:
    assert KEY == "welcome_messages"
