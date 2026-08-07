from __future__ import annotations

import random

class Game2048:
    def __init__(self, board: list[list[int]] | None = None) -> None:
        self.board = board or [[0] * 4 for _ in range(4)]
        if board is None: self.spawn(); self.spawn()
    def spawn(self) -> None:
        empty = [(r, c) for r in range(4) for c in range(4) if not self.board[r][c]]
        if empty:
            r, c = random.choice(empty); self.board[r][c] = 4 if random.random() < .1 else 2
    @staticmethod
    def _merge(row: list[int]) -> list[int]:
        values = [value for value in row if value]
        result: list[int] = []
        while values:
            value = values.pop(0)
            if values and values[0] == value: value *= 2; values.pop(0)
            result.append(value)
        return result + [0] * (4 - len(result))
    def move(self, direction: str) -> bool:
        before = [row[:] for row in self.board]
        if direction == "left": self.board = [self._merge(row) for row in self.board]
        elif direction == "right": self.board = [list(reversed(self._merge(list(reversed(row))))) for row in self.board]
        elif direction in {"up", "down"}:
            cols = list(map(list, zip(*self.board)))
            cols = [self._merge(col) if direction == "up" else list(reversed(self._merge(list(reversed(col))))) for col in cols]
            self.board = list(map(list, zip(*cols)))
        else: raise ValueError("unknown direction")
        changed = self.board != before
        if changed: self.spawn()
        return changed
