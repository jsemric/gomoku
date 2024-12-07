import math
import array
import logging
import time
from enum import Enum
from functools import wraps, partial
from typing import Optional, Generator

logger = logging.getLogger(__name__)

GRID_ROWS = 25
GRID_SIZE = GRID_ROWS**2


def steps_to_win(pos: int, grid: array.array, player: int, opponent: int) -> float:
    """Return the number of cells to take to win or inf if not possible."""

    def check_direction(row_inc: int, col_inc: int) -> bool:
        row, col = get_row_col(pos)
        # go back 4 fields from pos
        left = 0
        while left < 4:
            row_, col_ = increment_cell(row, col, -row_inc, -col_inc)
            if inside_interval(row_, col_):
                left += 1
                row, col = row_, col_
            else:
                break

        curr_best = math.inf
        taken = 0
        to_take = 0
        # go forth 4+5 cells
        left_cell = right_cell = row, col
        for _ in range(left + 5):
            if not inside_interval(*right_cell):
                break

            next_pos = get_pos(*right_cell)
            if grid[next_pos] == opponent:
                to_take = 0
                taken = 0
            elif grid[next_pos] == player or next_pos == pos:
                taken += 1
            else:
                to_take += 1

            if taken + to_take == 5:
                curr_best = min(curr_best, to_take)
                if grid[get_pos(*left_cell)] == player:
                    taken -= 1
                else:
                    to_take -= 1
                left_cell = increment_cell(*left_cell, row_inc, col_inc)

            right_cell = increment_cell(*right_cell, row_inc, col_inc)
        return curr_best

    return min(
        check_direction(1, 0),  # vertical
        check_direction(0, 1),  # horizontal
        check_direction(1, 1),  # diagonal
        check_direction(1, -1),  # reversed diagonal
    )


def check_winning_step(grid: array.array, step: int, player: int) -> bool:
    return steps_to_win(step, grid, player, 33) == 0


def get_neigh(pos: int) -> Generator[int, None, None]:
    r, c = get_row_col(pos)
    neigh = (
        (r + 1, c),
        (r + 1, c + 1),
        (r, c + 1),
        (r - 1, c + 1),
        (r - 1, c),
        (r - 1, c - 1),
        (r, c - 1),
        (r + 1, c - 1),
    )
    for r, c in neigh:
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_ROWS:
            yield get_pos(r, c)


def get_row_col(pos: int) -> tuple[int, int]:
    return pos // GRID_ROWS, pos % GRID_ROWS


def get_pos(row: int, col: int) -> int:
    return row * GRID_ROWS + col


def get_row_col_all(cells: set[int]) -> set[tuple[int, int]]:
    return {get_row_col(pos) for pos in cells}


def get_pos_all(cells: set[tuple[int, int]]) -> set[int]:
    return {get_pos(row, col) for row, col in cells}


def inside_interval(row: int, col: int) -> bool:
    return 0 <= row < GRID_ROWS and 0 <= col < GRID_ROWS


def inside_interval_pos(pos: int) -> bool:
    return 0 <= pos < GRID_SIZE


def increment_cell(row: int, col: int, row_inc: int, col_inc: int) -> tuple[int, int]:
    return row + row_inc, col + col_inc


def increment_cell_pos(pos: int, row_inc: int, col_inc: int) -> int:
    return pos + row_inc + (col_inc * GRID_ROWS)
