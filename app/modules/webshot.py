from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from app.services.downloader import UnsafeURLError, validate_public_url
from app.userbot.registry import command


def public_url(value: str) -> str:
    try:
        return validate_public_url(value.strip())
    except UnsafeURLError as exc:
        raise ValueError("Нужна публичная HTTP(S)-ссылка.") from exc


async def _capture(url: str, pdf: bool) -> tuple[Path, Path]:
    url = public_url(url)
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError("Браузерный модуль ещё не установлен.") from exc
    directory = Path(tempfile.mkdtemp(prefix="userbot-webshot-"))
    output = directory / ("page.pdf" if pdf else "page.png")
    try:
        async with async_playwright() as playwright:
            executable = os.getenv("CHROMIUM_PATH", "/usr/bin/chromium")
            browser = await playwright.chromium.launch(
                headless=True, executable_path=executable if os.path.exists(executable) else None,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            try:
                page = await browser.new_page(viewport={"width": 1440, "height": 1200}, device_scale_factor=1)

                async def guard(route) -> None:
                    if route.request.url.startswith(("data:", "blob:", "about:")):
                        await route.continue_()
                        return
                    try:
                        public_url(route.request.url)
                    except ValueError:
                        await route.abort()
                    else:
                        await route.continue_()

                await page.route("**/*", guard)
                await page.goto(url, wait_until="networkidle", timeout=30_000)
                if pdf:
                    await page.pdf(path=str(output), format="A4", print_background=True)
                else:
                    await page.screenshot(path=str(output), full_page=True)
            finally:
                await browser.close()
        if not output.exists() or not output.stat().st_size:
            raise RuntimeError("Браузер не создал файл.")
        return directory, output
    except BaseException:
        shutil.rmtree(directory, ignore_errors=True)
        raise


async def _webshot(context: object, pdf: bool) -> None:
    url = context.raw_args.strip()
    if not url:
        await context.edit(f"⚠️ Использование: .{'fileshot' if pdf else 'screenshot'} <ссылка>")
        return
    await context.edit("🌐 Открываю страницу…")
    try:
        directory, output = await _capture(url, pdf)
    except (ValueError, RuntimeError):
        await context.edit("⚠️ Не удалось открыть страницу или создать снимок.")
        return
    try:
        await context.delete()
        sent = await context.event.client.send_file(context.chat_id, str(output), force_document=pdf)
        context.client.mark_internal(sent)
    finally:
        shutil.rmtree(directory, ignore_errors=True)


@command(name="screenshot", aliases=["shot"], category="Screenshot", description="Сделать PNG-снимок публичной веб-страницы.", usage=".screenshot <ссылка>")
async def screenshot(context: object) -> None:
    await _webshot(context, False)


@command(name="fileshot", category="WebShot", description="Сохранить публичную веб-страницу в PDF.", usage=".fileshot <ссылка>")
async def fileshot(context: object) -> None:
    await _webshot(context, True)
