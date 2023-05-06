import math
import logging
import time
from functools import wraps, partial
from collections import deque

logger = logging.getLogger(__name__)

GRID_ROWS = 25
GRID_SIZE = GRID_ROWS**2


def timeit(fn=None, *, name=None):
    if fn is None:
        return partial(timeit, name=name)
    name = fn.__name__

    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        res = fn(*args, **kwargs)
        duration = time.time() - start
        logger.info("Running %s took %.3f (s)", name, duration)
        return res

    return wrapper


def steps_to_win(pos, player, opponent) -> int:
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
        # go forth 4+5 fields
        q = deque([])
        for _ in range(left + 5):
            if inside_interval(row, col):
                next_pos = get_pos(row, col)
                if next_pos in opponent:
                    q.clear()
                    to_take = 0
                    taken = 0
                elif next_pos in player or next_pos == pos:
                    q.append(True)
                    taken += 1
                else:
                    q.append(False)
                    to_take += 1

                if taken + to_take == 5:
                    curr_best = min(curr_best, to_take)
                    if q.popleft() is True:
                        taken -= 1
                    else:
                        to_take -= 1

                row, col = increment_cell(row, col, row_inc, col_inc)
            else:
                break
        return curr_best

    return min(
        check_direction(1, 0),  # vertical
        check_direction(0, 1),  # horizontal
        check_direction(1, 1),  # diagonal
        check_direction(1, -1),  # reversed diagonal
    )


def distance(cell1, cell2):
    x1, y1 = get_row_col(cell1)
    x2, y2 = get_row_col(cell2)
    return max(abs(x1 - x2), abs(y1 - y2))


def check_winning_step(cells: set, step: int) -> bool:
    return steps_to_win(step, cells, set()) == 0


def get_neigh(pos: tuple[int, int]):
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
