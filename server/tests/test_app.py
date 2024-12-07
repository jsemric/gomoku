import pytest
from fastapi.testclient import TestClient

from gomoku.game import GameStatus
from gomoku.app import create_app, NextMoveRequest


@pytest.fixture
def test_client():
    return TestClient(create_app())


@pytest.mark.parametrize("endpoint", ["/", "/healthz"])
def test_health(test_client: TestClient, endpoint: str):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "player1_cells, player2_cells",
    [
        ([-1], []),
        ([1, 2, 3], [4]),
        ([1, 2, 3], [4, 4]),
    ],
)
def test_next_move_with_invalid_data(
    test_client: TestClient, player1_cells, player2_cells
):
    data = NextMoveRequest(
        player_cells=player1_cells,
        opponent_cells=player2_cells,
    ).json()
    response = test_client.post("/api/next-move", data=data)
    assert response.status_code == 400


def test_next_move(test_client: TestClient):
    data = NextMoveRequest(player_cells=[], opponent_cells=[]).json()
    response = test_client.post("/api/next-move", data=data)
    assert response.status_code == 200, response.json()["detail"]
    assert response.json()["status"] == GameStatus.Playing.name

    data = NextMoveRequest(player_cells=[1], opponent_cells=[]).json()
    response = test_client.post("/api/next-move", data=data)
    assert response.status_code == 200, response.json()["detail"]
    assert response.json()["status"] == GameStatus.Playing.name
