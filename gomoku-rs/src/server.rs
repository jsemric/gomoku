use tokio;
use axum::{
    routing::{get, post},
    http::StatusCode,
    Json, Router,
};
use serde::{Deserialize, Serialize};
use crate::{game, strategy::Strategy};
use crate::strategy;

pub async fn serve(port: u16) {
    let app = Router::new()
        .route("/", get(health))
        .route("/health", get(health))
        .route("/healthz", get(health))
        .route("/api/next-move", post(next_move));

    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{port}")).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> &'static str {
    "OK"
}

#[derive(Deserialize)]
struct NextMoveRequest {
    player_cells: Vec<usize>,
    opponent_cells: Vec<usize>
}

#[derive(Serialize)]
struct NextMoveResponse {
    status: String,
    next_move: Option<usize>
}

async fn next_move(Json(payload): Json<NextMoveRequest>) -> (StatusCode, Json<NextMoveResponse>) {
    // let g = game::create_game(payload.opponent_cells, payload.player_cells);
    let g = game::create_game(payload.player_cells, payload.opponent_cells);
    if ! matches!(g.status(), game::GameStatus::Playing) {
        let resp = NextMoveResponse{status: "".to_string(), next_move: None};
        return (StatusCode::BAD_REQUEST, Json(resp));
    }
    let mut algo = strategy::AlphaBeta::new(5, true);
    let result = algo.run(&g);
    let status = match g.status() {
        game::GameStatus::Draw => "Draw",
        game::GameStatus::Playing => "Playing",
        game::GameStatus::Finished => "Finished",
    };
    let resp = NextMoveResponse{status: status.to_string(), next_move: Some(result)};
    (StatusCode::OK, Json(resp))
}