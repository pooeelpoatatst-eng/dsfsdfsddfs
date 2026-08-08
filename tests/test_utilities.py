from app.modules.utilities import _file_name


def test_file_name_removes_forbidden_characters() -> None:
    assert _file_name('my:file?.txt', 'fallback') == 'my_file_.txt'
