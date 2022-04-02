import asyncio
import pytest
import uvicorn
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosedError

from app import create_app, Config
from game_manager import GameManager
from game import GameStatus
from messages import GameFound, GameStep, StepRequest

PORT = 5002


@pytest.fixture(scope="session")
async def server(db, event_loop: asyncio.AbstractEventLoop):
    config = uvicorn.Config(
        app=create_app(db, Config(2, 2)), host="localhost", port=PORT, loop=event_loop
    )
    server = uvicorn.Server(config)
    event_loop.create_task(server.serve())
    yield
    await server.shutdown()


@pytest.fixture(scope="session")
async def game_manager(db, event_loop: asyncio.AbstractEventLoop):
    gm = GameManager(db)
    event_loop.create_task(gm.run())
    yield
    await gm.shutdown()


@pytest.mark.asyncio
@pytest.mark.usefixtures("server", "game_manager")
@pytest.mark.parametrize("endpoint", ["/", "/healthz"])
async def test_health(endpoint):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://localhost:{PORT}{endpoint}") as resp:
            assert resp.status == 200


@pytest.mark.asyncio
@pytest.mark.usefixtures("server", "game_manager")
async def test_play_player_no_game():
    with pytest.raises(ConnectionClosedError):
        async with websockets.connect(f"ws://localhost:{PORT}/ws/play/player") as ws:
            await ws.recv()

    async with websockets.connect(f"ws://localhost:{PORT}/ws/play/player?q=xxx") as ws:
        data = await ws.recv()
        assert GameFound.load(data).found is False


@pytest.mark.asyncio
@pytest.mark.usefixtures("server", "game_manager")
@pytest.mark.parametrize("room", ["abcd", None])
async def test_play_player_game_win(room):
    r = f"&r={room}" if room else ""
    async with websockets.connect(
        f"ws://localhost:{PORT}/ws/play/player?q=xxx{r}"
    ) as ws1:
        async with websockets.connect(
            f"ws://localhost:{PORT}/ws/play/player?q=yyy{r}"
        ) as ws2:
            data1 = GameFound.load(await ws1.recv())
            data2 = GameFound.load(await ws2.recv())
            if data1.first:
                assert not data2.first
            else:
                ws1, ws2 = ws2, ws1
                assert data2.first

            for i in range(1, 5):
                await send_step(ws1, cell=i)
                await ws1.recv()
                await ws2.recv()

                await send_step(ws2, cell=20 + i)
                await ws1.recv()
                await ws2.recv()

            await send_step(ws1, cell=5)
            data = await ws1.recv()
            game_step = GameStep.load(data)
            assert game_step.status == GameStatus.Finished
            assert game_step.opponent is False


@pytest.mark.asyncio
@pytest.mark.usefixtures("server", "game_manager")
async def test_play_player_opponent_left():
    async with websockets.connect(f"ws://localhost:{PORT}/ws/play/player?q=xxx") as ws1:
        async with websockets.connect(
            f"ws://localhost:{PORT}/ws/play/player?q=yyy"
        ) as ws2:
            data1 = GameFound.load(await ws1.recv())
            await ws2.recv()

        if data1.first:
            await send_step(ws1, cell=1)
            await ws1.recv()

        game_step = GameStep.load(await ws1.recv())
        assert game_step.opponent_left


@pytest.mark.asyncio
@pytest.mark.usefixtures("server", "game_manager")
async def test_play_ai():
    async with websockets.connect(f"ws://localhost:{PORT}/ws/play/ai?first=true") as ws:
        data = GameFound.load(await ws.recv())
        assert data.found is True
        assert data.first is True

        await send_step(ws, cell=1)
        data = GameStep.load(await ws.recv())
        assert data.opponent is False
        assert data.status == 0
        assert data.valid is True
        assert data.cell == 1

        data = GameStep.load(await ws.recv())
        assert data.opponent is True
        assert data.status == 0
        assert data.valid is True

        # test undo
        await send_step(ws, undo=True)
        data = GameStep.load(await ws.recv())
        assert data.undo is True
        data = GameStep.load(await ws.recv())
        assert data.undo is True and data.cell == 1

        # cannot undo
        await send_step(ws, undo=True)
        data = GameStep.load(await ws.recv())
        assert data.valid is False

        # manual redo
        await send_step(ws, cell=1)
        data = GameStep.load(await ws.recv())
        assert data.valid is True
        assert data.cell == 1


def send_step(ws, **kwargs):
    return ws.send(StepRequest(**kwargs).dump().decode())
