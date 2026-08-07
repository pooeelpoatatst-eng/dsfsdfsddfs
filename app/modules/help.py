from __future__ import annotations

from app.userbot.registry import REGISTRY, command, commands


@command(name="help", aliases=["h"], category="Остальное", description="Список команд и описание команды.", usage=".help [command]")
async def help_command(context: object) -> None:
    if context.args:
        meta = REGISTRY.get(context.args[0].removeprefix(".").lower())
        if not meta:
            await context.edit("⚠️ Команда не найдена."); return
        await context.edit(f"{meta.name.title()}\n\n.{meta.name}\n{meta.description}\n\nИспользование: {meta.usage}"); return
    grouped: dict[str, list[str]] = {}
    for meta in commands(): grouped.setdefault(meta.category, []).append(meta.name)
    lines = ["╭ Commands"] + [f"├ {category}: " + ", ".join(f".{name}" for name in sorted(names)) for category, names in grouped.items()] + ["╰ .help <command>"]
    await context.edit("\n".join(lines)[:4000])
