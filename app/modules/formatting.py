from __future__ import annotations

from telethon.tl.types import MessageEntityBold, MessageEntityCode, MessageEntityItalic, MessageEntitySpoiler, MessageEntityStrike, MessageEntityUnderline

from app.userbot.registry import command


async def format_message(context: object, entity: object) -> None:
    text = context.raw_args
    if not text:
        reply = await context.get_reply()
        text = reply.raw_text if reply else ""
    if not text:
        await context.edit("⚠️ Добавь текст или ответь на сообщение."); return
    context.client.processed.add(context.chat_id, context.message.id)
    await context.event.edit(text, formatting_entities=[entity(0, len(text))])

def make_formatter(name: str, entity: object, description: str) -> None:
    @command(name=name, category="Форматирование", description=description, usage=f".{name} <text> или reply")
    async def handler(context: object) -> None: await format_message(context, entity)

make_formatter("bold", MessageEntityBold, "Жирный текст.")
make_formatter("italic", MessageEntityItalic, "Курсивный текст.")
make_formatter("underline", MessageEntityUnderline, "Подчёркнутый текст.")
make_formatter("strike", MessageEntityStrike, "Зачёркнутый текст.")
make_formatter("monospace", MessageEntityCode, "Моноширинный текст.")
make_formatter("spoiler", MessageEntitySpoiler, "Скрытый спойлер.")
