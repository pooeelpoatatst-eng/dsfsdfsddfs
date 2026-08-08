from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.services.downloader import UnsafeURLError, validate_public_url


class YandexMusicError(ValueError):
    pass


@dataclass(frozen=True)
class SharedTrack:
    url: str
    title: str


YAMUSIC_HOSTS = {"music.yandex.ru", "music.yandex.com", "music.yandex.kz", "music.yandex.by", "music.yandex.uz"}
META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.I)
META_ATTRIBUTE_RE = re.compile(r"([\w:-]+)\s*=\s*([\"'])(.*?)\2", re.I)
TRACK_ID_RE = re.compile(r'(?:"trackId"|"track_id"|"id")\s*:\s*"?(\d{3,})"?', re.I)
TRACK_PATH_RE = re.compile(r"/(?:album/\d+/)?track/(?P<id>\d+)(?:/|$)", re.I)
URL_RE = re.compile(r"https?://[^\s<>\]\)]+", re.I)


def normalize_yandex_music_url(value: str) -> str:
    """Extract a share URL from plain text/Markdown and unescape HTML query text."""
    value = html.unescape(value.strip())
    match = URL_RE.search(value)
    if match:
        value = match.group(0)
    return value.strip(" \t\r\n<>'\"()[]")


def validate_yandex_music_url(url: str) -> str:
    url = normalize_yandex_music_url(url)
    try:
        validated = validate_public_url(url)
    except UnsafeURLError as exc:
        raise YandexMusicError("Нужна корректная публичная ссылка Яндекс Музыки.") from exc
    host = (urlparse(validated).hostname or "").lower().removeprefix("www.")
    if host not in YAMUSIC_HOSTS:
        raise YandexMusicError("Поддерживаются только ссылки music.yandex.ru (и региональные домены).")
    path = urlparse(validated).path
    if not TRACK_PATH_RE.search(path):
        raise YandexMusicError("A Yandex Music track link is required for .ym.")
    return validated


def track_id_from_url(url: str) -> str:
    match = TRACK_PATH_RE.search(urlparse(validate_yandex_music_url(url)).path)
    if not match:
        raise YandexMusicError("A Yandex Music track link is required for .ym.")
    return match.group("id")


def track_title_from_api(data: object) -> str:
    if not isinstance(data, dict):
        return ""
    result = data.get("result")
    track = result[0] if isinstance(result, list) and result else None
    if not isinstance(track, dict):
        return ""
    title = str(track.get("title") or "").strip()
    artists = track.get("artists")
    names = [str(item.get("name") or "").strip() for item in artists if isinstance(item, dict)] if isinstance(artists, list) else []
    artist = ", ".join(name for name in names if name)
    return f"{artist} — {title}"[:240] if artist and title else title[:240]


def _meta_content(page: str, key: str) -> str:
    for tag in META_TAG_RE.findall(page):
        attrs = {name.lower(): html.unescape(value).strip() for name, _, value in META_ATTRIBUTE_RE.findall(tag)}
        if attrs.get("property", "").lower() == key or attrs.get("name", "").lower() == key:
            return attrs.get("content", "")
    return ""


def _rsc_meta_content(page: str, key: str) -> str:
    """Read Next.js escaped meta tags when normal HTML meta tags are absent."""
    marker = f'\\"property\\":\\"{key}\\"'
    position = page.find(marker)
    if position < 0:
        return ""
    content_marker = '\\"content\\":\\"'
    start = page.find(content_marker, position)
    if start < 0:
        return ""
    raw = page[start + len(content_marker):]
    match = re.match(r'((?:\\\\.|[^"])*)\\"', raw)
    if not match:
        return ""
    try:
        return json.loads(f'"{match.group(1)}"').strip()
    except json.JSONDecodeError:
        return ""


def parse_og_title(page: str) -> str:
    title = _meta_content(page, "og:title") or _rsc_meta_content(page, "og:title") or _meta_content(page, "twitter:title")
    description = _meta_content(page, "og:description") or _rsc_meta_content(page, "og:description") or _meta_content(page, "twitter:description")
    title = re.sub(r"\s*[—–-]\s*Яндекс Музыка.*$", "", title, flags=re.I).strip()
    artist = description.split("•", 1)[0].strip()
    if title and artist and artist.lower() not in {"трек", title.lower()}:
        return f"{artist} — {title}"[:240]
    return title[:240]


def parse_track_ids(page: str) -> list[str]:
    # Public pages include a bootstrap JSON payload. The exact surrounding
    # shape changes, so retain only unique numeric ids in their seen order.
    return list(dict.fromkeys(TRACK_ID_RE.findall(page)))[:2_000]


class YandexMusicShareService:
    """Reads public page metadata; it never downloads or bypasses audio access."""

    async def _page(self, url: str) -> str:
        url = validate_yandex_music_url(url)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(12), follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 Telegram Userbot"}) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise YandexMusicError("Не получилось открыть ссылку Яндекс Музыки.") from exc
        return response.text

    async def track(self, url: str) -> SharedTrack:
        url = validate_yandex_music_url(url)
        track_id = track_id_from_url(url)
        title = ""
        async with httpx.AsyncClient(timeout=httpx.Timeout(12), headers={"User-Agent": "Mozilla/5.0 Telegram Userbot"}) as client:
            for host in ("api.music.yandex.net", "api.music.yandex.ru"):
                try:
                    response = await client.get(f"https://{host}/tracks/{track_id}")
                    response.raise_for_status()
                    title = track_title_from_api(response.json())
                    if title:
                        break
                # One Yandex API hostname may be geo-blocked (451) in a
                # datacentre while the other one remains available.
                except (httpx.HTTPError, ValueError):
                    continue
        if not title:
            try:
                title = parse_og_title(await self._page(url))
            except YandexMusicError:
                title = ""
        if not title:
            raise YandexMusicError("Не смог прочитать название трека из ссылки. Пришли именно ссылку на трек, не альбом или плейлист.")
        return SharedTrack(url, title)

    async def random_track(self, playlist_url: str) -> SharedTrack:
        page = await self._page(playlist_url)
        track_ids = parse_track_ids(page)
        if not track_ids:
            raise YandexMusicError("В публичном плейлисте не удалось найти треки. Проверь, что ссылка открыта для всех.")
        import random
        track_url = f"https://music.yandex.ru/track/{random.choice(track_ids)}"
        return await self.track(track_url)
