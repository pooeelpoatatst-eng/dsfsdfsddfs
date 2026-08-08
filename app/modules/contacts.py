from __future__ import annotations

from telethon import functions, types

from app.userbot.registry import command


async def _reply_entity(context: object) -> tuple[object, object] | tuple[None, None]:
    reply = await context.get_reply()
    if not reply:
        return None, None
    return reply, await context.event.client.get_entity(reply.sender_id)


@command(name="block", category="Contacts", description="Заблокировать пользователя из reply.", usage="reply .block")
async def block(context: object) -> None:
    _, entity = await _reply_entity(context)
    if not entity:
        await context.edit("⚠️ Ответь на сообщение пользователя командой .block")
        return
    await context.event.client(functions.contacts.BlockRequest(entity))
    await context.edit("✅ Пользователь заблокирован.")


@command(name="unblock", category="Contacts", description="Разблокировать пользователя из reply.", usage="reply .unblock")
async def unblock(context: object) -> None:
    _, entity = await _reply_entity(context)
    if not entity:
        await context.edit("⚠️ Ответь на сообщение пользователя командой .unblock")
        return
    await context.event.client(functions.contacts.UnblockRequest(entity))
    await context.edit("✅ Пользователь разблокирован.")


@command(name="addcontact", category="Contacts", description="Добавить пользователя из reply в контакты.", usage="reply .addcontact")
async def addcontact(context: object) -> None:
    _, entity = await _reply_entity(context)
    if not isinstance(entity, types.User):
        await context.edit("⚠️ Ответь на сообщение обычного пользователя.")
        return
    await context.event.client(
        functions.contacts.AddContactRequest(
            id=entity,
            first_name=entity.first_name or "Telegram",
            last_name=entity.last_name or "",
            phone=entity.phone or "",
            add_phone_privacy_exception=False,
        )
    )
    await context.edit("✅ Контакт добавлен.")


@command(name="delcontact", category="Contacts", description="Удалить пользователя из контактов по reply.", usage="reply .delcontact")
async def delcontact(context: object) -> None:
    _, entity = await _reply_entity(context)
    if not isinstance(entity, types.User):
        await context.edit("⚠️ Ответь на сообщение пользователя.")
        return
    await context.event.client(functions.contacts.DeleteContactsRequest(id=[entity]))
    await context.edit("✅ Контакт удалён.")


@command(name="report", category="Contacts", description="Пожаловаться на reply-сообщение как спам.", usage="reply .report [комментарий]")
async def report(context: object) -> None:
    reply, _ = await _reply_entity(context)
    if not reply:
        await context.edit("⚠️ Ответь на сообщение, на которое нужно пожаловаться.")
        return
    await context.event.client(
        functions.messages.ReportRequest(
            peer=context.chat_id,
            id=[reply.id],
            reason=types.InputReportReasonSpam(),
            message=context.raw_args[:512],
        )
    )
    await context.edit("✅ Жалоба на выбранное сообщение отправлена.")
