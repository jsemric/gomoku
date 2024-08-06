import os
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from strategy import Mtd
from utils import get_status, validate, GameError, GameStatus

HEALTH_ENDPOINTS = ["/", "/healthz"]
logger = logging.getLogger(__name__)

class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and len(record.args) >= 3 and record.args[2] not in HEALTH_ENDPOINTS

# Add filter to the logger
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

class NextMoveRequest(BaseModel):
    player_cells: list[int]
    opponent_cells: list[int]
    player_last_step: Optional[int] = None


class NextMoveResponse(BaseModel):
    status: str
    next_step: Optional[int] = None


def create_app():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
    app = FastAPI()

    @app.get("/")
    @app.get("/healthz")
    async def healthz():
        return {"healthy": True}

    @app.post("/api/next-move")
    async def next_move(game: NextMoveRequest):
        player_cells = set(game.player_cells)
        opponent_cells = set(game.opponent_cells)
        player_last_step = game.player_last_step
        try:
            validate(player_cells, opponent_cells, player_last_step)
        except GameError as err:
            raise HTTPException(400, str(err))
        status = get_status(player_cells, opponent_cells, player_last_step)
        if status != GameStatus.Playing:
            raise HTTPException(400, f"Game status: {status.name}")
        strategy = Mtd()
        opponent_next_step = strategy.run(
            opponent_cells, player_cells, player_last_step
        )
        opponent_cells.add(opponent_next_step)
        status = get_status(opponent_cells, player_cells, opponent_next_step)
        if status == GameStatus.Finished:
            logger.info("AI won the game")
        return NextMoveResponse(status=status.name, next_step=opponent_next_step)

    return app
