from __future__ import annotations

import asyncio
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


class PublicAudioError(RuntimeError):
    pass


@dataclass(frozen=True)
class DownloadedAudio:
    path: Path
    source_url: str


def public_searches(query: str) -> tuple[str, ...]:
    """Public sources tried in order; no account cookies or paywall bypasses."""
    return (f"scsearch1:{query}", f"ytsearch1:{query}")


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
    try:
        for attempt, search in enumerate(public_searches(query), start=1):
            output = folder / f"track-{attempt}.%(ext)s"
            options = {
                "format": "bestaudio/best",
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "outtmpl": str(output),
                "max_filesize": max_mb * 1024 * 1024,
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
            }
            try:
                with yt_dlp.YoutubeDL(options) as downloader:
                    info = downloader.extract_info(search, download=True)
                selected = (info.get("entries") or [info])[0]
                duration = selected.get("duration")
                if duration is not None and duration < 20:
                    continue
                files = list(folder.glob(f"track-{attempt}.mp3"))
                if not files or files[0].stat().st_size > max_mb * 1024 * 1024:
                    continue
                source = str(selected.get("webpage_url") or selected.get("original_url") or "")
                return DownloadedAudio(files[0], source)
            except Exception:
                continue
        raise PublicAudioError("Не нашёл доступный публичный аудиоисточник для этого трека.")
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise
