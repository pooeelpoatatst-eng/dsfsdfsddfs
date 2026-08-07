from __future__ import annotations

from dataclasses import dataclass, field

WINNERS = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))

@dataclass
class TicTacToe:
    board: list[str] = field(default_factory=lambda: [" "] * 9)
    turn: str = "X"
    def move(self, cell: int) -> str | None:
        if not 1 <= cell <= 9 or self.board[cell - 1] != " ": raise ValueError("invalid move")
        self.board[cell - 1] = self.turn
        winner = next((self.turn for line in WINNERS if all(self.board[i] == self.turn for i in line)), None)
        if not winner: self.turn = "O" if self.turn == "X" else "X"
        return winner
    def render(self) -> str:
        cells = [cell if cell != " " else str(i + 1) for i, cell in enumerate(self.board)]
        return f"{cells[0]} │ {cells[1]} │ {cells[2]}\n──┼───┼──\n{cells[3]} │ {cells[4]} │ {cells[5]}\n──┼───┼──\n{cells[6]} │ {cells[7]} │ {cells[8]}"
