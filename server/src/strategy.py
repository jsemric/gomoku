import random
import logging
import math
from typing import Optional
from abc import ABC, abstractmethod

from utils import (
    GRID_SIZE,
    timeit,
    steps_to_win,
    get_neigh,
    increment_cell_pos,
    inside_interval_pos,
)

logger = logging.getLogger(__name__)

WIN_SCORE = 1000
DEFEAT_SCORE = -WIN_SCORE
MAX_DEPTH = 5


class BaseStrategy(ABC):
    @abstractmethod
    def run(
        self, player1: set[int], player2: set[int], last_step: int
    ) -> Optional[int]:
        pass


class RandomStrategy(ABC):
    """Strategy using random cell selection."""

    def run(
        self, player1: set[int], player2: set[int], last_step: int
    ) -> Optional[int]:
        while True:
            next_pos = random.randint(0, GRID_SIZE - 1)
            if not self._taken(next_pos, player1, player2):
                return next_pos

    def _taken(self, pos: int, player1: set[int], player2: set[int]) -> bool:
        return pos in player1 or pos in player2


class DummyStrategy(RandomStrategy):
    """Strategy trying to greedily get 5 in one direction."""

    def __init__(
        self, row_inc: int = 1, col_inc: int = 1, start_pos: int = GRID_SIZE // 2
    ) -> None:
        self.row_inc = row_inc
        self.col_inc = col_inc
        self.next_pos: Optional[int] = start_pos
        if self.row_inc not in (1, -1, 0) and self.col_inc not in (1, -1, 0):
            raise ValueError("Row and column increment must be either 0, 1, or -1.")

    def run(
        self, player1: set[int], player2: set[int], last_step: int
    ) -> Optional[int]:
        self.next_pos = increment_cell_pos(self.next_pos, self.row_inc, self.col_inc)
        if self._taken(self.next_pos, player1, player2) or not inside_interval_pos(
            self.next_pos
        ):
            self.next_pos = super().run(player1, player2, last_step)
        return self.next_pos


class AlphaBeta(BaseStrategy):
    """Strategy using the min-max search with the alpha-beta prunning."""

    def __init__(self, max_depth: int = MAX_DEPTH):
        self._max_depth = max_depth

    def run(
        self,
        player1: set[int],
        player2: set[int],
        last_step: int,
    ) -> Optional[int]:
        if last_step is None:
            return random.randint(0, GRID_SIZE - 1)
        pos, score = self._run(
            tuple(player1), tuple(player2), last_step, self._max_depth
        )
        return pos

    def _run(
        self,
        player1_cells: tuple[int, ...],
        player2_cells: tuple[int, ...],
        last_step: int,
        depth: int,
        maximize: bool = True,
        alpha: float = -math.inf,
        beta: float = math.inf,
    ) -> tuple[Optional[int], float]:
        """Return step and score"""
        assert last_step in player1_cells or last_step in player2_cells
        player1 = set(player1_cells)  # maximizing
        player2 = set(player2_cells)  # minimizing

        # check other player victory
        score = self._evaluate(
            player2 if maximize else player1,
            player1 if maximize else player2,
            last_step,
            not maximize,
            depth,
        )
        if score is not None:
            return None, score

        if maximize:
            best_move, best_score = None, -math.inf
            for move in self.get_possible_moves(player1, player2, last_step):
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
            for move in self.get_possible_moves(player1, player2, last_step):
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

    def get_possible_moves(
        self, player1: set[int], player2: set[int], last_step: int
    ) -> list[int]:
        moves = []
        for pos in player1 | player2:
            for n in get_neigh(pos):
                if n not in player1 and n not in player2:
                    moves.append(n)
        return moves

    def _evaluate(
        self,
        player: set[int],
        opponent: set[int],
        last_step: Optional[int],
        maximize: bool,
        depth: int,
    ) -> Optional[float]:
        steps = steps_to_win(last_step, player, opponent)
        if steps == 0:
            score = WIN_SCORE - (self._max_depth - depth)
            return score if maximize else -score
        if depth <= 0:
            # return steps to win the lowe the better
            return -steps if maximize else steps
        return None


class Mtd(AlphaBeta):
    def __init__(self, *args, transposition_table=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.transposition_table = transposition_table or {}
        self._table_hits = 0
        self._guess_step = None

    @timeit(name="mtd.run")
    def run(
        self,
        player1: set[int],
        player2: set[int],
        last_step: "Optional[int]",
    ) -> Optional[int]:
        self.transposition_table.clear()
        self._table_hits = 0
        self._table_misses = 0
        self._guess_step = None
        if last_step is None:
            return random.randint(0, GRID_SIZE - 1)
        pos, score = None, 0.0
        for depth in range(0, self._max_depth):
            pos, score = self._mtd(player1, player2, last_step, score, depth)
            logger.info("Got step/score/depth %s/%s/%s", pos, score, depth)
            self._guess_step = pos
            logger.info(
                "Table hit/miss/depth %6d/%6d/%d",
                self._table_hits,
                self._table_misses,
                depth,
            )
        return pos

    def _mtd(
        self,
        player1: set[int],
        player2: set[int],
        last_step: int,
        score: float,
        depth: int,
    ) -> tuple[Optional[int], float]:
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
        player1_cells: tuple[int, ...],
        player2_cells: tuple[int, ...],
        last_step: int,
        depth: int,
        maximize: bool = True,
        alpha: float = -math.inf,
        beta: float = math.inf,
    ) -> tuple[Optional[int], float]:
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

        self._table_misses += 1

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

    def get_possible_moves(
        self, player1: set[int], player2: set[int], last_step: int
    ) -> list[int]:
        ret = []
        if self._guess_step is not None:
            if self._guess_step not in player1 and self._guess_step not in player2:
                ret.append(self._guess_step)
        ret.extend(super().get_possible_moves(player1, player2, last_step))
        return ret
