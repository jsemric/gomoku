import os
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from gomoku.strategy import Mtd
from gomoku.game import validate, GameError, GameStatus, GameState

HEALTH_ENDPOINTS = ["/", "/healthz"]
logger = logging.getLogger(__name__)


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return (
            record.args
            and len(record.args) >= 3
            and record.args[2] not in HEALTH_ENDPOINTS
        )


# Add filter to the logger
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


class NextMoveRequest(BaseModel):
    player_cells: list[int]
    opponent_cells: list[int]


class NextMoveResponse(BaseModel):
    status: str
    next_move: Optional[int] = None


def create_app():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s",
    )
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
    app = FastAPI()

    @app.get("/")
    @app.get("/healthz")
    async def healthz():
        return {"healthy": True}

    @app.post("/api/next-move")
    async def next_move(game: NextMoveRequest):
        player_cells = game.player_cells
        opponent_cells = game.opponent_cells
        try:
            validate(set(player_cells), set(opponent_cells))
        except GameError as err:
            raise HTTPException(400, str(err))
        gs = GameState.create(player_cells, opponent_cells)
        if gs.status != GameStatus.Playing:
            raise HTTPException(400, f"Game status: {gs.status.name}")
        strategy = Mtd()
        opponent_next_step = strategy.run(gs)
        gs.add_cell(opponent_next_step)
        if gs.status == GameStatus.Finished:
            logger.info("AI won the game")
        return NextMoveResponse(status=gs.status.name, next_move=opponent_next_step)

    return app
