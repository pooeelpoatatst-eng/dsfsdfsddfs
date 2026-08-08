from datetime import date, timedelta

from app.modules.quotes import _quote_html
from app.modules.streak import apply_message, is_active


def test_fake_quote_is_visibly_labelled() -> None:
    assert "фейковая цитата" in _quote_html("A", "B", fake=True)


def test_streak_requires_messages_from_both_sides_each_day() -> None:
    today = date(2026, 8, 8)
    entry, completed = apply_message({}, today, "out")
    assert completed is False
    entry, completed = apply_message(entry, today, "in")
    assert completed is True and entry["count"] == 1
    entry, completed = apply_message(entry, today, "in")
    assert completed is False and entry["count"] == 1
    entry, completed = apply_message(entry, today + timedelta(days=1), "out")
    entry, completed = apply_message(entry, today + timedelta(days=1), "in")
    assert completed is True and entry["count"] == 2
    assert is_active(entry, today + timedelta(days=2))
