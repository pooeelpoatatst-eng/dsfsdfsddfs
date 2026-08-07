from app.games.game2048 import Game2048
from app.games.tictactoe import TicTacToe

def test_2048_merges_once_per_pair() -> None:
    game = Game2048([[2, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    game.move("left")
    assert game.board[0][:3] == [4, 2, 0]

def test_tictactoe_detects_winner() -> None:
    game = TicTacToe()
    for cell in (1, 4, 2, 5):
        assert game.move(cell) is None
    assert game.move(3) == "X"
