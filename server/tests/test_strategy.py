import pytest
import itertools

from utils import get_status, GameStatus
from strategy import Mtd, RandomStrategy, DummyStrategy, BaseStrategy

CELL_INCREMENTS = set(itertools.permutations([-1, -1, 0, 1, 1], 2))


@pytest.mark.parametrize("row_inc, col_inc", CELL_INCREMENTS)
def test_dummy_strategy_beats_random(row_inc, col_inc):
    _second_strategy_wins(RandomStrategy(), DummyStrategy(row_inc, col_inc), 20)


def test_mtd_strategy_beats_random():
    _second_strategy_wins(RandomStrategy(), Mtd(), 20)


@pytest.mark.parametrize("row_inc, col_inc", CELL_INCREMENTS)
def test_mtd_strategy_beats_dummy(row_inc, col_inc):
    _second_strategy_wins(DummyStrategy(row_inc, col_inc), Mtd(), 20)


def _second_strategy_wins(
    strategy_a: BaseStrategy, strategy_b: BaseStrategy, max_steps: int
):
    def next_move(
        strategy: BaseStrategy, player: set[int], opponent: set[int], last_step: int
    ):
        next_step = strategy.run(player, opponent, last_step)
        status = get_status(player, opponent, next_step)
        player.add(next_step)
        if status == GameStatus.Draw:
            assert False, "Game draw unexpectedly"
        return status, next_step

    player_a = set()
    player_b = set()
    player_a_last_step = None
    player_b_last_step = None
    for _ in range(max_steps):
        status, player_a_last_step = next_move(
            strategy_a, player_a, player_b, player_a_last_step
        )
        if status == GameStatus.Finished:
            assert "First strategy should have not won"
        status, player_b_last_step = next_move(
            strategy_b, player_b, player_a, player_b_last_step
        )
        if status == GameStatus.Finished:
            break
    assert status == GameStatus.Finished


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
