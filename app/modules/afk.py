from __future__ import annotations

from datetime import datetime, timezone
import time

from sqlalchemy import select

from app.database.models import AfkState
from app.services.ai import AIUnavailableError
from app.userbot.registry import command

_last_ai_reply: dict[tuple[int, int, int], float] = {}
AI_REPLY_COOLDOWN_SECONDS = 2


@command(name="afk", category="AI / режимы", description="Автоответ при AFK.", usage=".afk [reason|off|status]")
async def afk(context: object) -> None:
    arg = context.raw_args.strip()
    async with context.services.settings.db.session() as session:
        state = await session.get(AfkState, context.user_id)
        if not state: state = AfkState(user_id=context.user_id); session.add(state)
        if arg.lower() == "off":
            state.enabled = False; await context.edit("💤 AFK выключен."); return
        if arg.lower() == "status":
            await context.edit("💤 AFK: " + (f"ON, {state.reason or 'без причины'}" if state.enabled else "OFF")); return
        state.enabled, state.since, state.reason = True, datetime.now(timezone.utc), arg[:500] or None
    await context.edit(f"💤 AFK включён{': ' + arg[:500] if arg else ''}")


async def maybe_reply_afk(client: object, event: object) -> None:
    # AI chat mode is independent from AFK and is enabled per current chat.
    # A per-sender cooldown prevents the account from replying to every line.
    ai_chats = await client.services.settings.get(client.user_id, "afk_ai_chats", [])
    if event.chat_id in ai_chats and client.services.ai.available:
        key = (client.user_id, event.chat_id, event.sender_id)
        now = time.monotonic()
        if now - _last_ai_reply.get(key, 0) < AI_REPLY_COOLDOWN_SECONDS:
            return
        try:
            history = []
            async for message in client.iter_messages(event.chat_id, limit=6):
                if message.raw_text:
                    speaker = "я" if message.out else "собеседник"
                    history.append(f"{speaker}: {message.raw_text[:300]}")
            prompt = """Пиши от первого лица как молодой русскоязычный человек в обычном Telegram-чате. Ответь естественно, учитывая последние сообщения диалога. Только нижний регистр. Не используй точки, восклицательные знаки, кавычки, markdown, упоминания AI, бота, автоответа, AFK или отсутствия человека. Разговорная речь и мягкий сленг допустимы, но не оскорбляй и не угрожай. Не отвечай пустым сообщением. Одно короткое сообщение, максимум 180 символов."""
            result = await client.services.ai.transform(prompt, "\n".join(reversed(history))[:1800])
            await client.services.usage.record_ai(client.user_id, result.prompt_tokens, result.completion_tokens)
            text = result.text.lower().replace("\n", " ").strip().rstrip(".!?")[:180]
            if text:
                _last_ai_reply[key] = now
                await event.reply(text)
            return
        except AIUnavailableError:
            await client.services.usage.record_ai(client.user_id, error=True)
            return
    async with client.services.settings.db.session() as session:
        state = await session.get(AfkState, client.user_id)
        if not state or not state.enabled or not event.is_private: return
    elapsed = datetime.now(timezone.utc) - state.since
    minutes = max(1, int(elapsed.total_seconds() // 60))
    await event.reply(f"💤 AFK {minutes} мин.\nПричина: {state.reason or 'не указана'}")


@command(name="afkai", category="AI / режимы", description="AI общается в текущем чате от твоего имени.", usage=".afkai on|off")
async def afk_ai(context: object) -> None:
    value = context.args[0].lower() if context.args else ""
    if value not in {"on", "off"}:
        await context.edit("⚠️ Использование: .afkai on или .afkai off"); return
    chats = await context.services.settings.get(context.user_id, "afk_ai_chats", [])
    chats = [int(chat_id) for chat_id in chats]
    if value == "on" and context.chat_id not in chats:
        chats.append(context.chat_id)
    if value == "off":
        chats = [chat_id for chat_id in chats if chat_id != context.chat_id]
    await context.services.settings.set(context.user_id, "afk_ai_chats", chats)
    await context.delete()
