from __future__ import annotations

from telethon.tl import functions, types

from app.userbot.registry import command


@command(name="del", aliases=["delete"], category="Сообщения", description="Удалить своё сообщение или reply-сообщение.", usage=".del или reply .del")
async def delete_message(context: object) -> None:
    reply = await context.get_reply()
    if reply: await context.event.client.delete_messages(context.chat_id, [reply.id])
    await context.delete()

@command(name="edit", category="Сообщения", description="Изменить reply на новый текст.", usage="reply .edit <text>", requires_reply=True)
async def edit_reply(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not context.raw_args:
        await context.edit("⚠️ Reply на своё сообщение: .edit новый текст"); return
    await context.event.client.edit_message(context.chat_id, reply.id, context.raw_args)
    await context.delete()

@command(name="repeat", aliases=["rep"], category="Сообщения", description="Повторить текст несколько раз.", usage=".repeat 3 text")
async def repeat(context: object) -> None:
    try: amount = min(max(int(context.args[0]), 1), 20)
    except (ValueError, IndexError): await context.edit("⚠️ .repeat 3 text"); return
    text = " ".join(context.args[1:])
    await context.edit("\n".join(text for _ in range(amount))[:4000] if text else "⚠️ Добавь текст.")

@command(name="id", category="Чаты", description="Показать ID чата и reply-пользователя.", usage=".id [reply]")
async def ids(context: object) -> None:
    reply = await context.get_reply(); text = f"chat: `{context.chat_id}`"
    if reply: text += f"\nuser: `{reply.sender_id}`\nmessage: `{reply.id}`"
    await context.edit(text)

@command(name="chatinfo", category="Чаты", description="Информация о текущем чате.", usage=".chatinfo")
async def chat_info(context: object) -> None:
    entity = await context.event.client.get_entity(context.chat_id)
    title = getattr(entity, "title", None) or getattr(entity, "first_name", "unknown")
    await context.edit(f"💬 {title}\nID: `{context.chat_id}`\nType: {entity.__class__.__name__}")

@command(name="copy", category="Сообщения", description="Переслать reply без подписи.", usage="reply .copy")
async def copy(context: object) -> None:
    reply = await context.get_reply()
    if not reply: await context.edit("⚠️ Ответь на сообщение."); return
    result = await context.event.client.forward_messages(context.chat_id, reply, from_peer=context.chat_id, drop_author=True)
    for message in result if isinstance(result, list) else [result]: context.client.mark_internal(message)
    await context.delete()

@command(name="react", category="Сообщения", description="Поставить реакцию на reply.", usage="reply .react ❤️")
async def react(context: object) -> None:
    reply = await context.get_reply()
    if not reply: await context.edit("⚠️ Ответь на сообщение."); return
    await context.event.client(functions.messages.SendReactionRequest(peer=context.chat_id, msg_id=reply.id, reaction=[types.ReactionEmoji(emoticon=context.raw_args or "❤️")]))
    await context.delete()
