import aioredis
import logging
import random
import asyncio

from typing import Optional
from messages import FindGameRequest, FindGameResponse

logger = logging.getLogger(__name__)


class GameManager:
    GAME_CHANNEL = "find_game"

    def __init__(self, db: aioredis.Redis):
        self._db = db
        self._stack = set()  # TODO: replace with redis sorted set?
        self._rooms: dict[str, str] = {}
        self._sub: Optional[aioredis.client.PubSub] = None

    async def run(self, max_messages=None):
        logger.debug("Running Game Manager")
        self._sub = self._db.pubsub()
        await self._sub.subscribe(self.GAME_CHANNEL)
        msg_count = 0
        async for msg in self._sub.listen():
            if msg["type"] == "message":
                await self.on_message(FindGameRequest.load(msg["data"]))
                msg_count += 1
                if max_messages and max_messages <= msg_count:
                    break

    async def on_room_message(self, request: FindGameRequest):
        if request.is_remove:
            logger.debug("Removing: %s from room %s", request.player, request.room)
            if request.player in self._rooms.get(request.room, {}):
                del self._rooms[request.room]
        elif request.room not in self._rooms:
            logger.debug("Adding: %s to room %s", request.player, request.room)
            self._rooms[request.room] = request.player
        else:
            logger.debug("Adding: %s to room %s", request.player, request.room)
            await self.notify_players(self._rooms[request.room], request.player)
            del self._rooms[request.room]

    async def on_message(self, request: FindGameRequest):
        if request.room is not None:
            await self.on_room_message(request)
            return
        if request.is_remove:
            logger.debug("Removing: %s", request.player)
            if request.player in self._stack:
                self._stack.remove(request.player)
            return
        logger.debug("Adding: %s", request.player)
        self._stack.add(request.player)
        if len(self._stack) > 1:
            client_id1 = self._stack.pop()
            client_id2 = self._stack.pop()
            await self.notify_players(client_id1, client_id2)

    async def notify_players(self, client_id1, client_id2):
        first_is_first = random.randint(0, 1) % 2 == 1
        logger.debug("Publishing for clients %s %s", client_id1, client_id2)
        await self._db.publish(
            client_id1, FindGameResponse(client_id2, first_is_first).dump()
        )
        await self._db.publish(
            client_id2, FindGameResponse(client_id1, not first_is_first).dump()
        )

    async def shutdown(self):
        logger.debug("Shutting down GameManager")
        await self._sub.unsubscribe(self.GAME_CHANNEL)


if __name__ == "__main__":
    import os

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    host = os.getenv("REDIS_HOST")
    port = int(os.getenv("REDIS_PORT"))
    db = aioredis.from_url(f"redis://{host}:{port}")
    asyncio.get_event_loop().run_until_complete(GameManager(db).run())
