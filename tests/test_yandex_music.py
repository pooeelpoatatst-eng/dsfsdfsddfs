import pytest

from app.services.yandex_music import YandexMusicError, normalize_yandex_music_url, parse_og_title, parse_track_ids, track_id_from_url, track_title_from_api, track_title_from_song_link, validate_yandex_music_url


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
    assert track_id_from_url(url) == "154249264"


def test_parses_track_title_from_public_yandex_api_payload() -> None:
    payload = {"result": [{"title": "Танцуешь", "artists": [{"name": "Locked23"}]}]}
    assert track_title_from_api(payload) == "Locked23 — Танцуешь"


def test_parses_track_title_from_song_link_payload() -> None:
    payload = {
        "entityUniqueId": "YANDEX_SONG::154249264",
        "entitiesByUniqueId": {
            "YANDEX_SONG::154249264": {"title": "Танцуешь", "artistName": "Locked23"},
        },
    }
    assert track_title_from_song_link(payload) == "Locked23 — Танцуешь"


def test_parses_nextjs_escaped_meta_title() -> None:
    page = r'{\"property\":\"og:title\",\"content\":\"Танцуешь\"}{\"property\":\"og:description\",\"content\":\"Locked23 • Трек\"}'
    assert parse_og_title(page) == "Locked23 — Танцуешь"
