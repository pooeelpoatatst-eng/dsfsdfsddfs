from __future__ import annotations

from app.userbot.registry import command


MAX_DELETE = 100


def _limit(args: list[str], default: int = 25) -> int | None:
    try:
        value = int(args[0]) if args else default
    except ValueError:
        return None
    return value if 1 <= value <= MAX_DELETE else None


async def _purge(context: object) -> None:
    reply = await context.get_reply()
    if not reply:
        await context.edit("⚠️ Ответь на первое сообщение диапазона.")
        return
    count = context.message.id - reply.id + 1
    if count < 1 or count > MAX_DELETE:
        await context.edit(f"⚠️ Можно удалить от 1 до {MAX_DELETE} сообщений за раз. Сейчас: {count}.")
        return
    await context.event.client.delete_messages(context.chat_id, list(range(reply.id, context.message.id + 1)))


@command(name="purge", category="Purger", description="Удалить диапазон от reply до команды, максимум 100 сообщений.", usage="reply .purge")
async def purge(context: object) -> None:
    await _purge(context)


@command(name="rpurge", category="Purger", description="Безопасный purge диапазона от reply до команды.", usage="reply .rpurge")
async def reverse_purge(context: object) -> None:
    await _purge(context)


@command(name="delme", category="Purger", description="Удалить свои последние сообщения в текущем чате, максимум 100.", usage=".delme [количество]")
async def delete_my(context: object) -> None:
    limit = _limit(context.args)
    if limit is None:
        await context.edit("⚠️ Количество — от 1 до 100.")
        return
    messages = []
    async for message in context.event.client.iter_messages(context.chat_id, from_user="me", limit=limit + 1):
        messages.append(message.id)
    if context.message.id not in messages:
        messages.append(context.message.id)
    await context.event.client.delete_messages(context.chat_id, messages[: limit + 1])


@command(name="delmenow", category="Purger", description="Удалить текущую команду без другого действия.", usage=".delmenow")
async def delete_me_now(context: object) -> None:
    await context.delete()


@command(name="delword", category="Purger", description="Удалить свои сообщения с указанным словом, максимум 100.", usage=".delword <слово> [количество]")
async def delete_word(context: object) -> None:
    if not context.args:
        await context.edit("⚠️ Использование: .delword <слово> [количество]")
        return
    word = context.args[0].casefold()
    limit = _limit(context.args[1:], 25)
    if limit is None:
        await context.edit("⚠️ Количество — от 1 до 100.")
        return
    found = []
    async for message in context.event.client.iter_messages(context.chat_id, from_user="me", limit=2_000):
        if word in (message.raw_text or "").casefold():
            found.append(message.id)
            if len(found) >= limit:
                break
    if not found:
        await context.edit("Ничего не найдено.")
        return
    found.append(context.message.id)
    await context.event.client.delete_messages(context.chat_id, found)
