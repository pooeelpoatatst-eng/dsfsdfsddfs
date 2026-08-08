from __future__ import annotations

import re
import asyncio
import os

from app.constants import DEFAULT_MODULES
from app.userbot.registry import REGISTRY, command, commands


ALIAS_RE = re.compile(r"^[a-z][a-z0-9_]{0,24}$")


def _modules() -> dict[str, bool]:
    return {meta.module: True for meta in commands()} | DEFAULT_MODULES


@command(name="settings", category="Core", description="Показать активные настройки userbot.", usage=".settings")
async def settings(context: object) -> None:
    prefix = await context.services.settings.get(context.user_id, "command_prefix", ".")
    language = await context.services.settings.get(context.user_id, "language", "ru")
    aliases = await context.services.settings.get(context.user_id, "command_aliases", {})
    await context.edit(
        "⚙️ Настройки\n\n"
        f"Префикс: <code>{prefix}</code>\nЯзык: {language}\n"
        f"Алиасов: {len(aliases) if isinstance(aliases, dict) else 0}\n\n"
        "Изменить: .setprefix, .lang, .preset, .addalias"
    )


@command(name="setprefix", category="Core", description="Сменить префикс команд для своего аккаунта.", usage=".setprefix !")
async def setprefix(context: object) -> None:
    prefix = context.raw_args.strip()
    if not prefix or len(prefix) > 3 or any(char.isspace() or char.isalnum() for char in prefix):
        await context.edit("⚠️ Префикс — от 1 до 3 небуквенных символов, например: ! или ;;")
        return
    await context.services.settings.set(context.user_id, "command_prefix", prefix)
    await context.edit(f"✅ Новый префикс: {prefix}\nТеперь команды начинаются так: {prefix}help")


@command(name="lang", category="Core", description="Сохранить язык интерфейса: ru или en.", usage=".lang ru | en")
async def lang(context: object) -> None:
    value = (context.args[0].lower() if context.args else "")
    if value not in {"ru", "en"}:
        await context.edit("⚠️ Использование: .lang ru или .lang en")
        return
    await context.services.settings.set(context.user_id, "language", value)
    await context.edit(f"✅ Язык интерфейса сохранён: {value.upper()}")


@command(name="preset", category="Core", description="Включить полный или базовый набор модулей.", usage=".preset all | basic")
async def preset(context: object) -> None:
    value = (context.args[0].lower() if context.args else "all")
    modules = _modules()
    if value == "all":
        chosen = modules
    elif value == "basic":
        basic = {"core", "help", "tools", "chat_tools", "notes", "formatting", "music"}
        chosen = {name: name in basic for name in modules}
    else:
        await context.edit("⚠️ Использование: .preset all или .preset basic")
        return
    await context.services.settings.set(context.user_id, "modules", chosen)
    await context.edit(f"✅ Набор «{value}» сохранён. Включено модулей: {sum(chosen.values())}.")


@command(name="addalias", category="Core", description="Создать свой короткий алиас для существующей команды.", usage=".addalias <алиас> <команда>")
async def addalias(context: object) -> None:
    if len(context.args) != 2:
        await context.edit("⚠️ Использование: .addalias <алиас> <команда>")
        return
    alias, target = context.args[0].lower(), context.args[1].removeprefix(".").lower()
    if not ALIAS_RE.fullmatch(alias) or alias in REGISTRY:
        await context.edit("⚠️ Алиас: латинские буквы, цифры и _, без совпадения со встроенной командой.")
        return
    if target not in REGISTRY:
        await context.edit("⚠️ Такой команды нет. Проверь через .help.")
        return
    aliases = await context.services.settings.get(context.user_id, "command_aliases", {})
    aliases = aliases if isinstance(aliases, dict) else {}
    aliases[alias] = REGISTRY[target].name
    await context.services.settings.set(context.user_id, "command_aliases", aliases)
    await context.edit(f"✅ .{alias} → .{REGISTRY[target].name}")


@command(name="delalias", category="Core", description="Удалить свой алиас.", usage=".delalias <алиас>")
async def delalias(context: object) -> None:
    alias = (context.args[0].lower() if context.args else "")
    aliases = await context.services.settings.get(context.user_id, "command_aliases", {})
    aliases = aliases if isinstance(aliases, dict) else {}
    if alias not in aliases:
        await context.edit("⚠️ Такого пользовательского алиаса нет.")
        return
    aliases.pop(alias)
    await context.services.settings.set(context.user_id, "command_aliases", aliases)
    await context.edit(f"✅ Алиас .{alias} удалён.")


@command(name="aliases", category="Core", description="Показать пользовательские алиасы.", usage=".aliases")
async def aliases(context: object) -> None:
    saved = await context.services.settings.get(context.user_id, "command_aliases", {})
    if not isinstance(saved, dict) or not saved:
        await context.edit("У тебя пока нет алиасов. Пример: .addalias пинг ping")
        return
    lines = "\n".join(f"• .{name} → .{target}" for name, target in sorted(saved.items()))
    await context.edit(f"🏷 Алиасы\n\n{lines}")


@command(name="restart", category="Core", description="Перезапустить worker userbot после подтверждения в чате.", usage=".restart")
async def restart(context: object) -> None:
    await context.edit("🔄 Перезапускаю worker…")

    async def stop_worker() -> None:
        await asyncio.sleep(1)
        os._exit(0)

    asyncio.create_task(stop_worker())
