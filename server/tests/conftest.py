import pytest
import docker
import aioredis
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.stop()
    loop.close()


@pytest.fixture(scope="session")
async def db(event_loop):
    client = docker.from_env()
    container = None
    port = "6379"
    try:
        container = client.containers.run(
            "redis", ports={port: port}, detach=True, auto_remove=True
        )
        db = aioredis.Redis(host="localhost", port=int(port))
        yield db
        await db.close()
    finally:
        if container is not None:
            container.stop()
