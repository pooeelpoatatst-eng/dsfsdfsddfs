from app.games.game2048 import Game2048
from app.games.service import GameService, TicTacToeSession, WordlySession
from app.games.tictactoe import TicTacToe

def test_2048_merges_once_per_pair() -> None:
    game = Game2048([[2, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    game.spawn = lambda: None
    game.move("left")
    assert game.board[0][:3] == [4, 2, 0]

def test_tictactoe_detects_winner() -> None:
    game = TicTacToe()
    for cell in (1, 4, 2, 5):
        assert game.move(cell) is None
    assert game.move(3) == "X"


def test_2048_knows_when_no_moves_remain() -> None:
    game = Game2048([[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
    assert not game.can_move()
    game.board[0][0] = 0
    assert game.can_move()


def test_wordly_marks_duplicate_letters_once() -> None:
    # "а" occurs only once in "арбуз", so a repeated guess gets one yellow.
    row = GameService._wordly_row(WordlySession(owner_id=1, word="арбуз").word, "ааааб")
    assert row.count("🟨") == 1


def test_ttt_keyboard_uses_callback_cells_and_symbols() -> None:
    service = GameService(bot=None)
    session = TicTacToeSession(1, 2, "Первый", "Второй")
    session.game.move(1)
    keyboard = service._ttt_keyboard("token", session).inline_keyboard
    assert keyboard[0][0].text == "❌"
    assert keyboard[0][1].callback_data == "g:t:token:1"
    assert [button.text for button in keyboard[-1]] == ["❌ Отмена", "🔄 Заново"]
