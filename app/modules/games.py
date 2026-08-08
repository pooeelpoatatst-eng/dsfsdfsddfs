from __future__ import annotations

import random

from telethon.tl import functions, types

from app.userbot.registry import command


async def _display_name(event: object) -> str:
    sender = await event.get_sender()
    return getattr(sender, "first_name", None) or getattr(sender, "username", None) or "Игрок"


async def _start(context: object, method: str, *args: object, reply_to: int | None = None) -> None:
    try:
        await getattr(context.services.games, method)(context.chat_id, *args, reply_to=reply_to)
    except Exception:
        # The bot must be able to post in the selected chat. Most commonly it
        # hasn't been added to a group yet or has no permission to send.
        await context.edit("⚠️ Не смог отправить игровое поле. Добавь control bot в этот чат и дай ему право писать сообщения.")
        return
    await context.delete()


@command(name="flip", category="Игры", description="Подбросить монету.", usage=".flip")
async def flip(context: object) -> None:
    await context.edit("🪙 " + random.choice(["Орёл", "Решка"]))


@command(name="dice", category="Игры", description="Бросить кубик Telegram.", usage=".dice")
async def dice(context: object) -> None:
    peer = await context.event.client.get_input_entity(context.chat_id)
    await context.event.client(functions.messages.SendMediaRequest(
        peer=peer,
        media=types.InputMediaDice(emoticon="🎲"),
        message="",
        random_id=random.randrange(-(2**63), 2**63),
    ))
    await context.delete()


@command(name="ttt", category="Игры", description="Кнопочные крестики-нолики с пользователем в reply.", usage=".ttt (reply на соперника)")
async def ttt(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.sender_id or reply.sender_id == context.client.telegram_user_id:
        await context.edit("⚠️ Ответь `.ttt` на сообщение соперника.")
        return
    await _start(
        context,
        "start_ttt",
        context.client.telegram_user_id,
        reply.sender_id,
        await _display_name(context.event),
        await _display_name(reply),
        reply_to=reply.id,
    )


@command(name="2048", category="Игры", description="Кнопочная игра 2048.", usage=".2048")
async def game_2048(context: object) -> None:
    await _start(context, "start_2048", context.client.telegram_user_id, await _display_name(context.event))


@command(name="rps", aliases=["камень"], category="Игры", description="Камень, ножницы, бумага с пользователем в reply.", usage=".rps (reply на соперника)")
async def rps(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.sender_id or reply.sender_id == context.client.telegram_user_id:
        await context.edit("⚠️ Ответь `.rps` на сообщение соперника.")
        return
    await _start(
        context,
        "start_rps",
        context.client.telegram_user_id,
        reply.sender_id,
        await _display_name(context.event),
        await _display_name(reply),
        reply_to=reply.id,
    )


@command(name="guess", aliases=["угадай"], category="Игры", description="Угадай число кнопками.", usage=".guess")
async def guess(context: object) -> None:
    await _start(context, "start_guess", context.client.telegram_user_id)


@command(name="wordly", aliases=["wordle"], category="Игры", description="Угадай русское слово из 5 букв кнопками.", usage=".wordly")
async def wordly(context: object) -> None:
    await _start(context, "start_wordly", context.client.telegram_user_id)
