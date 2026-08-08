from app.modules.quotes import _quote_html


def test_fake_quote_is_visibly_labelled() -> None:
    assert "фейковая цитата" in _quote_html("A", "B", fake=True)
