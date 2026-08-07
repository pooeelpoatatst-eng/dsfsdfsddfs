import random

from app.modules.kawaii import local_kawaii

def test_local_kawaii_preserves_non_empty_text() -> None:
    random.seed(2)
    result = local_kawaii("пиздеж")
    assert "п" in result.lower()
    assert result != ""

def test_local_kawaii_short_text_stays_short() -> None:
    result = local_kawaii("да")
    assert len(result) < 20
