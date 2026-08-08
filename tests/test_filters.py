from app.modules.filters import _split_rule


def test_filter_rule_needs_trigger_and_response() -> None:
    assert _split_rule("hello | world") == ("hello", "world")
    assert _split_rule("hello") is None
    assert _split_rule(" | world") is None
