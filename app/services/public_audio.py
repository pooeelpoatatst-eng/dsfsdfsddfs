from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass
from pathlib import Path


class PublicAudioError(RuntimeError):
    pass


@dataclass(frozen=True)
class DownloadedAudio:
    path: Path
    source_url: str


async def download_public_audio(query: str, max_mb: int = 50) -> DownloadedAudio:
    """Find a public matching audio source and make a Telegram-ready MP3.

    The query comes from public Yandex Music metadata, while the actual file is
    obtained from a public web result through yt-dlp. It is intentionally not a
    Yandex Music stream extractor and never uses account cookies or a Yandex
    subscription.
    """
    return await asyncio.to_thread(_download, query, max_mb)


def _download(query: str, max_mb: int) -> DownloadedAudio:
    try:
        import yt_dlp
    except ImportError as exc:
        raise PublicAudioError("На сервере не установлен обработчик аудио.") from exc
    folder = Path(tempfile.mkdtemp(prefix="userbot-audio-"))
    output = folder / "track.%(ext)s"
    options = {
        "format": "bestaudio/best",
        "default_search": "ytsearch1",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(output),
        "max_filesize": max_mb * 1024 * 1024,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
    }
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(f"ytsearch1:{query}", download=True)
            source = str(info.get("webpage_url") or info.get("original_url") or "")
    except Exception as exc:
        raise PublicAudioError("Не нашёл доступный публичный аудиоисточник для этого трека.") from exc
    files = list(folder.glob("*.mp3"))
    if not files:
        raise PublicAudioError("Источник не отдал аудиофайл в подходящем формате.")
    path = files[0]
    if path.stat().st_size > max_mb * 1024 * 1024:
        raise PublicAudioError(f"Трек больше {max_mb} МБ и не помещается в лимит.")
    return DownloadedAudio(path, source)
