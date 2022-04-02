import asyncio
import os
import logging
import random
from dataclasses import asdict, dataclass
from typing import Optional
from uuid import uuid4

import aioredis
from fastapi import FastAPI, WebSocket, Cookie, Query, status, WebSocketDisconnect

from game import Game
from game_manager import GameManager
from messages import FindGameRequest, FindGameResponse, GameFound, GameStep, StepRequest
from exceptions import *
from tasks import run_mtd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    find_game_timeout: float
    player_move_timeout: float
    redis_host: str = None
    redis_port: str = None
    use_celery: bool = False


def setup_app():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    config = Config(
        find_game_timeout=_getenv("FIND_GAME_TIMEOUT", 30, float),
        player_move_timeout=_getenv("PLAYER_MOVE_TIMEOUT", 30, float),
        redis_host=_getenv("REDIS_HOST", "localhost"),
        redis_port=_getenv("REDIS_PORT", 6379, int),
        use_celery=True,
    )
    db = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
    return create_app(db, config)


def _getenv(env_name: str, default_val=None, dtype: type = None):
    ret = os.getenv(env_name, default_val)
    return dtype(ret) if dtype is not None else ret


def create_app(db: aioredis.Redis, config: Config):
    app = FastAPI()

    @app.get("/")
    @app.get("/healthz")
    async def healthz():
        return {"healthy": True}

    @app.websocket("/ws/play/ai")
    async def play_ai(websocket: WebSocket, first: Optional[bool] = Query(None)):
        await websocket.accept()
        if first is None:
            first = bool(random.randint(0, 1))
        logger.debug(f"First is {first}")
        await websocket.send_json(GameFound(True, first).asdict())
        game = Game()
        try:
            if not first:
                pos = game.next_step()
                step = GameStep(cell=pos, opponent=True, status=game.status)
                await websocket.send_json(asdict(step))

            while True:
                data = await websocket.receive_text()
                logger.debug("Received data from client %s", data)
                req = StepRequest.load(data)
                try:
                    if req.undo:
                        logger.debug("Undoing")
                        # undo player and AI move
                        cell = game.undo()
                        await websocket.send_json(
                            asdict(GameStep(undo=True, opponent=False, cell=cell))
                        )
                        cell = game.undo()
                        await websocket.send_json(
                            asdict(GameStep(undo=True, opponent=True, cell=cell))
                        )
                    else:
                        pos = req.cell
                        finished = game.take(pos)
                        step = GameStep(cell=pos, opponent=False, status=game.status)
                        logger.debug("Sending step to client %s", step)
                        await websocket.send_json(asdict(step))
                        if finished:
                            break

                        if config.use_celery:
                            p1, p2 = game.player_data
                            res = run_mtd.delay(p1, p2, game.last_step)
                            pos = None
                            while pos is None:
                                if res.ready():
                                    pos = res.get(timeout=1)
                                await asyncio.sleep(0.1)
                            game.take(pos)
                        else:
                            pos = game.next_step()
                        step = GameStep(cell=pos, opponent=True, status=game.status)
                        logger.debug("Sending step to client %s", step)
                        await websocket.send_json(asdict(step))
                except InvalidStep:
                    logger.info("Invalid step")
                    await websocket.send_json(asdict(GameStep(valid=False)))

        except WebSocketDisconnect:
            logger.debug("Client disconnected")
            return
        except Exception as e:
            logger.error("Unexpected error: %s", e, exc_info=True)

        await websocket.close()

    @app.websocket("/ws/play/player")
    async def play_player(
        websocket: WebSocket,
        q: Optional[str] = Query(None),
        r: Optional[str] = Query(None),
    ):
        await websocket.accept()
        if not q:
            await websocket.close(status.WS_1008_POLICY_VIOLATION)
            return
        client_id = q + ":" + str(uuid4())
        logger.debug("User id %s", client_id)
        sub = db.pubsub(ignore_subscribe_messages=True)

        await sub.subscribe(client_id)
        find_game_msg = None
        try:
            find_game_msg = await find_game(
                db,
                sub,
                FindGameRequest(player=client_id, room=r),
                config.find_game_timeout,
            )
            await websocket.send_json(GameFound(True, find_game_msg.first).asdict())

            game = Game()
            if not find_game_msg.first:
                pos = await get_opponent_move(sub, config.player_move_timeout)
                game.take(pos)
                step = GameStep(cell=pos, opponent=True, status=game.status)
                await websocket.send_json(asdict(step))

            while not game.finished:
                data = await websocket.receive_text()
                logger.debug("Received data from client %s", data)
                req = StepRequest.load(data)
                try:
                    finished = game.take(req.cell)
                    step = GameStep(cell=req.cell, opponent=False, status=game.status)
                    logger.debug("Sending step %s to client %s", step, client_id)
                    await websocket.send_json(asdict(step))
                    await db.publish(
                        find_game_msg.opponent, GameStep(cell=req.cell).dump()
                    )
                    if finished:
                        break

                    pos = await get_opponent_move(sub, config.player_move_timeout)
                    game.take(pos)
                    step = GameStep(cell=pos, opponent=True, status=game.status)
                    logger.debug(
                        "Received step %s from opponent %s",
                        step,
                        find_game_msg.opponent,
                    )
                    await websocket.send_json(asdict(step))
                except InvalidStep:
                    await websocket.send_json(asdict(GameStep(valid=False)))

        except NoGameFound:
            logger.debug("No game found")
            await websocket.send_json(GameFound(False, False).asdict())
        except OpponentLeft:
            logger.debug("Opponent left")
            await websocket.send_json(GameStep(opponent_left=True).asdict())
        except WebSocketDisconnect:
            logger.debug("Client disconnected")
            if find_game_msg is not None:
                await db.publish(
                    find_game_msg.opponent, GameStep(opponent_left=True).dump()
                )
            return
        except Exception as e:
            logger.error("Unexpected error: %s", e, exc_info=True)
            if find_game_msg is not None:
                await db.publish(
                    find_game_msg.opponent, GameStep(opponent_left=True).dump()
                )

        await db.publish(
            GameManager.GAME_CHANNEL,
            FindGameRequest(player=client_id, is_remove=True, room=r).dump(),
        )
        await websocket.close()

    return app


async def find_game(
    db: aioredis.Redis,
    sub: aioredis.client.PubSub,
    request: FindGameRequest,
    timeout: float = 15,
) -> FindGameResponse:
    await db.publish(GameManager.GAME_CHANNEL, request.dump())
    await sub.get_message()
    msg = await sub.get_message(timeout=timeout)
    if msg is None:
        raise NoGameFound()
    logger.debug("For request: %s received message: %s", request, msg["data"])
    return FindGameResponse.load(msg["data"])


async def get_opponent_move(sub: aioredis.client.PubSub, timeout: float = 15) -> int:
    msg = await sub.get_message(timeout=timeout)
    logger.debug("Received %s", msg)
    if msg is None:
        raise OpponentLeft()
    move_msg = GameStep.load(msg["data"])
    if move_msg.opponent_left:
        raise OpponentLeft()
    return move_msg.cell
