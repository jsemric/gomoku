import pytest
import logging
import aioredis

from game_manager import GameManager
from messages import FindGameRequest, FindGameResponse


@pytest.mark.asyncio
async def test_find_game(db: aioredis.Redis, event_loop):
    gm = GameManager(db)
    event_loop.create_task(gm.run())

    id1 = "xxx-xx1"
    id2 = "xxx-xx2"
    sub = db.pubsub()
    await sub.subscribe(id1)
    await db.publish(gm.GAME_CHANNEL, FindGameRequest(id1).dump())
    await db.publish(gm.GAME_CHANNEL, FindGameRequest(id2).dump())
    await sub.get_message(timeout=3)  # subscribe message
    msg = await sub.get_message(timeout=3)
    logging.debug(msg)
    msg = FindGameResponse.load(msg["data"])
    assert id2 == msg.opponent
