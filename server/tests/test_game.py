import pytest
import random
from pytest import param
from game import Game, GRID_ROWS, GRID_SIZE, check_winning_step
from exceptions import InvalidStep


def test_ai_game():
    game = Game()
    pos = 10
    game.take(pos)
    assert game.taken(pos)
    assert not game.finished
    assert game.player2_turn

    for i in range(14):
        game.next_step()
        if game.finished:
            break
        while game.taken(pos):
            pos = random.randint(0, GRID_SIZE - 1)
        game.take(pos)
    assert game.finished


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


@pytest.mark.parametrize(
    "cells",
    [
        {100, 76, 52, 28},
        {0, 1, 2, 4, 5},
        {0, 1, 2, 4, 24},
        {0, 25, 50, 75, GRID_ROWS * (GRID_ROWS - 1)},
        param({21, 22, 23, 24, 25}, id="horizontal right edge"),
        param({24, 25, 26, 27, 28}, id="horizontal left edge"),
        param({100, 76, 52, 28, 100 + GRID_ROWS - 1}, id="diagonal left edge"),
        param({50, 76, 102, 128, 50 - GRID_ROWS - 1}, id="reverse diagonal left edge"),
    ],
)
def test_no_victory(cells):
    for i in cells:
        assert check_winning_step(cells, i) is False


@pytest.mark.parametrize(
    "cells",
    [
        {0, 1, 2, 3, 4},
        {27, 52, 77, 102, 127},
        {101, 77, 53, 29, 5},
        {100, 76, 52, 28, 4},
    ],
)
def test_victory(cells):
    for i in cells:
        assert check_winning_step(cells, i) is True
