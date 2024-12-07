import random
import logging
import math
from typing import Optional
from abc import ABC, abstractmethod

from gomoku.game import GameState
from gomoku.utils import (
    GRID_SIZE,
    steps_to_win,
    get_neigh,
    increment_cell_pos,
    inside_interval_pos,
)

logger = logging.getLogger(__name__)

WIN_SCORE = 1000.0
DEFEAT_SCORE = -WIN_SCORE
MAX_DEPTH = 5


class BaseStrategy(ABC):
    @abstractmethod
    def run(self, gs: GameState) -> Optional[int]:
        pass


def _random_cell(gs: GameState) -> int:
    while True:
        next_pos = random.randint(0, GRID_SIZE - 1)
        if gs.grid[next_pos] == 0:
            return next_pos


class RandomStrategy(BaseStrategy):
    """Strategy using random cell selection."""

    def run(
        self,
        gs: GameState,
    ) -> Optional[int]:
        return _random_cell(gs)


class DummyStrategy(BaseStrategy):
    """Strategy trying to greedily get 5 in one direction."""

    def __init__(
        self, row_inc: int = 1, col_inc: int = 1, start_pos: int = GRID_SIZE // 2
    ) -> None:
        self.row_inc = row_inc
        self.col_inc = col_inc
        self.next_pos: Optional[int] = start_pos
        if self.row_inc not in (1, -1, 0) and self.col_inc not in (1, -1, 0):
            raise ValueError("Row and column increment must be either 0, 1, or -1.")

    def run(self, gs: GameState) -> Optional[int]:
        self.next_pos = increment_cell_pos(self.next_pos, self.row_inc, self.col_inc)
        if not inside_interval_pos(self.next_pos) or gs.is_taken(self.next_pos):
            self.next_pos = _random_cell(gs)
        return self.next_pos


class AlphaBeta(BaseStrategy):
    """Strategy using the min-max search with the alpha-beta prunning."""

    def __init__(self, max_depth: int = MAX_DEPTH):
        self._max_depth = max_depth
        self._memory = {}
        self._memory_hits = 0
        self._total_searches = 0

    def run(self, gs: GameState) -> Optional[int]:
        if not gs.last_step:
            return _random_cell(gs)
        self._reset_memory()
        pos, _ = self._memorized_search(gs, self._max_depth)
        self._log_hit_rate()
        return pos

    def _reset_memory(self) -> None:
        self._memory = {}
        self._memory_hits = 0
        self._total_searches = 0

    def _log_hit_rate(self) -> None:
        logger.info(
            "Table hit/total/pct %6d/%6d/%.2f",
            self._memory_hits,
            self._total_searches,
            100 * self._memory_hits / self._total_searches,
        )

    def _memorized_search(
        self,
        gs: GameState,
        depth: int,
        maximize: bool = True,
        alpha: float = -math.inf,
        beta: float = math.inf,
    ) -> tuple[Optional[int], float]:
        key = gs.grid.tobytes(), depth, maximize
        move, lower_bound, upper_bound = -1, -math.inf, math.inf
        if key in self._memory:
            move, lower_bound, upper_bound = self._memory[key]
            self._memory_hits += 1
            if lower_bound >= beta:
                return move, lower_bound
            if upper_bound <= alpha:
                return move, upper_bound
            alpha = max(alpha, lower_bound)
            beta = min(beta, upper_bound)

        self._total_searches += 1

        best_move, best_score = self._search(gs, depth, maximize, alpha, beta)

        if best_score <= alpha:
            self._memory[key] = best_move, lower_bound, best_score
        if beta > best_score > alpha:
            self._memory[key] = best_move, best_score, best_score
        if best_score >= beta:
            self._memory[key] = best_move, best_score, upper_bound
        return best_move, best_score

    def _search(
        self,
        gs: GameState,
        depth: int,
        maximize: bool = True,
        alpha: float = -math.inf,
        beta: float = math.inf,
    ) -> tuple[Optional[int], float]:
        """Return step and score"""
        assert gs.grid[gs.last_step] == gs.last_player

        # check other player victory
        score = self._evaluate(gs, not maximize, depth)
        if score is not None:
            return None, score

        if maximize:
            best_move, best_score = None, -math.inf
            for move in self.get_possible_moves(gs):
                with gs.with_move(move) as new_gs:
                    _, score = self._memorized_search(
                        new_gs,
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
            for move in self.get_possible_moves(gs):
                with gs.with_move(move) as new_gs:
                    _, score = self._memorized_search(
                        new_gs,
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

    def get_possible_moves(self, gs: GameState) -> list[int]:
        moves = []
        for pos in gs.p1 + gs.p2:
            for n in get_neigh(pos):
                if not gs.is_taken(n):
                    moves.append(n)
        return moves

    def _evaluate(
        self,
        gs: GameState,
        maximize: bool,
        depth: int,
    ) -> Optional[float]:
        p1, p2 = (2, 1) if maximize else (1, 2)
        # p1, p2 = (1, 2) if maximize else (2, 1)
        steps = steps_to_win(gs.last_step, gs.grid, p1, p2)
        if steps == 0:
            score = WIN_SCORE - (self._max_depth - depth)
            return score if maximize else -score
        if depth <= 0:
            # return steps to win the lower the better
            return float(-steps if maximize else steps)
        return None


class Mtd(AlphaBeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._guess_step = None

    def run(self, gs: GameState) -> Optional[int]:
        self._guess_step = None
        if gs.last_step is None:
            return _random_cell(gs)
        logger.info("Starting iterative MTD(f) search")
        self._reset_memory()
        pos, score = None, 0.0
        for depth in range(1, self._max_depth):
            logger.info("Starting iterative MTD(f) search at depth %s", depth)
            pos, score = self._mtd(gs, score, depth)
            self._log_hit_rate()
            logger.info("Finished iterative MTD(f) search at depth %s", depth)
            self._guess_step = pos
        logger.info("Finished iterative MTD(f) search")
        return pos

    def _mtd(
        self,
        gs: GameState,
        score: float,
        depth: int,
    ) -> tuple[Optional[int], float]:
        move = None
        upper_bound = math.inf
        lower_bound = -math.inf
        while lower_bound < upper_bound:
            beta = score + 1 if score == lower_bound else score
            move, score = self._memorized_search(gs, depth, True, beta - 1, beta)
            if score < beta:
                upper_bound = score
            else:
                lower_bound = score
        return move, score

    def get_possible_moves(self, gs: GameState) -> list[int]:
        ret = []
        if self._guess_step is not None and not gs.is_taken(self._guess_step):
            ret.append(self._guess_step)
        ret.extend(super().get_possible_moves(gs))
        return ret
