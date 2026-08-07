from __future__ import annotations

import random

from app.games.tictactoe import TicTacToe
from app.userbot.registry import command

_games: dict[tuple[int, int], TicTacToe] = {}

@command(name="flip", category="Игры", description="Подбросить монету.", usage=".flip")
async def flip(context: object) -> None: await context.edit("🪙 " + random.choice(["Орёл", "Решка"]))

@command(name="dice", category="Игры", description="Бросить кубик Telegram.", usage=".dice")
async def dice(context: object) -> None:
    await context.delete(); result = await context.event.client.send_message(context.chat_id, file="🎲"); context.client.mark_internal(result)

@command(name="ttt", category="Игры", description="Крестики-нолики в текущем чате.", usage=".ttt [1-9]")
async def ttt(context: object) -> None:
    key = (context.user_id, context.chat_id); game = _games.get(key)
    if not context.args:
        game = TicTacToe(); _games[key] = game; await context.edit("🎮 Tic-tac-toe\n" + game.render() + "\nХод X: .ttt 1"); return
    if not game: await context.edit("⚠️ Сначала начни игру: .ttt"); return
    try: winner = game.move(int(context.args[0]))
    except (ValueError, IndexError): await context.edit("⚠️ Неверный ход."); return
    if winner: _games.pop(key, None); await context.edit(game.render() + f"\n🏆 Победил {winner}"); return
    await context.edit(game.render() + f"\nХод {game.turn}")
