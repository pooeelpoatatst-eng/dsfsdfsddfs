from __future__ import annotations

from app.database.repositories import NotesRepository
from app.userbot.registry import command


@command(name="note", category="Инструменты", description="Сохранить или отправить заметку.", usage=".note add NAME TEXT | .note NAME | .note del NAME")
async def note(context: object) -> None:
    repo = NotesRepository(context.services.settings.db)
    if not context.args:
        await context.edit("⚠️ Использование: .note add NAME TEXT"); return
    action = context.args[0].lower()
    if action == "add":
        if len(context.args) < 2: await context.edit("⚠️ Укажи имя заметки."); return
        name = context.args[1]
        content = " ".join(context.args[2:])
        if not content:
            reply = await context.get_reply(); content = reply.raw_text if reply else ""
        if not content or len(content) > 8000: await context.edit("⚠️ Текст заметки обязателен и не длиннее 8000 символов."); return
        await repo.add(context.user_id, None, name, content); await context.edit(f"✅ Заметка `{name}` сохранена."); return
    if action == "del":
        await context.edit("⚠️ Удаление заметок пока недоступно через этот MVP."); return
    saved = await repo.get(context.user_id, context.chat_id, action)
    await context.edit(saved.content if saved else "⚠️ Заметка не найдена.")


@command(name="notes", category="Инструменты", description="Список заметок.", usage=".notes")
async def notes(context: object) -> None:
    rows = await NotesRepository(context.services.settings.db).list(context.user_id, context.chat_id)
    await context.edit("📝 Notes\n" + ("\n".join(f"• {row.name}" for row in rows) if rows else "Нет заметок."))
