import pytest
import math

from utils import (
    steps_to_win,
    check_winning_step,
    GRID_ROWS,
    get_row_col_all,
    get_pos_all,
)

N = GRID_ROWS


@pytest.mark.parametrize(
    "pos,player,opponent,expected",
    [
        (0, set(), set(), 4),
        (0, {1, 5}, set(), 3),
        (0, {1, 3, 4}, set(), 1),
        (0, {1, 3, 4}, {2, N, N + 1}, math.inf),
        (1, {0, 3, 4}, set(), 1),
    ],
)
def test_steps_to_win(pos, player, opponent, expected):
    steps = steps_to_win(pos, player, opponent)
    assert steps == expected


@pytest.mark.parametrize(
    "cells",
    [
        {(0, 0), (0, 1), (0, 2), (0, 3), (0, 5)},
        {(0, 0), (1, 0), (2, 0), (3, 0), (5, 0)},
        {(0, 0), (1, 1), (2, 2), (3, 3), (5, 4)},
        {(0, 4), (1, 3), (2, 2), (3, 2), (4, 0)},
        {(1, 2), (4, 2), (2, 2), (3, 3), (5, 2)},
        {(1, 4), (2, 3), (0, 5), (3, 2), (5, 1)},
    ],
)
def test_no_victory(cells):
    cells = get_pos_all(cells)
    for i in cells:
        assert check_winning_step(cells, i) is False


@pytest.mark.parametrize(
    "cells",
    [
        {(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)},
        {(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)},
        {(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)},
        {(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)},
        {(1, 2), (4, 2), (2, 2), (3, 2), (5, 2)},
        {(1, 4), (2, 3), (0, 5), (3, 2), (4, 1)},
    ],
)
def test_victory(cells):
    cells = get_pos_all(cells)
    for i in cells:
        assert check_winning_step(cells, i) is True, f"Last step: {i}"


def test_pos_row_cols():
    cells = {27, 52, 77, 102, 127}
    cells_converted = get_row_col_all(cells)
    assert frozenset(get_pos_all(cells_converted)) == frozenset(cells)
