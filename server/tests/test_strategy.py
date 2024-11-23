import pytest
import itertools

from game import GameState, GameStatus
from strategy import Mtd, AlphaBeta, RandomStrategy, DummyStrategy, BaseStrategy

CELL_INCREMENTS = set(itertools.permutations([-1, -1, 0, 1, 1], 2))


@pytest.mark.parametrize("row_inc, col_inc", CELL_INCREMENTS)
def test_dummy_strategy_beats_random(row_inc, col_inc):
    _second_strategy_wins(RandomStrategy(), DummyStrategy(row_inc, col_inc), 20)


def test_alphabeta_strategy_beats_random():
    _second_strategy_wins(RandomStrategy(), AlphaBeta(3), 20)


@pytest.mark.skip("Revisit later")
@pytest.mark.parametrize("row_inc, col_inc", CELL_INCREMENTS)
def test_alphabeta_strategy_beats_dummy(row_inc, col_inc):
    _second_strategy_wins(DummyStrategy(row_inc, col_inc), AlphaBeta(5), 20)


def test_mtd_strategy_beats_random():
    _second_strategy_wins(RandomStrategy(), Mtd(), 20)


@pytest.mark.parametrize("row_inc, col_inc", CELL_INCREMENTS)
def test_mtd_strategy_beats_dummy(row_inc, col_inc):
    _second_strategy_wins(DummyStrategy(row_inc, col_inc), Mtd(), 20)


def _second_strategy_wins(
    strategy_a: BaseStrategy, strategy_b: BaseStrategy, max_steps: int
):
    gs = GameState.create([], [])
    for _ in range(max_steps):
        cell = strategy_a.run(gs)
        gs.add_cell(cell)
        assert gs.status == GameStatus.Playing, "First strategy should have lost"
        cell = strategy_b.run(gs)
        gs.add_cell(cell)
        if gs.status == GameStatus.Finished:
            break
    assert gs.status == GameStatus.Finished, "Second strategy should have won"


if __name__ == "__main__":
    from pycallgraph import PyCallGraph
    from pycallgraph.output import GraphvizOutput
    import logging
    import time

    logging.basicConfig(level=logging.INFO)
    start = time.time()
    with PyCallGraph(output=GraphvizOutput()):
        _second_strategy_wins(DummyStrategy(1, 0), Mtd(), 20)
        duration = time.time() - start
    print("Duration: %5d s" % duration)
