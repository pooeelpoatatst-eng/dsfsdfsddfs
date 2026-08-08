from __future__ import annotations

from app.services.yandex_music import YandexMusicError, YandexMusicShareService
from app.userbot.registry import command


music = YandexMusicShareService()


async def _send_track(context: object, url: str) -> None:
    try:
        track = await music.track(url)
    except YandexMusicError as exc:
        await context.edit(f"⚠️ {exc}")
        return
    await context.delete()
    message = await context.event.client.send_message(context.chat_id, f"🎵 {track.title}\n{track.url}", link_preview=True)
    context.client.mark_internal(message)


@command(name="ym", aliases=["music"], category="Музыка", description="Поделиться треком Яндекс Музыки в текущем диалоге.", usage=".ym <ссылка на трек>")
async def ym(context: object) -> None:
    if not context.raw_args.strip():
        await context.edit("⚠️ .ym https://music.yandex.ru/album/.../track/...")
        return
    await _send_track(context, context.raw_args.strip())


@command(name="ymplaylist", aliases=["playlist"], category="Музыка", description="Сохранить публичный плейлист Яндекс Музыки для случайного трека.", usage=".ymplaylist set <ссылка> | .ymplaylist status | .ymplaylist clear")
async def ym_playlist(context: object) -> None:
    action, _, value = context.raw_args.strip().partition(" ")
    action = action.lower()
    if action == "set" and value.strip():
        try:
            # Verify now, so `.randomtrack` does not silently store an invalid
            # or non-public address.
            await music.random_track(value.strip())
        except YandexMusicError as exc:
            await context.edit(f"⚠️ {exc}")
            return
        await context.services.settings.set(context.user_id, "ym_playlist", {"url": value.strip()})
        await context.edit("🎶 Плейлист сохранён. Теперь `.randomtrack` отправит случайный трек.")
        return
    if action == "clear":
        await context.services.settings.set(context.user_id, "ym_playlist", {})
        await context.edit("🎶 Плейлист очищен.")
        return
    saved = await context.services.settings.get(context.user_id, "ym_playlist", {})
    url = saved.get("url") if isinstance(saved, dict) else None
    await context.edit(f"🎶 Плейлист: {url}" if url else "🎶 Плейлист не задан. `.ymplaylist set <публичная ссылка>`")


@command(name="randomtrack", aliases=["ymrandom", "track"], category="Музыка", description="Отправить случайный трек из сохранённого публичного плейлиста.", usage=".randomtrack")
async def random_track(context: object) -> None:
    saved = await context.services.settings.get(context.user_id, "ym_playlist", {})
    url = saved.get("url") if isinstance(saved, dict) else None
    if not url:
        await context.edit("⚠️ Сначала сохрани публичный плейлист: `.ymplaylist set <ссылка>`")
        return
    try:
        track = await music.random_track(url)
    except YandexMusicError as exc:
        await context.edit(f"⚠️ {exc}")
        return
    await context.delete()
    message = await context.event.client.send_message(context.chat_id, f"🎲🎵 {track.title}\n{track.url}", link_preview=True)
    context.client.mark_internal(message)
