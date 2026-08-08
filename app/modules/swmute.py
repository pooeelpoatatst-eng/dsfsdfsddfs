from __future__ import annotations

from typing import Any

from app.userbot.registry import command


KEY = "swmute_words"


async def _words(context: object) -> dict[str, list[str]]:
    value = await context.services.settings.get(context.user_id, KEY, {})
    return value if isinstance(value, dict) else {}


@command(name="swmute", category="SwMute", description="Удалять в этом чате новые сообщения с указанным словом.", usage=".swmute <слово>")
async def swmute(context: object) -> None:
    word = context.raw_args.strip().casefold()
    if not word or len(word) > 80:
        await context.edit("⚠️ Укажи слово или короткую фразу до 80 символов.")
        return
    saved = await _words(context)
    chat = saved.setdefault(str(context.chat_id), [])
    if word not in chat:
        chat.append(word)
    await context.services.settings.set(context.user_id, KEY, saved)
    await context.edit(f"✅ SwMute добавлен: {word}")


@command(name="swmutelist", category="SwMute", description="Показать SwMute-слова этого чата.", usage=".swmutelist")
async def swmute_list(context: object) -> None:
    items = (await _words(context)).get(str(context.chat_id), [])
    await context.edit("🔇 SwMute\n\n" + ("\n".join(f"• {word}" for word in items) if items else "Список пуст."))


@command(name="swmuteclear", category="SwMute", description="Очистить SwMute-слова этого чата.", usage=".swmuteclear")
async def swmute_clear(context: object) -> None:
    saved = await _words(context)
    count = len(saved.pop(str(context.chat_id), []))
    await context.services.settings.set(context.user_id, KEY, saved)
    await context.edit(f"✅ SwMute очищен: {count}.")


async def maybe_swmute(client: Any, event: Any) -> None:
    saved = await client.services.settings.get(client.user_id, KEY, {})
    words = saved.get(str(event.chat_id), []) if isinstance(saved, dict) else []
    text = (event.raw_text or "").casefold()
    if text and any(word in text for word in words if isinstance(word, str)):
        try:
            await event.delete()
        except Exception:
            return
