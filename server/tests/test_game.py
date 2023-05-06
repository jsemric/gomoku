import pytest

from game import Game
from utils import GRID_SIZE
from exceptions import InvalidStep


def test_victory():
    game = Game()
    for i in range(4):
        game.take(i)
        game.take(GRID_SIZE - i - 1)
    game.take(4)
    assert game.finished and game.player1_won


def test_undo():
    game = Game()
    game.take(1)
    game.undo()
    assert game.taken(1) is False
    assert game.player2_turn is False
    assert game._last_step is None

    with pytest.raises(InvalidStep):
        game.undo()

    for i in range(1, 5):
        # take 1, 2, 3, 4
        game.take(i)

    # undo 3, 4
    for _ in range(2):
        game.undo()
    assert game.taken(1) and game.taken(2) and not game.taken(3) and not game.taken(4)
    assert game.player2_turn is False
    assert game._last_step == 2
