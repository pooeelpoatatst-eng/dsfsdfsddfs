import pytest

from app.services.yandex_music import YandexMusicError, parse_og_title, parse_track_ids, validate_yandex_music_url


def test_parses_public_page_metadata() -> None:
    page = '<meta content="Артист • Трек • 2026" property="og:description"><meta content="Трек" property="og:title"><script>{"trackId":"123"}{"trackId":"456"}{"trackId":"123"}</script>'
    assert parse_og_title(page) == "Артист — Трек"
    assert parse_track_ids(page) == ["123", "456"]


def test_rejects_non_yandex_music_host() -> None:
    with pytest.raises(YandexMusicError):
        validate_yandex_music_url("https://example.com/track/123")
