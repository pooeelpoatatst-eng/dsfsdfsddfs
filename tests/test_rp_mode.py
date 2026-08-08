from app.modules.rp_mode import _rule


def test_rp_rule_uses_separator_and_normalizes_trigger() -> None:
    assert _rule(" Hello | Hi ") == ("hello", "Hi")
    assert _rule("hello") is None
