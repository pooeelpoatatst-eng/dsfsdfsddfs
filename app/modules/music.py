from __future__ import annotations

import shutil
import re

from app.services.public_audio import PublicAudioError, download_public_audio
from app.services.yandex_music import SharedTrack, YandexMusicError, YandexMusicShareService
from app.userbot.registry import command


music = YandexMusicShareService()


async def _send_audio(context: object, track: SharedTrack) -> None:
    await context.edit(f"🎵 Ищу и подготавливаю: {track.title[:180]}")
    try:
        audio = await download_public_audio(track.title)
    except PublicAudioError as exc:
        await context.edit(f"⚠️ {exc}")
        return
    try:
        safe_name = re.sub(r'[\\/:*?"<>|]+', "_", track.title).strip()[:120] or "track"
        path = audio.path.with_name(f"{safe_name}.mp3")
        audio.path.rename(path)
        await context.delete()
        message = await context.event.client.send_file(context.chat_id, str(path), caption=f"🎵 {track.title[:220]}", force_document=False, supports_streaming=True)
        context.client.mark_internal(message)
    finally:
        shutil.rmtree(audio.path.parent, ignore_errors=True)


@command(name="ym", aliases=["music"], category="Музыка", description="По Яндекс-ссылке найти публичный аудиоисточник и отправить трек файлом.", usage=".ym <ссылка Яндекс Музыки>")
async def ym(context: object) -> None:
    if not context.raw_args.strip():
        await context.edit("⚠️ .ym https://music.yandex.ru/album/.../track/...")
        return
    try:
        track = await music.track(context.raw_args.strip())
    except YandexMusicError as exc:
        await context.edit(f"⚠️ {exc}")
        return
    await _send_audio(context, track)


@command(name="ymplaylist", aliases=["playlist"], category="Музыка", description="Сохранить публичный плейлист Яндекс Музыки для случайного аудиотрека.", usage=".ymplaylist set <ссылка> | status | clear")
async def ym_playlist(context: object) -> None:
    action, _, value = context.raw_args.strip().partition(" ")
    action = action.lower()
    if action == "set" and value.strip():
        try:
            await music.random_track(value.strip())
        except YandexMusicError as exc:
            await context.edit(f"⚠️ {exc}")
            return
        await context.services.settings.set(context.user_id, "ym_playlist", {"url": value.strip()})
        await context.edit("🎶 Плейлист Яндекс Музыки сохранён. `.randomtrack` будет отправлять случайный трек аудиофайлом.")
        return
    if action == "clear":
        await context.services.settings.set(context.user_id, "ym_playlist", {})
        await context.edit("🎶 Плейлист очищен.")
        return
    saved = await context.services.settings.get(context.user_id, "ym_playlist", {})
    url = saved.get("url") if isinstance(saved, dict) else None
    await context.edit(f"🎶 Плейлист: {url}" if url else "🎶 Плейлист не задан. `.ymplaylist set <публичная ссылка>`")


@command(name="randomtrack", aliases=["ymrandom"], category="Музыка", description="Отправить случайный аудиотрек из недавней музыки в «Избранном».", usage=".randomtrack")
async def random_track(context: object) -> None:
    import random
    from telethon import types
    selected = None
    count = 0
    async for message in context.event.client.iter_messages("me", limit=300, filter=types.InputMessagesFilterMusic()):
        count += 1
        if random.randrange(count) == 0:
            selected = message
    if not selected:
        await context.edit("⚠️ В «Избранном» нет аудиофайлов. Сохрани туда треки — `.randomtrack` возьмёт случайный.")
        return
    await context.delete()
    result = await context.event.client.forward_messages(context.chat_id, selected, from_peer="me", drop_author=True)
    for item in result if isinstance(result, list) else [result]:
        context.client.mark_internal(item)
