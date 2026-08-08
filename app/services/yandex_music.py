from __future__ import annotations

import html
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
OG_TITLE_RE = re.compile(r'<meta[^>]+(?:property|name)=["\']og:title["\'][^>]+content=["\']([^"\']+)', re.I)
TRACK_ID_RE = re.compile(r'(?:"trackId"|"track_id"|"id")\s*:\s*"?(\d{3,})"?', re.I)


def validate_yandex_music_url(url: str) -> str:
    try:
        validated = validate_public_url(url)
    except UnsafeURLError as exc:
        raise YandexMusicError("Нужна корректная публичная ссылка Яндекс Музыки.") from exc
    host = (urlparse(validated).hostname or "").lower().removeprefix("www.")
    if host not in YAMUSIC_HOSTS:
        raise YandexMusicError("Поддерживаются только ссылки music.yandex.ru (и региональные домены).")
    return validated


def parse_og_title(page: str) -> str:
    match = OG_TITLE_RE.search(page)
    if not match:
        return "Трек из Яндекс Музыки"
    title = html.unescape(match.group(1)).strip()
    return re.sub(r"\s*[—–-]\s*Яндекс Музыка.*$", "", title, flags=re.I)[:240] or "Трек из Яндекс Музыки"


def parse_track_ids(page: str) -> list[str]:
    # Public pages include a bootstrap JSON payload. The exact surrounding
    # shape changes, so retain only unique numeric ids in their seen order.
    return list(dict.fromkeys(TRACK_ID_RE.findall(page)))[:2_000]


class YandexMusicShareService:
    """Reads public page metadata; it never downloads or bypasses audio access."""

    async def _page(self, url: str) -> str:
        url = validate_yandex_music_url(url)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(12), follow_redirects=False, headers={"User-Agent": "Mozilla/5.0 Telegram Userbot"}) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise YandexMusicError("Не получилось открыть ссылку Яндекс Музыки.") from exc
        return response.text

    async def track(self, url: str) -> SharedTrack:
        page = await self._page(url)
        return SharedTrack(validate_yandex_music_url(url), parse_og_title(page))

    async def random_track(self, playlist_url: str) -> SharedTrack:
        page = await self._page(playlist_url)
        track_ids = parse_track_ids(page)
        if not track_ids:
            raise YandexMusicError("В публичном плейлисте не удалось найти треки. Проверь, что ссылка открыта для всех.")
        import random
        track_url = f"https://music.yandex.ru/track/{random.choice(track_ids)}"
        return await self.track(track_url)
