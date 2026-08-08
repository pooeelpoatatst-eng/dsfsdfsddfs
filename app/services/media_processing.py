from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Any


class MediaProcessingError(RuntimeError):
    pass


MAX_MEDIA_BYTES = 50 * 1024 * 1024


def safe_suffix(name: str | None, fallback: str) -> str:
    suffix = Path(name or "").suffix.lower()
    return suffix if suffix and len(suffix) <= 8 and suffix[1:].isalnum() else fallback


async def ffmpeg_reply(
    client: Any, reply: Any, *, output_name: str, output_suffix: str, args: list[str], timeout: float = 120
) -> tuple[Path, Path]:
    if not reply or not reply.file:
        raise MediaProcessingError("Ответь на аудио или видео.")
    if reply.file.size and reply.file.size > MAX_MEDIA_BYTES:
        raise MediaProcessingError("Файл больше 50 МБ — не буду обрабатывать его на сервере.")
    folder = Path(tempfile.mkdtemp(prefix="userbot-media-"))
    source = folder / f"input{safe_suffix(getattr(reply.file, 'name', None), '.bin')}"
    output = folder / f"{output_name}{output_suffix}"
    try:
        result = await client.download_media(reply, file=str(source))
        if not result or not source.exists():
            raise MediaProcessingError("Не удалось скачать файл из Telegram.")
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source), *args, str(output),
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        if process.returncode or not output.exists() or output.stat().st_size == 0:
            message = stderr.decode("utf-8", errors="replace").strip()
            raise MediaProcessingError(f"FFmpeg не смог обработать файл{': ' + message[:180] if message else ''}.")
        return folder, output
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise


def cleanup(folder: Path) -> None:
    shutil.rmtree(folder, ignore_errors=True)
