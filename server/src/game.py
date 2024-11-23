import array
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Generator
from utils import GRID_SIZE, inside_interval_pos, check_winning_step


class GameStatus(str, Enum):
    Playing = "PLAYING"
    Draw = "DRAW"
    Finished = "FINISHED"


class GameError(Exception):
    pass


PLAYER_1 = 1
PLAYER_2 = 2


@dataclass
class GameState:
    p1: list[int]
    p2: list[int]
    grid: array.array

    @classmethod
    def create(cls, p1, p2) -> "GameState":
        grid = array.array("B", [0] * GRID_SIZE)
        for i in p1:
            grid[i] = PLAYER_1
        for i in p2:
            grid[i] = PLAYER_2
        return GameState(p1, p2, grid)

    @contextmanager
    def with_move(self, pos: int) -> Generator["GameState", None, None]:
        self.add_cell(pos)
        yield self
        self.pop_cell()

    def is_taken(self, pos: int) -> bool:
        return self.grid[pos] != 0

    def add_cell(self, pos: int) -> None:
        assert 0 <= pos < GRID_SIZE
        assert not self.is_taken(pos)
        p = self.p1 if self.last_player == PLAYER_2 else self.p2
        p.append(pos)
        self.grid[pos] = self.last_player

    def pop_cell(self) -> None:
        p = self.p1 if self.last_player == PLAYER_1 else self.p2
        self.grid[p.pop()] = 0

    @property
    def last_step(self) -> Optional[int]:
        assert len(self.p1) >= len(self.p2)
        if not self.p1:
            return None
        if self.last_player == PLAYER_1:
            return self.p1[-1]
        return self.p2[-1]

    @property
    def last_player(self) -> int:
        assert len(self.p1) >= len(self.p2)
        if len(self.p1) == len(self.p2):
            return PLAYER_2
        return PLAYER_1

    @property
    def status(self) -> GameStatus:
        if all(i != 0 for i in self.grid):
            return GameStatus.Draw

        if self.last_step is not None and check_winning_step(
            self.grid, self.last_step, self.last_player
        ):
            return GameStatus.Finished
        return GameStatus.Playing


def validate(player_cells: set[int], opponent_cells: set[int]) -> None:
    if any(not inside_interval_pos(cell) for cell in player_cells):
        raise GameError("Player cell outside interval")
    if any(not inside_interval_pos(cell) for cell in opponent_cells):
        raise GameError("Opponent cell outside interval")
    player_cells_num = len(player_cells)
    opponent_cells_num = len(opponent_cells)
    if player_cells_num - opponent_cells_num not in (0, 1):
        raise GameError("Invalid number of cells per player")
    if player_cells & opponent_cells:
        raise GameError("Player and opponent cells overlap")
