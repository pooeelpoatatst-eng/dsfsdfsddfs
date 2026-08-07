from app.userbot.commands import parse_command

def test_parser_supports_quoted_arguments() -> None:
    parsed = parse_command('.note add title "hello world"')
    assert parsed and parsed.name == "note"
    assert parsed.args == ["add", "title", "hello world"]

def test_parser_rejects_domain() -> None:
    assert parse_command(".example.com") is None
