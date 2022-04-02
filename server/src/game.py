import logging
from typing import Optional
from enum import IntEnum

from exceptions import GameAlreadyFinished, InvalidStep

try:
    from mtd import Mtd, check_winning_step
except ImportError:
    Mtd = lambda *_: None
    check_winning_step = lambda *_: False


GRID_ROWS = 25
GRID_SIZE = GRID_ROWS * GRID_ROWS
logger = logging.getLogger(__name__)


class GameStatus(IntEnum):
    Playing = 0
    Draw = 1
    Finished = 2


class Game:
    def __init__(self):
        self._player1_cells = set()
        self._player2_cells = set()
        self._player2_turn: bool = False
        self._status: GameStatus = GameStatus.Playing
        self._last_step: Optional[int] = None
        self._steps = []
        self._algo = Mtd(5)

    @property
    def finished(self):
        return self._status != GameStatus.Playing

    @property
    def status(self):
        return self._status

    @property
    def last_step(self):
        return self._last_step

    @property
    def player_data(self):
        return list(self._player1_cells), list(self._player2_cells)

    def undo(self):
        if not self._steps:
            raise InvalidStep("Cannot undo")
        if self._player2_turn:
            self._player1_cells.remove(self._steps[-1])
            self._player2_turn = False
        else:
            self._player2_cells.remove(self._steps[-1])
            self._player2_turn = True
        ret = self._steps.pop()
        self._status = GameStatus.Playing
        self._last_step = self._steps[-1] if self._steps else None
        return ret

    @property
    def player2_turn(self):
        return self._player2_turn

    def take(self, pos: int) -> bool:
        if self.finished:
            raise GameAlreadyFinished("Game already finished")
        if self.taken(pos):
            raise InvalidStep(f"Cell {pos} already taken")
        if not (0 <= pos < GRID_SIZE):
            raise InvalidStep(f"Cell {pos} out of grid")
        logger.debug("Player %s takes %s", "2" if self._player2_turn else "1", pos)
        if self._player2_turn:
            self._player2_cells.add(pos)
            self._last_step = pos
        else:
            self._player1_cells.add(pos)
            self._last_step = pos

        self._update_status()
        self._player2_turn = not self._player2_turn
        self._steps.append(pos)
        return self.finished

    def _update_status(self):
        if self.check_victory(self._player2_turn):
            self._status = GameStatus.Finished
        if len(self._player1_cells) + len(self._player2_cells) == GRID_SIZE:
            self._status = GameStatus.Playing

    def taken(self, pos: int) -> bool:
        return pos in self._player1_cells or pos in self._player2_cells

    def check_victory(self, player2: bool = False):
        cells = self._player2_cells if player2 else self._player1_cells
        return check_winning_step(cells, self._last_step)

    def next_step(self) -> int:
        p1, p2 = self._player1_cells, self._player2_cells
        if self._player2_turn:
            p1, p2 = self._player2_cells, self._player1_cells
        pos = self._algo.run(p1, p2, self._last_step)
        self.take(pos)
        return pos
