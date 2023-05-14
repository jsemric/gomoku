import pytest
from fastapi.testclient import TestClient

from utils import GameStatus, GRID_SIZE
from app import create_app, NextMoveRequest


@pytest.fixture
def test_client():
    return TestClient(create_app())


@pytest.mark.parametrize("endpoint", ["/", "/healthz"])
def test_health(test_client: TestClient, endpoint: str):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "player1_cells, player2_cells, last_step",
    [
        ([-1], [], -1),
        ([1], [], None),
        ([1, 2], [3], 3),
        ([1, 2, 3], [4], 3),
        ([0, 1, 2, 3, 4], [5, 6, 7, 8], 3),
    ],
)
def test_next_move_with_invalid_data(
    test_client: TestClient, player1_cells, player2_cells, last_step
):
    data = NextMoveRequest(
        player_cells=player1_cells,
        opponent_cells=player2_cells,
        player_last_step=last_step,
    ).json()
    response = test_client.post("/api/next-move", data=data)
    assert response.status_code == 400


def test_next_move(test_client: TestClient):
    data = NextMoveRequest(player_cells=[], opponent_cells=[]).json()
    response = test_client.post("/api/next-move", data=data)
    assert response.status_code == 200, response.json()["detail"]
    assert response.json()["status"] == GameStatus.Playing.name

    data = NextMoveRequest(
        player_cells=[1], opponent_cells=[], player_last_step=1
    ).json()
    response = test_client.post("/api/next-move", data=data)
    assert response.status_code == 200, response.json()["detail"]
    assert response.json()["status"] == GameStatus.Playing.name
