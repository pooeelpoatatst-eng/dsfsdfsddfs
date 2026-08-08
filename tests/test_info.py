from app.modules.info import _entity_text


class User:
    id = 5
    first_name = "Name"
    last_name = None
    username = "user"
    bot = False


def test_info_output_contains_safe_public_fields() -> None:
    text = _entity_text(User())
    assert "Name" in text and "@user" in text and "ID: 5" in text
