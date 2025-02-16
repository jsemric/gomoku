use gomoku_rs::server::serve;
use tokio;
use std::env;

#[tokio::main]
async fn main() {
    let port_str = env::var("PORT").unwrap_or(String::from("8080"));
    let port: u16 = port_str.parse().expect("port should be a valid interger");
    println!("Serving on port {port}");
    serve(port).await;
}
