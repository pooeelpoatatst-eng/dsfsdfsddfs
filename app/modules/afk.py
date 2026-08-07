from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.database.models import AfkState
from app.services.ai import AIUnavailableError
from app.userbot.registry import command


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
    async with client.services.settings.db.session() as session:
        state = await session.get(AfkState, client.user_id)
        if not state or not state.enabled or not event.is_private: return
    elapsed = datetime.now(timezone.utc) - state.since
    minutes = max(1, int(elapsed.total_seconds() // 60))
    ai_afk = await client.services.settings.get(client.user_id, "afk_ai", False)
    if ai_afk and client.services.ai.available:
        try:
            prompt = """Ты автоответчик человека, который сейчас AFK в Telegram. Ответь на русском кратко, дружелюбно и по смыслу входящего сообщения. Не говори, что ты AI. Обязательно упомяни, что владелец AFK и ответит позже. Максимум 2 предложения."""
            result = await client.services.ai.transform(prompt, event.raw_text[:1000])
            await client.services.usage.record_ai(client.user_id, result.prompt_tokens, result.completion_tokens)
            await event.reply(result.text[:500])
            return
        except AIUnavailableError:
            await client.services.usage.record_ai(client.user_id, error=True)
    await event.reply(f"💤 AFK {minutes} мин.\nПричина: {state.reason or 'не указана'}")


@command(name="afkai", category="AI / режимы", description="AI-автоответчик во время AFK, только личные чаты.", usage=".afkai on|off")
async def afk_ai(context: object) -> None:
    value = context.args[0].lower() if context.args else ""
    if value not in {"on", "off"}:
        await context.edit("⚠️ Использование: .afkai on или .afkai off"); return
    await context.services.settings.set(context.user_id, "afk_ai", value == "on")
    await context.delete()
