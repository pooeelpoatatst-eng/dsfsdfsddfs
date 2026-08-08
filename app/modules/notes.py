from __future__ import annotations

from app.database.repositories import NotesRepository
from app.userbot.registry import command


def _repo(context: object) -> NotesRepository:
    return NotesRepository(context.services.settings.db)


async def _save(context: object, name: str, content: str) -> None:
    if not name or len(name) > 100 or not content or len(content) > 8_000:
        await context.edit("⚠️ Имя обязательно, текст — от 1 до 8000 символов.")
        return
    await _repo(context).add(context.user_id, None, name, content)
    await context.edit(f"✅ Заметка «{name}» сохранена.")


@command(name="save", category="Notes", description="Сохранить текст или reply как заметку.", usage=".save <имя> <текст> или reply .save <имя>")
async def save(context: object) -> None:
    if not context.args:
        await context.edit("⚠️ Использование: .save <имя> <текст>")
        return
    name = context.args[0]
    content = " ".join(context.args[1:])
    if not content:
        reply = await context.get_reply()
        content = reply.raw_text if reply else ""
    await _save(context, name, content)


@command(name="note", category="Notes", description="Открыть, сохранить или удалить заметку.", usage=".note <имя> | .note add <имя> <текст> | .note del <имя>")
async def note(context: object) -> None:
    if not context.args:
        await context.edit("⚠️ Использование: .note <имя> или .note add <имя> <текст>")
        return
    action = context.args[0].lower()
    if action == "add":
        if len(context.args) < 2:
            await context.edit("⚠️ Укажи имя заметки.")
            return
        name, content = context.args[1], " ".join(context.args[2:])
        if not content:
            reply = await context.get_reply()
            content = reply.raw_text if reply else ""
        await _save(context, name, content)
        return
    if action == "del":
        if len(context.args) != 2:
            await context.edit("⚠️ Использование: .note del <имя>")
            return
        removed = await _repo(context).delete(context.user_id, context.args[1])
        await context.edit("✅ Заметка удалена." if removed else "⚠️ Заметка не найдена.")
        return
    saved = await _repo(context).get(context.user_id, context.chat_id, action)
    await context.edit(saved.content if saved else "⚠️ Заметка не найдена.")


@command(name="notes", category="Notes", description="Показать все сохранённые заметки.", usage=".notes")
async def notes(context: object) -> None:
    rows = await _repo(context).list(context.user_id, context.chat_id)
    names = "\n".join(f"• {row.name}" for row in rows)
    await context.edit(f"📝 Заметки\n\n{names}" if names else "📝 Заметок пока нет.")


@command(name="delnote", category="Notes", description="Удалить заметку по имени.", usage=".delnote <имя>")
async def delnote(context: object) -> None:
    if not context.args:
        await context.edit("⚠️ Использование: .delnote <имя>")
        return
    removed = await _repo(context).delete(context.user_id, context.args[0])
    await context.edit("✅ Заметка удалена." if removed else "⚠️ Заметка не найдена.")


@command(name="delallnotes", category="Notes", description="Удалить все свои заметки.", usage=".delallnotes")
async def delallnotes(context: object) -> None:
    count = await _repo(context).clear(context.user_id)
    await context.edit(f"✅ Удалено заметок: {count}.")
