from __future__ import annotations

from app.userbot.registry import command


@command(name="alwaysonline", category="Онлайн", description="Поддерживать статус «в сети» с безопасным интервалом.", usage=".alwaysonline on | off | status")
async def always_online(context: object) -> None:
    action = (context.args[0].lower() if context.args else "status")
    if action not in {"on", "off", "status"}:
        await context.edit("⚠️ Использование: .alwaysonline on, off или status")
        return
    if action == "status":
        enabled = await context.services.settings.get(context.user_id, "always_online", False)
        await context.edit(f"🟢 Always online: {'включён' if enabled else 'выключен'}")
        return
    enabled = action == "on"
    await context.services.settings.set(context.user_id, "always_online", enabled)
    await context.edit(f"✅ Always online {'включён' if enabled else 'выключен'}.")


@command(name="stats", category="Stats", description="Показать самые используемые команды.", usage=".stats")
async def stats(context: object) -> None:
    rows = await context.services.usage.commands(context.user_id)
    if not rows:
        await context.edit("📊 Статистики пока нет. Воспользуйся несколькими командами.")
        return
    lines = "\n".join(f"• .{row.command} — {row.count}" for row in rows)
    await context.edit(f"📊 Топ команд\n\n{lines}")
