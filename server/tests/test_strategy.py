import pytest
import itertools

from game import Game
from strategy import Mtd, RandomStrategy, DummyStrategy

CELL_INCREMENTS = set(itertools.permutations([-1, -1, 0, 1, 1], 2))


@pytest.mark.parametrize("row_inc, col_inc", CELL_INCREMENTS)
def test_dummy_strategy_beats_random(row_inc, col_inc):
    game = Game(
        player1_strategy=DummyStrategy(row_inc, col_inc),
        player2_strategy=RandomStrategy(),
    )
    _first_strategy_wins(game, 10)


def test_mtd_strategy_beats_random():
    game = Game(player1_strategy=Mtd(), player2_strategy=RandomStrategy())
    _first_strategy_wins(game, 20)


@pytest.mark.parametrize("row_inc, col_inc", CELL_INCREMENTS)
def test_mtd_strategy_beats_dummy(row_inc, col_inc):
    game = Game(
        player1_strategy=Mtd(), player2_strategy=DummyStrategy(row_inc, col_inc)
    )
    _first_strategy_wins(game, 20)


def _first_strategy_wins(game, max_steps):
    for _ in range(max_steps):
        game.next_step()
        if game.finished:
            break
    assert game.player1_won


if __name__ == "__main__":
    from pycallgraph import PyCallGraph
    from pycallgraph.output import GraphvizOutput
    import logging
    import time

    logging.basicConfig(level=logging.INFO)
    start = time.time()
    with PyCallGraph(output=GraphvizOutput()):
        game = Game(
            player1_strategy=Mtd(), player2_strategy=DummyStrategy(1, 0), verbose=True
        )
        _first_strategy_wins(game, 20)
        duration = time.time() - start
    print("Duration: %5d s" % duration)
