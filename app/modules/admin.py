from __future__ import annotations

from datetime import UTC, datetime, timedelta

from telethon import functions
from telethon.errors import ChatAdminRequiredError

from app.userbot.registry import command


async def _reply_user(context: object) -> object | None:
    reply = await context.get_reply()
    if not reply or not reply.sender_id:
        await context.edit("⚠️ Ответь на сообщение пользователя.")
        return None
    return await context.event.client.get_entity(reply.sender_id)


async def _run_admin(context: object, operation, success: str) -> None:
    try:
        await operation()
    except ChatAdminRequiredError:
        await context.edit("⚠️ Для этого действия нужны права администратора в текущем чате.")
    except Exception:
        await context.edit("⚠️ Telegram не выполнил действие: проверь права, тип чата и пользователя.")
    else:
        await context.edit(success)


@command(name="promote", category="Admin", description="Выдать пользователю права администратора по reply.", usage="reply .promote")
async def promote(context: object) -> None:
    user = await _reply_user(context)
    if user:
        await _run_admin(context, lambda: context.event.client.edit_admin(
            context.chat_id, user, is_admin=True, change_info=True, delete_messages=True,
            ban_users=True, invite_users=True, pin_messages=True
        ), "✅ Пользователь повышен до администратора.")


@command(name="demote", category="Admin", description="Снять права администратора с пользователя из reply.", usage="reply .demote")
async def demote(context: object) -> None:
    user = await _reply_user(context)
    if user:
        await _run_admin(context, lambda: context.event.client.edit_admin(context.chat_id, user, is_admin=False), "✅ Права администратора сняты.")


@command(name="pin", category="Admin", description="Закрепить reply-сообщение.", usage="reply .pin")
async def pin(context: object) -> None:
    reply = await context.get_reply()
    if not reply:
        await context.edit("⚠️ Ответь на сообщение, которое нужно закрепить.")
        return
    await _run_admin(context, lambda: context.event.client.pin_message(context.chat_id, reply, notify=False), "📌 Сообщение закреплено.")


@command(name="unpin", category="Admin", description="Снять текущее закрепление.", usage=".unpin")
async def unpin(context: object) -> None:
    await _run_admin(context, lambda: context.event.client.pin_message(context.chat_id, None), "✅ Закрепление снято.")


@command(name="kick", category="Admin", description="Исключить пользователя из чата по reply.", usage="reply .kick")
async def kick(context: object) -> None:
    user = await _reply_user(context)
    if user:
        await _run_admin(context, lambda: context.event.client.kick_participant(context.chat_id, user), "✅ Пользователь исключён.")


@command(name="ban", category="Admin", description="Забанить пользователя из reply.", usage="reply .ban")
async def ban(context: object) -> None:
    user = await _reply_user(context)
    if user:
        await _run_admin(context, lambda: context.event.client.edit_permissions(context.chat_id, user, view_messages=False), "✅ Пользователь забанен.")


@command(name="tban", category="Admin", description="Временно забанить пользователя на минуты.", usage="reply .tban <минуты>")
async def temporary_ban(context: object) -> None:
    user = await _reply_user(context)
    try:
        minutes = int(context.args[0])
        if not 1 <= minutes <= 43_200:
            raise ValueError
    except (IndexError, ValueError):
        await context.edit("⚠️ Использование: reply .tban <1–43200 минут>")
        return
    if user:
        until = datetime.now(UTC) + timedelta(minutes=minutes)
        await _run_admin(
            context,
            lambda: context.event.client.edit_permissions(context.chat_id, user, until_date=until, view_messages=False),
            f"✅ Пользователь забанен на {minutes} мин.",
        )


@command(name="unban", category="Admin", description="Снять бан с пользователя из reply.", usage="reply .unban")
async def unban(context: object) -> None:
    user = await _reply_user(context)
    if user:
        await _run_admin(context, lambda: context.event.client.edit_permissions(context.chat_id, user, view_messages=True), "✅ Бан снят.")


@command(name="mute", category="Admin", description="Запретить пользователю писать в чат.", usage="reply .mute")
async def mute(context: object) -> None:
    user = await _reply_user(context)
    if user:
        await _run_admin(context, lambda: context.event.client.edit_permissions(context.chat_id, user, send_messages=False), "🔇 Пользователь замьючен.")


@command(name="unmute", category="Admin", description="Разрешить пользователю писать в чат.", usage="reply .unmute")
async def unmute(context: object) -> None:
    user = await _reply_user(context)
    if user:
        await _run_admin(context, lambda: context.event.client.edit_permissions(context.chat_id, user, send_messages=True), "✅ Мут снят.")


@command(name="setgtitle", category="Admin", description="Изменить название текущей группы.", usage=".setgtitle <название>")
async def set_group_title(context: object) -> None:
    title = context.raw_args.strip()
    if not title or len(title) > 128:
        await context.edit("⚠️ Укажи название от 1 до 128 символов.")
        return
    await _run_admin(
        context,
        lambda: context.event.client(functions.channels.EditTitleRequest(channel=context.chat_id, title=title)),
        "✅ Название группы изменено.",
    )


async def _warns(context: object) -> dict[str, list[str]]:
    value = await context.services.settings.get(context.user_id, "admin_warns", {})
    return value if isinstance(value, dict) else {}


@command(name="warn", category="Admin", description="Выдать локальное предупреждение пользователю из reply.", usage="reply .warn [причина]")
async def warn(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.sender_id:
        await context.edit("⚠️ Ответь на сообщение пользователя.")
        return
    values = await _warns(context)
    key = f"{context.chat_id}:{reply.sender_id}"
    reasons = values.setdefault(key, [])
    reasons.append(context.raw_args.strip() or "без причины")
    values[key] = reasons[-20:]
    await context.services.settings.set(context.user_id, "admin_warns", values)
    await context.edit(f"⚠️ Варн выдан. Всего: {len(values[key])}.")


@command(name="unwarn", category="Admin", description="Снять последнее предупреждение с пользователя из reply.", usage="reply .unwarn")
async def unwarn(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.sender_id:
        await context.edit("⚠️ Ответь на сообщение пользователя.")
        return
    values = await _warns(context)
    key = f"{context.chat_id}:{reply.sender_id}"
    if not values.get(key):
        await context.edit("⚠️ У пользователя нет предупреждений.")
        return
    values[key].pop()
    if not values[key]:
        values.pop(key)
    await context.services.settings.set(context.user_id, "admin_warns", values)
    await context.edit("✅ Последний варн снят.")


@command(name="warns", category="Admin", description="Показать предупреждения пользователя из reply.", usage="reply .warns")
async def warns(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.sender_id:
        await context.edit("⚠️ Ответь на сообщение пользователя.")
        return
    reasons = (await _warns(context)).get(f"{context.chat_id}:{reply.sender_id}", [])
    if not reasons:
        await context.edit("✅ У пользователя нет предупреждений.")
        return
    lines = "\n".join(f"{index + 1}. {reason}" for index, reason in enumerate(reasons))
    await context.edit(f"⚠️ Предупреждения ({len(reasons)})\n\n{lines}")
