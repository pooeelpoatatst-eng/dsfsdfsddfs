from __future__ import annotations

import html
from collections import defaultdict

from app.userbot.registry import REGISTRY, CommandMeta, command, commands


CATEGORY_TITLES = {
    "AI / полезное": "🤖 AI и тексты",
    "AI / режимы": "✨ Режимы",
    "Анимации": "🌈 Анимации",
    "Игры": "🎮 Игры",
    "Инструменты": "🧰 Утилиты",
    "Музыка": "🎵 Музыка",
    "Профиль": "👤 Профиль",
    "Сообщения": "💬 Сообщения",
    "Форматирование": "✍️ Форматирование",
    "Чаты": "👥 Чаты",
    "Общение": "💭 Общение",
    "Остальное": "⚙️ Остальное",
}


def _command_lines(metas: list[CommandMeta], width: int = 42) -> list[str]:
    result: list[str] = []
    current = ""
    for meta in sorted(metas, key=lambda item: item.name):
        for name in (meta.name, *meta.aliases):
            token = f".{name}"
            candidate = f"{current} | {token}" if current else token
            if current and len(candidate) > width:
                result.append(current)
                current = token
            else:
                current = candidate
    if current:
        result.append(current)
    return result or ["—"]


def module_table(category: str, metas: list[CommandMeta]) -> str:
    """Compact fixed-width table that stays readable in Telegram's pre block."""
    left, right = 15, 44
    border = f"├{'─' * left}┼{'─' * right}┤"
    lines = [
        f"┌{'─' * left}┬{'─' * right}┐",
        f"│ {'Модуль':<{left - 2}} │ {'Команды':<{right - 2}} │",
        border,
    ]
    label = category[: left - 2]
    for index, value in enumerate(_command_lines(metas, right - 2)):
        lines.append(f"│ {(label if index == 0 else ''):<{left - 2}} │ {value:<{right - 2}} │")
    lines.append(f"└{'─' * left}┴{'─' * right}┘")
    return "\n".join(lines)


def help_pages(limit: int = 3_700) -> list[str]:
    grouped: dict[str, list[CommandMeta]] = defaultdict(list)
    for meta in commands():
        grouped[meta.category].append(meta)
    header = "<b>📚 Команды</b>"
    footer = "\n\n<i>.help &lt;команда&gt; — назначение и использование</i>"
    blocks: list[str] = []
    for category in sorted(grouped, key=lambda item: CATEGORY_TITLES.get(item, item)):
        title = CATEGORY_TITLES.get(category, category)
        blocks.append(f"<b>{html.escape(title)}</b>\n<pre>{html.escape(module_table(category, grouped[category]))}</pre>")
    pages: list[str] = []
    current = header
    for block in blocks:
        candidate = f"{current}\n\n{block}"
        if len(candidate) > limit - len(footer) and current != header:
            pages.append(current)
            current = header + "\n\n" + block
        else:
            current = candidate
    pages.append(current + footer)
    return pages


def help_menu() -> str:
    """Compatibility helper for a single-page command set and unit tests."""
    return "\n\n".join(help_pages())


def compact_menu() -> str:
    grouped: dict[str, list[CommandMeta]] = defaultdict(list)
    for meta in commands():
        grouped[meta.category].append(meta)
    rows = []
    for category in sorted(grouped, key=lambda item: CATEGORY_TITLES.get(item, item)):
        title = CATEGORY_TITLES.get(category, category)
        plain = title.split(" ", 1)[-1]
        rows.append(f"• <code>.help {html.escape(category)}</code> — {html.escape(plain)}")
    return (
        "<b>📚 Команды</b>\n"
        "<i>.help &lt;команда&gt; — описание и использование</i>\n"
        "<i>.help &lt;модуль&gt; — таблица модуля</i>\n\n"
        + "\n".join(rows)
    )


@command(
    name="help",
    aliases=["h"],
    category="Остальное",
    description="Табличный список команд и подробности отдельной команды.",
    usage=".help [команда]",
)
async def help_command(context: object) -> None:
    if context.args:
        query = context.args[0].removeprefix(".").lower()
        meta = REGISTRY.get(query)
        if not meta:
            grouped: dict[str, list[CommandMeta]] = defaultdict(list)
            for item in commands():
                grouped[item.category].append(item)
            category = next(
                (
                    name for name, values in grouped.items()
                    if query in {name.lower(), CATEGORY_TITLES.get(name, name).lower(), values[0].module.lower()}
                ),
                None,
            )
            if not category:
                await context.edit("⚠️ Команда или модуль не найдены. Открой .help.")
                return
            await context.edit_html(
                f"<b>{html.escape(CATEGORY_TITLES.get(category, category))}</b>\n"
                f"<pre>{html.escape(module_table(category, grouped[category]))}</pre>"
            )
            return
        aliases = f"\nАлиасы: {', '.join(f'.{alias}' for alias in meta.aliases)}" if meta.aliases else ""
        await context.edit_html(
            f"<b>.{html.escape(meta.name)}</b>\n\n{html.escape(meta.description)}{html.escape(aliases)}"
            f"\n\n<b>Использование</b>\n<code>{html.escape(meta.usage)}</code>"
        )
        return
    await context.edit_html(compact_menu())
