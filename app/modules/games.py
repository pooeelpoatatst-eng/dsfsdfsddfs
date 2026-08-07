from __future__ import annotations

import random
from dataclasses import dataclass

from telethon.tl import functions, types

from app.games.tictactoe import TicTacToe
from app.userbot.registry import command

@dataclass
class Match:
    game: TicTacToe
    owner_id: int
    opponent_id: int

_games: dict[int, Match] = {}

@command(name="flip", category="Игры", description="Подбросить монету.", usage=".flip")
async def flip(context: object) -> None: await context.edit("🪙 " + random.choice(["Орёл", "Решка"]))

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

async def render(context: object, match: Match, reply_to: int | None = None) -> None:
    player = match.owner_id if match.game.turn == "X" else match.opponent_id
    message = await context.event.client.send_message(context.chat_id, "🎮 Tic-tac-toe\n" + match.game.render() + f"\nХод: {'X' if match.game.turn == 'X' else 'O'} (`{player}`): .ttt <1-9>", reply_to=reply_to)
    context.client.mark_internal(message)

@command(name="ttt", category="Игры", description="Крестики-нолики с reply-пользователем.", usage=".ttt <@user/reply> | .ttt 1-9")
async def ttt(context: object) -> None:
    match = _games.get(context.chat_id)
    if context.args and context.args[0].lower() == "stop":
        _games.pop(context.chat_id, None); await context.delete(); return
    if context.args and context.args[0].isdigit():
        if not match or match.owner_id != context.client.telegram_user_id:
            await context.edit("⚠️ Начни игру reply-командой `.ttt`."); return
        if match.game.turn != "X": await context.edit("⚠️ Сейчас ход соперника."); return
        try: winner = match.game.move(int(context.args[0]))
        except ValueError: await context.edit("⚠️ Эта клетка занята."); return
        await context.delete()
        if winner:
            _games.pop(context.chat_id, None)
            message = await context.event.client.send_message(context.chat_id, match.game.render() + "\n🏆 Ты победил!")
            context.client.mark_internal(message); return
        await render(context, match); return
    reply = await context.get_reply()
    if not reply or not reply.sender_id or reply.sender_id == context.client.telegram_user_id:
        await context.edit("⚠️ Ответь на сообщение соперника: `.ttt`"); return
    _games[context.chat_id] = Match(TicTacToe(), context.client.telegram_user_id, reply.sender_id)
    await context.delete()
    await render(context, _games[context.chat_id], reply.id)


async def handle_opponent_move(client: object, event: object) -> None:
    match = _games.get(event.chat_id)
    text = (event.raw_text or "").strip()
    if not match or event.sender_id != match.opponent_id or match.game.turn != "O" or not text.startswith(".ttt "):
        return
    try: cell = int(text.split(maxsplit=1)[1])
    except ValueError: return
    try: winner = match.game.move(cell)
    except ValueError:
        message = await event.reply("⚠️ Эта клетка занята. Выбери другую: `.ttt 1-9`"); client.mark_internal(message); return
    if winner:
        _games.pop(event.chat_id, None)
        message = await event.reply(match.game.render() + "\n🏆 Соперник победил!"); client.mark_internal(message); return
    message = await event.reply("🎮 Tic-tac-toe\n" + match.game.render() + "\nТвой ход: `.ttt <1-9>`")
    client.mark_internal(message)
