import pytest

from app.services.yandex_music import YandexMusicError, normalize_yandex_music_url, parse_og_title, parse_track_ids, validate_yandex_music_url


def test_parses_public_page_metadata() -> None:
    page = '<meta content="Артист • Трек • 2026" property="og:description"><meta content="Трек" property="og:title"><script>{"trackId":"123"}{"trackId":"456"}{"trackId":"123"}</script>'
    assert parse_og_title(page) == "Артист — Трек"
    assert parse_track_ids(page) == ["123", "456"]


def test_rejects_non_yandex_music_host() -> None:
    with pytest.raises(YandexMusicError):
        validate_yandex_music_url("https://example.com/track/123")


def test_accepts_album_track_share_url_and_html_query() -> None:
    url = "[track](https://music.yandex.ru/album/43309761/track/154249264?utm_source=desktop&amp;utm_medium=copy_link)"
    assert normalize_yandex_music_url(url) == "https://music.yandex.ru/album/43309761/track/154249264?utm_source=desktop&utm_medium=copy_link"
    assert validate_yandex_music_url(url).startswith("https://music.yandex.ru/album/43309761/track/154249264")
