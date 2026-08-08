from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from app.userbot.registry import command


KEY = "typing_watch_chats"
_events: dict[tuple[int, int], Counter[str]] = defaultdict(Counter)
_last: dict[tuple[int, int], tuple[int, str, datetime]] = {}


async def _watched(context: object) -> list[int]:
    value = await context.services.settings.get(context.user_id, KEY, [])
    return [int(item) for item in value] if isinstance(value, list) else []


@command(name="typingwatch", category="TypingWatch", description="Включить или выключить сбор событий печати в текущем чате.", usage=".typingwatch on | off | status")
async def typing_watch(context: object) -> None:
    action = context.args[0].lower() if context.args else "status"
    watched = await _watched(context)
    if action == "on":
        if context.chat_id not in watched:
            watched.append(context.chat_id)
        await context.services.settings.set(context.user_id, KEY, watched)
        await context.edit("✅ TypingWatch включён для этого чата.")
    elif action == "off":
        watched = [chat_id for chat_id in watched if chat_id != context.chat_id]
        await context.services.settings.set(context.user_id, KEY, watched)
        await context.edit("✅ TypingWatch выключен для этого чата.")
    elif action == "status":
        await context.edit(f"⌨️ TypingWatch: {'ON' if context.chat_id in watched else 'OFF'}")
    else:
        await context.edit("⚠️ Использование: .typingwatch on, off или status")


@command(name="typingstat", category="TypingWatch", description="Показать статистику печати после включения TypingWatch.", usage=".typingstat")
async def typing_stat(context: object) -> None:
    key = (context.user_id, context.chat_id)
    counter = _events.get(key, Counter())
    last = _last.get(key)
    lines = [f"⌨️ События печати: {sum(counter.values())}"]
    if counter:
        lines.append("\n".join(f"• {action}: {count}" for action, count in counter.most_common()))
    if last:
        user_id, action, at = last
        lines.append(f"Последнее: {user_id} — {action}, {at.strftime('%H:%M:%S')}")
    await context.edit("\n\n".join(lines))


def _action(event: Any) -> str | None:
    if getattr(event, "typing", False):
        return "печатает"
    if getattr(event, "recording", False):
        return "записывает"
    if getattr(event, "uploading", False):
        return "загружает"
    if getattr(event, "playing", False):
        return "играет"
    return None


async def maybe_record_typing(client: Any, event: Any) -> None:
    if not getattr(event, "chat_id", None) or event.sender_id == client.telegram_user_id:
        return
    watched = await client.services.settings.get(client.user_id, KEY, [])
    if event.chat_id not in watched:
        return
    action = _action(event)
    if not action:
        return
    key = (client.user_id, event.chat_id)
    _events[key][action] += 1
    _last[key] = (event.sender_id, action, datetime.now(timezone.utc))
