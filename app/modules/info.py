from __future__ import annotations

import json
import html

from app.userbot.registry import command


async def _entity(context: object) -> object | None:
    reply = await context.get_reply()
    if reply and reply.sender_id:
        return await context.event.client.get_entity(reply.sender_id)
    if context.raw_args.strip():
        try:
            return await context.event.client.get_entity(context.raw_args.strip())
        except (TypeError, ValueError):
            return None
    return await context.event.client.get_me()


def _entity_text(entity: object) -> str:
    title = getattr(entity, "title", None) or " ".join(
        part for part in (getattr(entity, "first_name", None), getattr(entity, "last_name", None)) if part
    ) or "Без имени"
    username = getattr(entity, "username", None)
    fields = [
        f"Имя: {title}",
        f"ID: {getattr(entity, 'id', '—')}",
        f"Username: @{username}" if username else "Username: нет",
        f"Тип: {entity.__class__.__name__}",
    ]
    if hasattr(entity, "bot"):
        fields.append(f"Бот: {'да' if getattr(entity, 'bot', False) else 'нет'}")
    return "\n".join(fields)


@command(name="info", category="Info", description="Показать публичную информацию о пользователе или чате.", usage=".info [@username] или reply")
async def info(context: object) -> None:
    entity = await _entity(context)
    if not entity:
        await context.edit("⚠️ Не удалось найти пользователя или чат.")
        return
    await context.edit(f"ℹ️ Информация\n\n{_entity_text(entity)}")


@command(name="who", category="Info", description="Коротко показать, кто автор reply-сообщения.", usage="reply .who")
async def who(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.sender_id:
        await context.edit("⚠️ Ответь на сообщение пользователя.")
        return
    entity = await context.event.client.get_entity(reply.sender_id)
    await context.edit(f"👤 {_entity_text(entity)}")


@command(name="dump", category="Test", description="Показать технические поля reply-сообщения.", usage="reply .dump")
async def dump(context: object) -> None:
    reply = await context.get_reply()
    if not reply:
        await context.edit("⚠️ Ответь на сообщение.")
        return
    data = reply.to_dict() if hasattr(reply, "to_dict") else {"id": reply.id, "text": reply.raw_text}
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    await context.edit_html(f"<pre>{html.escape(text[:3_900])}</pre>")
