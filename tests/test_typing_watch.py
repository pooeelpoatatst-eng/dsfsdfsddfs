from app.modules.typing_watch import _action


class Event:
    typing = True
    recording = False
    uploading = False
    playing = False


def test_typing_action_identifies_typing() -> None:
    assert _action(Event()) == "печатает"
