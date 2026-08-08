from __future__ import annotations

import html

from app.userbot.registry import command


def _quote_html(author: str, text: str, fake: bool = False) -> str:
    badge = " <i>— фейковая цитата</i>" if fake else ""
    return f"<b>{html.escape(author)}</b>{badge}\n<blockquote>{html.escape(text)}</blockquote>"


@command(name="quote", category="Quotes", description="Оформить reply-сообщение как цитату.", usage="reply .quote")
async def quote(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.raw_text:
        await context.edit("⚠️ Ответь на текстовое сообщение.")
        return
    sender = await reply.get_sender()
    author = getattr(sender, "first_name", None) or getattr(sender, "title", None) or "Пользователь"
    await context.edit_html(_quote_html(author, reply.raw_text))


@command(name="fakequote", category="Quotes", description="Сделать явно помеченную фейковую цитату.", usage=".fakequote <имя> | <текст>")
async def fakequote(context: object) -> None:
    author, separator, text = context.raw_args.partition("|")
    if not separator or not author.strip() or not text.strip():
        await context.edit("⚠️ Использование: .fakequote <имя> | <текст>")
        return
    await context.edit_html(_quote_html(author.strip(), text.strip(), fake=True))
