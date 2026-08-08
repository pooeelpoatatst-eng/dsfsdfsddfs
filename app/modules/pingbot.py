from __future__ import annotations

from telethon import types

from app.userbot.registry import command


KEY = "ping_bots"


async def _bots(context: object) -> dict[str, str]:
    value = await context.services.settings.get(context.user_id, KEY, {})
    return value if isinstance(value, dict) else {}


@command(name="addpingbot", category="PingBot", description="Добавить бота в свой список ручного ping.", usage=".addpingbot @bot")
async def add_ping_bot(context: object) -> None:
    target = context.raw_args.strip()
    if not target:
        await context.edit("⚠️ Использование: .addpingbot @bot")
        return
    try:
        entity = await context.event.client.get_entity(target)
    except (TypeError, ValueError):
        await context.edit("⚠️ Бот не найден.")
        return
    if not isinstance(entity, types.User) or not entity.bot:
        await context.edit("⚠️ Укажи username именно Telegram-бота.")
        return
    saved = await _bots(context)
    saved[str(entity.id)] = "@" + (entity.username or str(entity.id))
    await context.services.settings.set(context.user_id, KEY, saved)
    await context.edit(f"✅ {saved[str(entity.id)]} добавлен.")


@command(name="delpingbot", category="PingBot", description="Удалить бота из списка.", usage=".delpingbot @bot")
async def delete_ping_bot(context: object) -> None:
    target = context.raw_args.strip().removeprefix("@").casefold()
    saved = await _bots(context)
    removed = [key for key, value in saved.items() if value.removeprefix("@").casefold() == target or key == target]
    for key in removed:
        saved.pop(key, None)
    await context.services.settings.set(context.user_id, KEY, saved)
    await context.edit("✅ Бот удалён." if removed else "⚠️ Этого бота нет в списке.")


@command(name="pingbots", category="PingBot", description="Показать сохранённых ботов для ручного ping.", usage=".pingbots")
async def ping_bots(context: object) -> None:
    saved = await _bots(context)
    await context.edit("🤖 Ping bots\n\n" + ("\n".join(f"• {name}" for name in saved.values()) if saved else "Список пуст."))


@command(name="pingnow", category="PingBot", description="Отправить /start сохранённым ботам, максимум 10.", usage=".pingnow")
async def ping_now(context: object) -> None:
    saved = await _bots(context)
    if not saved:
        await context.edit("⚠️ Список пуст. Добавь бота через .addpingbot")
        return
    sent = 0
    for identifier in list(saved)[:10]:
        try:
            message = await context.event.client.send_message(int(identifier), "/start")
            context.client.mark_internal(message)
            sent += 1
        except Exception:
            continue
    await context.edit(f"✅ Отправлено /start ботам: {sent}.")
