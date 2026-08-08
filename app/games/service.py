from __future__ import annotations

import random
import secrets
from dataclasses import dataclass, field
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent

from app.games.game2048 import Game2048
from app.games.tictactoe import TicTacToe


EMPTY_CELL = "⠀"
WORDLY_WORDS = (
    "арбуз", "билет", "ветер", "город", "диван", "жираф", "замок", "игрок",
    "какао", "лампа", "маска", "нитка", "океан", "пламя", "радар", "салют",
    "тыква", "фокус", "холст", "цифра", "школа", "экран", "юрист", "ягода",
)


@dataclass
class TicTacToeSession:
    owner_id: int
    opponent_id: int
    owner_name: str
    opponent_name: str
    game: TicTacToe = field(default_factory=TicTacToe)
    message_id: int | None = None
    finished: bool = False

    def player_for_turn(self) -> tuple[int, str, str]:
        if self.game.turn == "X":
            return self.owner_id, self.owner_name, "❌"
        return self.opponent_id, self.opponent_name, "⭕️"


@dataclass
class Game2048Session:
    owner_id: int
    owner_name: str
    game: Game2048 = field(default_factory=Game2048)
    message_id: int | None = None


@dataclass
class RpsSession:
    owner_id: int
    opponent_id: int
    owner_name: str
    opponent_name: str
    choices: dict[int, str] = field(default_factory=dict)
    message_id: int | None = None


@dataclass
class GuessSession:
    owner_id: int
    target: int = field(default_factory=lambda: random.randint(1, 9))
    attempts: int = 3
    message_id: int | None = None


@dataclass
class WordlySession:
    owner_id: int
    word: str = field(default_factory=lambda: random.choice(WORDLY_WORDS))
    guesses: list[str] = field(default_factory=list)
    typed: str = ""
    message_id: int | None = None


