from __future__ import annotations

import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.services.downloader import UnsafeURLError, validate_public_url
from app.userbot.registry import command


async def _download(url: str, max_bytes: int) -> tuple[Path, Path]:
    try:
        current = validate_public_url(url)
    except UnsafeURLError as exc:
        raise ValueError("Нужна публичная HTTP(S)-ссылка.") from exc
    directory = Path(tempfile.mkdtemp(prefix="userbot-url-"))
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            for _ in range(4):
                async with client.stream("GET", current) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise ValueError("Сервер вернул пустой редирект.")
                        current = validate_public_url(str(response.url.join(location)))
                        continue
                    response.raise_for_status()
                    size = int(response.headers.get("content-length", 0) or 0)
                    if size > max_bytes:
                        raise ValueError(f"Файл больше {max_bytes // 1024 // 1024} МБ.")
                    name = Path(urlparse(str(response.url)).path).name or "download.bin"
                    path = directory / name[:120]
                    written = 0
                    with path.open("wb") as output:
                        async for chunk in response.aiter_bytes():
                            written += len(chunk)
                            if written > max_bytes:
                                raise ValueError(f"Файл больше {max_bytes // 1024 // 1024} МБ.")
                            output.write(chunk)
                    return directory, path
            raise ValueError("Слишком много редиректов.")
    except BaseException:
        for child in directory.glob("*"):
            child.unlink(missing_ok=True)
        directory.rmdir()
        raise


async def _url_download(context: object, max_mb: int) -> None:
    url = context.raw_args.strip()
    if not url:
        await context.edit("⚠️ Использование: .urldl <публичная ссылка>")
        return
    try:
        directory, path = await _download(url, max_mb * 1024 * 1024)
    except (ValueError, httpx.HTTPError):
        await context.edit(f"⚠️ Не удалось скачать файл (лимит {max_mb} МБ).")
        return
    try:
        await context.delete()
        sent = await context.event.client.send_file(context.chat_id, str(path), force_document=True)
        context.client.mark_internal(sent)
    finally:
        path.unlink(missing_ok=True)
        directory.rmdir()


@command(name="urldl", category="UrlDl", description="Скачать файл по публичной ссылке, до 50 МБ.", usage=".urldl <ссылка>")
async def urldl(context: object) -> None:
    await _url_download(context, 50)


@command(name="urldlbig", category="UrlDl", description="Скачать файл по публичной ссылке, до 250 МБ.", usage=".urldlbig <ссылка>")
async def urldl_big(context: object) -> None:
    await _url_download(context, 250)
