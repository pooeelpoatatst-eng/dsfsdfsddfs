from __future__ import annotations

from telethon import functions, types
from telethon.errors import ChatAdminRequiredError

from app.userbot.registry import command


def _name(entity: object) -> str:
    return getattr(entity, "title", None) or getattr(entity, "first_name", None) or getattr(entity, "username", None) or str(getattr(entity, "id", "—"))


async def _participants(context: object, filter: object | None = None) -> list[object]:
    kwargs = {"limit": 200}
    if filter:
        kwargs["filter"] = filter
    return await context.event.client.get_participants(context.chat_id, **kwargs)


@command(name="invite", category="Chat", description="Создать ссылку-приглашение в текущий чат.", usage=".invite")
async def invite(context: object) -> None:
    chat = await context.event.get_chat()
    username = getattr(chat, "username", None)
    if username:
        await context.edit(f"🔗 https://t.me/{username}")
        return
    link = await context.event.client(functions.messages.ExportChatInviteRequest(peer=context.chat_id))
    await context.edit(f"🔗 {link.link}")


@command(name="kickme", category="Chat", description="Выйти из текущей группы или канала.", usage=".kickme")
async def kickme(context: object) -> None:
    await context.edit("👋 Выхожу из чата.")
    await context.event.client(functions.channels.LeaveChannelRequest(channel=context.chat_id))


@command(name="members", category="Chat", description="Показать до 200 участников текущего чата.", usage=".members")
async def members(context: object) -> None:
    try:
        rows = await _participants(context)
    except ChatAdminRequiredError:
        await context.edit("⚠️ Telegram разрешает список участников только администратору этого чата.")
        return
    text = "\n".join(f"• {_name(item)}" for item in rows)
    await context.edit(f"👥 Участники ({len(rows)})\n\n{text}"[:4_000])


@command(name="admins", category="Chat", description="Показать администраторов текущего чата.", usage=".admins")
async def admins(context: object) -> None:
    rows = await _participants(context, types.ChannelParticipantsAdmins())
    text = "\n".join(f"• {_name(item)}" for item in rows)
    await context.edit(f"🛡 Администраторы ({len(rows)})\n\n{text}"[:4_000])


@command(name="bots", category="Chat", description="Показать ботов текущего чата.", usage=".bots")
async def bots(context: object) -> None:
    rows = await _participants(context, types.ChannelParticipantsBots())
    text = "\n".join(f"• {_name(item)}" for item in rows)
    await context.edit(f"🤖 Боты ({len(rows)})\n\n{text}"[:4_000] if text else "🤖 В этом чате нет ботов.")


@command(name="link", category="Chat", description="Показать публичную ссылку чата либо создать инвайт.", usage=".link")
async def link(context: object) -> None:
    await invite(context)


@command(name="common", category="Chat", description="Показать общие чаты с пользователем из reply.", usage="reply .common")
async def common(context: object) -> None:
    reply = await context.get_reply()
    if not reply:
        await context.edit("⚠️ Ответь на сообщение пользователя.")
        return
    result = await context.event.client(functions.messages.GetCommonChatsRequest(user_id=reply.sender_id, max_id=0, limit=100))
    titles = "\n".join(f"• {_name(chat)}" for chat in result.chats)
    await context.edit(f"👥 Общие чаты ({len(result.chats)})\n\n{titles}"[:4_000] if titles else "👥 Общих чатов не найдено.")