class GameService:
    """In-memory games sent as inline-bot messages by the user account itself."""

    def __init__(self, bot: Any) -> None:
        self.bot = bot
        self.ttt: dict[str, TicTacToeSession] = {}
        self.games_2048: dict[str, Game2048Session] = {}
        self.rps: dict[str, RpsSession] = {}
        self.guess: dict[str, GuessSession] = {}
        self.wordly: dict[str, WordlySession] = {}
        self._bot_username: str | None = None

    @staticmethod
    def _id() -> str:
        return secrets.token_urlsafe(5).replace("-", "a").replace("_", "b")

    @staticmethod
    def _button(text: str, data: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=data)

    async def bot_username(self) -> str:
        if not self._bot_username:
            me = await self.bot.get_me()
            if not me.username:
                raise RuntimeError("Control bot needs a public username for inline games")
            self._bot_username = me.username
        return self._bot_username

    async def create_ttt(self, owner_id: int, opponent_id: int, owner_name: str, opponent_name: str) -> str:
        token = self._id()
        self.ttt[token] = TicTacToeSession(owner_id, opponent_id, owner_name, opponent_name)
        return token

    def _ttt_text(self, session: TicTacToeSession, result: str | None = None) -> str:
        if result:
            return "⭐ Крестики-нолики\n\n" + result
        _, name, mark = session.player_for_turn()
        return (
            "⭐ Крестики-нолики\n\n"
            f"❌ {session.owner_name}\n"
            f"⭕️ {session.opponent_name}\n\n"
            f"Ход: {mark} {name}"
        )

    def _ttt_keyboard(self, token: str, session: TicTacToeSession, finished: bool = False) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        for row in range(3):
            rows.append([
                self._button("❌" if session.game.board[row * 3 + col] == "X" else "⭕️" if session.game.board[row * 3 + col] == "O" else EMPTY_CELL, f"g:t:{token}:{row * 3 + col}")
                for col in range(3)
            ])
        rows.append([
            self._button("❌ Отмена", f"g:t:{token}:cancel"),
            self._button("🔄 Заново", f"g:t:{token}:reset"),
        ])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    async def create_2048(self, owner_id: int, owner_name: str) -> str:
        token = self._id()
        self.games_2048[token] = Game2048Session(owner_id, owner_name)
        return token

    @staticmethod
    def _tile(value: int) -> str:
        return {0: "▫️", 2: "2️⃣", 4: "4️⃣", 8: "8️⃣", 16: "🟧", 32: "🟥", 64: "🟪", 128: "🟦", 256: "🟩", 512: "🟨"}.get(value, "💎")

    def _2048_text(self, session: Game2048Session, status: str = "") -> str:
        board = "\n".join(" ".join(self._tile(cell) for cell in row) for row in session.game.board)
        max_tile = max(cell for row in session.game.board for cell in row)
        tail = status or f"Лучший тайл: {max_tile}"
        return f"🎮 2048 · {session.owner_name}\n\n{board}\n\n{tail}"

    def _2048_keyboard(self, token: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [self._button("⬆️", f"g:2:{token}:up")],
            [self._button("⬅️", f"g:2:{token}:left"), self._button("➡️", f"g:2:{token}:right")],
            [self._button("⬇️", f"g:2:{token}:down")],
            [self._button("🔄 Заново", f"g:2:{token}:reset"), self._button("✖️ Закрыть", f"g:2:{token}:close")],
        ])

    async def create_rps(self, owner_id: int, opponent_id: int, owner_name: str, opponent_name: str) -> str:
        token = self._id()
        self.rps[token] = RpsSession(owner_id, opponent_id, owner_name, opponent_name)
        return token

    @staticmethod
    def _rps_keyboard(token: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🪨", callback_data=f"g:r:{token}:rock"),
            InlineKeyboardButton(text="📄", callback_data=f"g:r:{token}:paper"),
            InlineKeyboardButton(text="✂️", callback_data=f"g:r:{token}:scissors"),
        ], [InlineKeyboardButton(text="✖️ Отмена", callback_data=f"g:r:{token}:cancel")]])

    def _rps_text(self, session: RpsSession, result: str | None = None) -> str:
        if result:
            return f"🪨 Камень · 📄 Бумага · ✂️ Ножницы\n\n{result}"
        chosen = [name for user_id, name in ((session.owner_id, session.owner_name), (session.opponent_id, session.opponent_name)) if user_id in session.choices]
        waiting = session.opponent_name if session.owner_id in session.choices else session.owner_name
        return f"🪨 Камень · 📄 Бумага · ✂️ Ножницы\n\n{session.owner_name} vs {session.opponent_name}\n\nВыбрали: {', '.join(chosen) or 'пока никто'}\nЖдём: {waiting}"

    async def create_guess(self, owner_id: int) -> str:
        token = self._id()
        self.guess[token] = GuessSession(owner_id)
        return token

    @staticmethod
    def _guess_keyboard(token: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=str(number), callback_data=f"g:n:{token}:{number}") for number in row]
            for row in ((1, 2, 3), (4, 5, 6), (7, 8, 9))
        ] + [[InlineKeyboardButton(text="✖️ Закрыть", callback_data=f"g:n:{token}:close")]])

    @staticmethod
    def _guess_text(session: GuessSession, status: str = "") -> str:
        return f"🔢 Угадай число от 1 до 9\n\nПопыток: {session.attempts}\n{status or 'Выбери число кнопкой.'}"

    async def create_wordly(self, owner_id: int) -> str:
        token = self._id()
        self.wordly[token] = WordlySession(owner_id)
        return token

    def inline_result(self, query: str) -> InlineQueryResultArticle | None:
        """Return the game card that Telegram will send *as the user* via bot."""
        prefix, _, token = query.partition(":")
        if prefix != "game" or not token:
            return None
        if token in self.ttt:
            session = self.ttt[token]
            return InlineQueryResultArticle(id=token, title="Крестики-нолики", description=f"{session.owner_name} vs {session.opponent_name}", input_message_content=InputTextMessageContent(message_text=self._ttt_text(session)), reply_markup=self._ttt_keyboard(token, session))
        if token in self.games_2048:
            session = self.games_2048[token]
            return InlineQueryResultArticle(id=token, title="2048", description="Играть кнопками", input_message_content=InputTextMessageContent(message_text=self._2048_text(session)), reply_markup=self._2048_keyboard(token))
        if token in self.rps:
            session = self.rps[token]
            return InlineQueryResultArticle(id=token, title="Камень · Ножницы · Бумага", description=f"{session.owner_name} vs {session.opponent_name}", input_message_content=InputTextMessageContent(message_text=self._rps_text(session)), reply_markup=self._rps_keyboard(token))
        if token in self.guess:
            session = self.guess[token]
            return InlineQueryResultArticle(id=token, title="Угадай число", description="От 1 до 9", input_message_content=InputTextMessageContent(message_text=self._guess_text(session)), reply_markup=self._guess_keyboard(token))
        if token in self.wordly:
            session = self.wordly[token]
            return InlineQueryResultArticle(id=token, title="Wordly", description="Угадай слово из 5 букв", input_message_content=InputTextMessageContent(message_text=self._wordly_text(session)), reply_markup=self._wordly_keyboard(token, session))
        return None

    async def _edit(self, callback: Any, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
        if getattr(callback, "inline_message_id", None):
            await self.bot.edit_message_text(inline_message_id=callback.inline_message_id, text=text, reply_markup=markup)
        else:
            await callback.message.edit_text(text, reply_markup=markup)

    @staticmethod
    def _wordly_keyboard(token: str, session: WordlySession) -> InlineKeyboardMarkup:
        rows = ["йцукенгшщзхъ", "фывапролджэ", "ячсмитьбю"]
        keyboard = [[InlineKeyboardButton(text=letter.upper(), callback_data=f"g:w:{token}:{letter}") for letter in row] for row in rows]
        keyboard.append([
            InlineKeyboardButton(text="⌫", callback_data=f"g:w:{token}:back"),
            InlineKeyboardButton(text="✅ Проверить", callback_data=f"g:w:{token}:enter"),
            InlineKeyboardButton(text="✖️", callback_data=f"g:w:{token}:close"),
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def _wordly_row(word: str, guess: str | None = None) -> str:
        if not guess:
            return "⬛⬛⬛⬛⬛"
        states = ["⬛"] * 5
        unused = list(word)
        for index, letter in enumerate(guess):
            if letter == word[index]:
                states[index] = "🟩"
                unused[index] = ""
        for index, letter in enumerate(guess):
            if states[index] == "⬛" and letter in unused:
                states[index] = "🟨"
                unused[unused.index(letter)] = ""
        return "".join(f"{state}{letter.upper()}" for state, letter in zip(states, guess))

    def _wordly_text(self, session: WordlySession, status: str = "") -> str:
        rows = [self._wordly_row(session.word, guess) for guess in session.guesses]
        rows.extend(self._wordly_row(session.word) for _ in range(6 - len(rows)))
        typed = " ".join(session.typed.upper()) or "—"
        return "🟩 Wordly · угадай слово из 5 букв\n\n" + "\n".join(rows) + f"\n\nСлово: {typed}\n{status or 'У тебя 6 попыток.'}"

    async def handle_callback(self, callback: Any) -> bool:
        data = callback.data or ""
        parts = data.split(":")
        if len(parts) != 4 or parts[0] != "g":
            return False
        kind, token, action = parts[1:]
        handlers = {"t": self._handle_ttt, "2": self._handle_2048, "r": self._handle_rps, "n": self._handle_guess, "w": self._handle_wordly}
        handler = handlers.get(kind)
        if not handler:
            return False
        await handler(callback, token, action)
        return True

    @staticmethod
    async def _forbidden(callback: Any) -> None:
        await callback.answer("Это не твоя игра.", show_alert=True)

    async def _handle_ttt(self, callback: Any, token: str, action: str) -> None:
        session = self.ttt.get(token)
        if not session:
            await callback.answer("Игра уже закончилась.", show_alert=True); return
        if callback.from_user.id not in {session.owner_id, session.opponent_id}:
            await self._forbidden(callback); return
        if action == "cancel":
            self.ttt.pop(token, None)
            await self._edit(callback, self._ttt_text(session, "Игра отменена."))
            await callback.answer(); return
        if action == "reset":
            if callback.from_user.id != session.owner_id:
                await callback.answer("Заново может начать тот, кто создал игру.", show_alert=True); return
            session.game = TicTacToe()
            session.finished = False
            await self._edit(callback, self._ttt_text(session), self._ttt_keyboard(token, session))
            await callback.answer("Новая партия!"); return
        if session.finished:
            await callback.answer("Партия уже завершена. Нажми «Заново».", show_alert=True); return
        player_id, _, _ = session.player_for_turn()
        if callback.from_user.id != player_id:
            await callback.answer("Сейчас ход соперника.", show_alert=True); return
        try:
            winner = session.game.move(int(action) + 1)
        except ValueError:
            await callback.answer("Эта клетка уже занята.", show_alert=True); return
        if winner or all(cell != " " for cell in session.game.board):
            result = f"🏆 Победил {session.owner_name if winner == 'X' else session.opponent_name}!" if winner else "🤝 Ничья!"
            session.finished = True
            await self._edit(callback, self._ttt_text(session, result), self._ttt_keyboard(token, session, True))
            await callback.answer()
            return
        await self._edit(callback, self._ttt_text(session), self._ttt_keyboard(token, session))
        await callback.answer()

    async def _handle_2048(self, callback: Any, token: str, action: str) -> None:
        session = self.games_2048.get(token)
        if not session:
            await callback.answer("Игра уже закончилась.", show_alert=True); return
        if callback.from_user.id != session.owner_id:
            await self._forbidden(callback); return
        if action == "close":
            self.games_2048.pop(token, None)
            await self._edit(callback, "🎮 2048 закрыта."); await callback.answer(); return
        if action == "reset":
            session.game = Game2048()
            status = "Новая игра!"
        else:
            changed = session.game.move(action)
            status = "Ход не меняет поле." if not changed else ""
        if not session.game.can_move():
            status = "💥 Ходов больше нет. Нажми «Заново»."
        await self._edit(callback, self._2048_text(session, status), self._2048_keyboard(token))
        await callback.answer()

    async def _handle_rps(self, callback: Any, token: str, action: str) -> None:
        session = self.rps.get(token)
        if not session:
            await callback.answer("Игра уже закончилась.", show_alert=True); return
        if callback.from_user.id not in {session.owner_id, session.opponent_id}:
            await self._forbidden(callback); return
        if action == "cancel":
            self.rps.pop(token, None)
            await self._edit(callback, "🪨 Камень · 📄 Бумага · ✂️ Ножницы\n\nИгра отменена."); await callback.answer(); return
        if callback.from_user.id in session.choices:
            await callback.answer("Выбор уже принят.", show_alert=True); return
        session.choices[callback.from_user.id] = action
        if len(session.choices) < 2:
            await self._edit(callback, self._rps_text(session), self._rps_keyboard(token))
            await callback.answer("Выбор скрыт до конца раунда."); return
        first, second = session.choices[session.owner_id], session.choices[session.opponent_id]
        beats = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
        labels = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        if first == second:
            outcome = "🤝 Ничья"
        else:
            outcome = f"🏆 Победил {session.owner_name if beats[first] == second else session.opponent_name}"
        result = f"{session.owner_name}: {labels[first]}\n{session.opponent_name}: {labels[second]}\n\n{outcome}"
        self.rps.pop(token, None)
        await self._edit(callback, self._rps_text(session, result)); await callback.answer()

    async def _handle_guess(self, callback: Any, token: str, action: str) -> None:
        session = self.guess.get(token)
        if not session:
            await callback.answer("Игра уже закончилась.", show_alert=True); return
        if callback.from_user.id != session.owner_id:
            await self._forbidden(callback); return
        if action == "close":
            self.guess.pop(token, None)
            await self._edit(callback, "🔢 Игра закрыта."); await callback.answer(); return
        number = int(action)
        if number == session.target:
            self.guess.pop(token, None)
            await self._edit(callback, f"🔢 Угадал! Это было число {number}. 🎉"); await callback.answer(); return
        session.attempts -= 1
        if session.attempts == 0:
            self.guess.pop(token, None)
            await self._edit(callback, f"🔢 Попытки закончились. Было число {session.target}."); await callback.answer(); return
        hint = "больше" if number < session.target else "меньше"
        await self._edit(callback, self._guess_text(session, f"Неа, загаданное число {hint}."), self._guess_keyboard(token)); await callback.answer()

    async def _handle_wordly(self, callback: Any, token: str, action: str) -> None:
        session = self.wordly.get(token)
        if not session:
            await callback.answer("Игра уже закончилась.", show_alert=True); return
        if callback.from_user.id != session.owner_id:
            await self._forbidden(callback); return
        if action == "close":
            self.wordly.pop(token, None)
            await self._edit(callback, f"🟩 Wordly закрыт. Слово было: {session.word.upper()}."); await callback.answer(); return
        if action == "back":
            session.typed = session.typed[:-1]
        elif action == "enter":
            if len(session.typed) != 5:
                await callback.answer("Нужно ровно 5 букв.", show_alert=True); return
            guess = session.typed
            session.guesses.append(guess)
            session.typed = ""
            if guess == session.word or len(session.guesses) == 6:
                won = guess == session.word
                self.wordly.pop(token, None)
                tail = "🏆 Угадано!" if won else f"💥 Слово было: {session.word.upper()}."
                await self._edit(callback, self._wordly_text(session, tail)); await callback.answer(); return
        elif len(action) == 1 and action in "йцукенгшщзхъфывапролджэячсмитьбю" and len(session.typed) < 5:
            session.typed += action
        await self._edit(callback, self._wordly_text(session), self._wordly_keyboard(token, session)); await callback.answer()
