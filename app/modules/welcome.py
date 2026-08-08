from __future__ import annotations

from typing import Any

from app.userbot.registry import command


KEY = "welcome_messages"


async def _settings(context: object) -> dict[str, dict[str, str]]:
    value = await context.services.settings.get(context.user_id, KEY, {})
    return value if isinstance(value, dict) else {}


async def _configure(context: object, kind: str) -> None:
    value = context.raw_args.strip()
    saved = await _settings(context)
    chat = saved.setdefault(str(context.chat_id), {})
    if not value or value == "status":
        text = chat.get(kind)
        await context.edit(f"👋 {kind}: {text}" if text else f"👋 {kind} выключено. Использование: .{kind} <текст> или off")
        return
    if value.lower() in {"off", "clear"}:
        chat.pop(kind, None)
        if not chat:
            saved.pop(str(context.chat_id), None)
        await context.services.settings.set(context.user_id, KEY, saved)
        await context.edit(f"✅ {kind} выключено.")
        return
    if len(value) > 1_000:
        await context.edit("⚠️ Текст не длиннее 1000 символов.")
        return
    chat[kind] = value
    await context.services.settings.set(context.user_id, KEY, saved)
    await context.edit(f"✅ {kind} сохранено. Используй {{name}} для имени человека.")


@command(name="welcome", category="Welcome", description="Настроить приветствие при входе участника.", usage=".welcome <текст>|off|status")
async def welcome(context: object) -> None:
    await _configure(context, "welcome")


@command(name="goodbye", category="Welcome", description="Настроить прощание при выходе участника.", usage=".goodbye <текст>|off|status")
async def goodbye(context: object) -> None:
    await _configure(context, "goodbye")


async def maybe_welcome(client: Any, event: Any) -> None:
    if not (getattr(event, "user_joined", False) or getattr(event, "user_left", False)):
        return
    saved = await client.services.settings.get(client.user_id, KEY, {})
    chat = saved.get(str(event.chat_id), {}) if isinstance(saved, dict) else {}
    kind = "welcome" if getattr(event, "user_joined", False) else "goodbye"
    template = chat.get(kind) if isinstance(chat, dict) else None
    if not isinstance(template, str):
        return
    user_id = getattr(event, "user_id", None)
    try:
        entity = await event.client.get_entity(user_id)
        name = getattr(entity, "first_name", None) or getattr(entity, "title", None) or "участник"
    except Exception:
        name = "участник"
    sent = await event.client.send_message(event.chat_id, template.replace("{name}", name))
    client.mark_internal(sent)
