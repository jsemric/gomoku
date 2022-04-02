import random
import math
from typing import Optional

WIN_SCORE = 1000
DEFEAT_SCORE = -WIN_SCORE
GRID_ROWS = 25
GRID_SIZE = GRID_ROWS ** 2 - 1
MAX_DEPTH = 5


class AlphaBeta:
    def __init__(self, max_depth: int = MAX_DEPTH):
        self._max_depth = max_depth

    def run(
            self,
            player1_cells,
            player2_cells,
            last_step,
    ) -> int:
        if last_step is None:
            return random.randint(0, GRID_SIZE - 1)
        pos, score = self._run(
            tuple(player1_cells), tuple(player2_cells), last_step, self._max_depth
        )
        return pos

    def _run(
            self,
            player1_cells: tuple,
            player2_cells: tuple,
            last_step: int,
            depth: int,
            maximize: bool = True,
            alpha: int = -math.inf,
            beta: int = math.inf,
    ) -> tuple:
        """Return step and score"""
        assert last_step in player1_cells or last_step in player2_cells
        player1 = set(player1_cells)  # maximizing
        player2 = set(player2_cells)  # minimizing

        # check other player victory
        score = self._evaluate(
            player2 if maximize else player1, last_step, not maximize, depth
        )
        if score is not None:
            return None, score

        if maximize:
            best_move, best_score = None, -math.inf
            for move in self._get_possible_moves(player1, player2, last_step):
                _, score = self._run(
                    tuple(player1 | {move}),
                    player2_cells,
                    move,
                    depth - 1,
                    False,
                    alpha,
                    beta,
                    )
                if score > best_score:
                    best_move = move
                    best_score = score
                alpha = max(alpha, score)
                if score >= beta:
                    break
        else:
            best_move, best_score = None, math.inf
            for move in self._get_possible_moves(player1, player2, last_step):
                _, score = self._run(
                    player1_cells,
                    tuple(player2 | {move}),
                    move,
                    depth - 1,
                    True,
                    alpha,
                    beta,
                    )
                if score < best_score:
                    best_move = move
                    best_score = score
                beta = min(beta, score)
                if score <= alpha:
                    break

        return best_move, best_score

    def _get_possible_moves(self, player1: set, player2: set, last_step: int):
        moves = []
        for pos in player1 | player2:
            for n in _get_neigh(pos):
                if n not in player1 and n not in player2:
                    moves.append(n)
        return moves

    def _evaluate(
            self, cells: set, last_step: Optional, maximize: bool, depth: int
    ):
        if check_winning_step(cells, last_step):
            score = WIN_SCORE - (self._max_depth - depth)
            return score if maximize else -score
        if depth <= 0:
            return 0
        return None


class Mtd(AlphaBeta):
    def __init__(self, *args, transposition_table=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.transposition_table = transposition_table or {}
        self._table_hits = 0
        self._guess_step = None

    def run(
            self,
            player1: set,
            player2: set,
            last_step: Optional[int],
    ) -> int:
        self.transposition_table.clear()
        self._table_hits = 0
        self._guess_step = None
        if last_step is None:
            return random.randint(0, GRID_SIZE - 1)
        pos, score = None, 0
        for depth in range(0, self._max_depth):
            pos, score = self._mtd(player1, player2, last_step, score, depth)
            self._guess_step = pos
        return pos

    def _mtd(self, player1: set, player2: set, last_step: int, score: int, depth: int):
        move = None
        upper_bound = math.inf
        lower_bound = -math.inf
        while lower_bound < upper_bound:
            beta = score + 1 if score == lower_bound else score
            move, score = self._run(
                tuple(player1), tuple(player2), last_step, depth, True, beta - 1, beta
            )
            if score < beta:
                upper_bound = score
            else:
                lower_bound = score
        return move, score

    def _run(
            self,
            player1_cells: tuple,
            player2_cells: tuple,
            last_step: int,
            depth: int,
            maximize: bool = True,
            alpha: int = -math.inf,
            beta: int = math.inf,
    ) -> tuple:
        transp_key = player1_cells, player2_cells, depth, maximize
        move, lower_bound, upper_bound = -1, -math.inf, math.inf
        if transp_key in self.transposition_table:
            move, lower_bound, upper_bound = self.transposition_table[transp_key]
            self._table_hits += 1
            if lower_bound >= beta:
                return move, lower_bound
            if upper_bound <= alpha:
                return move, upper_bound
            alpha = max(alpha, lower_bound)
            beta = min(beta, upper_bound)

        best_move, best_score = super()._run(
            player1_cells, player2_cells, last_step, depth, maximize, alpha, beta
        )

        if best_score <= alpha:
            self.transposition_table[transp_key] = best_move, lower_bound, best_score
        if beta > best_score > alpha:
            self.transposition_table[transp_key] = best_move, best_score, best_score
        if best_score >= beta:
            self.transposition_table[transp_key] = best_move, best_score, upper_bound
        return best_move, best_score

    def _get_possible_moves(self, player1: set, player2: set, last_step: int):
        ret = []
        if self._guess_step is not None:
            if self._guess_step not in player1 and self._guess_step not in player2:
                ret.append(self._guess_step)
        ret.extend(super()._get_possible_moves(player1, player2, last_step))
        return ret


def _distance(cell1, cell2):
    x1, y1 = _get_row_col(cell1)
    x2, y2 = _get_row_col(cell2)
    return max(abs(x1 - x2), abs(y1 - y2))


def check_winning_step(cells: set, step: int) -> bool:
    r, c = _get_row_col(step)
    return (
            _check_direction(cells, r, c, 1, 0)
            or _check_direction(cells, r, c, 0, 1)  # horizontal
            or _check_direction(cells, r, c, 1, 1)  # vertical
            or _check_direction(cells, r, c, 1, -1)  # diagonal  # reversed diagonal
    )


def _check_direction(cells: set, row: int, col: int, row_inc: int, col_inc: int) -> bool:
    cnt = 1
    r, c = row, col
    for _ in range(1, 5):
        r += row_inc
        c += col_inc
        if not (0 <= r < GRID_ROWS and 0 <= c < GRID_ROWS):
            break
        if _get_pos(r, c) not in cells:
            break
        cnt += 1

    r, c = row, col
    for _ in range(1, 5):
        r -= row_inc
        c -= col_inc
        if not (0 <= r < GRID_ROWS and 0 <= c < GRID_ROWS):
            break
        if _get_pos(r, c) not in cells:
            break
        cnt += 1
    return cnt >= 5


def _get_neigh(pos):
    r, c = _get_row_col(pos)
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
    for (r, c) in neigh:
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_ROWS:
            yield _get_pos(r, c)


def _get_row_col(pos):
    return pos // GRID_ROWS, pos % GRID_ROWS


def _get_pos(r, c):
    return r * GRID_ROWS + c
