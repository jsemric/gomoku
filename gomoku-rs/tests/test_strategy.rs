use gomoku_rs::game;
use gomoku_rs::strategy;

macro_rules! dummy_beats_random {
    ($($name:ident: $value:expr,)*) => {
    $(
        #[test]
        fn $name() {
            let (r, c) = $value;
            let mut s1 = strategy::RandomStrategy{};
            let mut s2 = strategy::DummyStrategy::new(r, c);
            second_strategy_wins(& mut s1, & mut s2);
        }
    )*
    }
}

macro_rules! alphabeta_beats_dummy {
    ($($name:ident: $value:expr,)*) => {
    $(
        #[test]
        fn $name() {
            let (r, c) = $value;
            let mut s1 = strategy::DummyStrategy::new(r, c);
            let mut s2 = strategy::AlphaBeta::new(4, false);
            second_strategy_wins(& mut s1, & mut s2);
        }
    )*
    }
}

dummy_beats_random! {
    dummy_0: (0, 1),
    dummy_1: (1, 1),
    dummy_2: (1, 0),
    dummy_3: (1, -1),
    dummy_4: (-1, -1),
    dummy_5: (-1, 1),
    dummy_6: (-1, 0),
    dummy_7: (0, -1),
}

alphabeta_beats_dummy! {
    alpha_dummy_0: (0, 1),
    alpha_dummy_1: (1, 1),
    alpha_dummy_2: (1, 0),
    alpha_dummy_3: (1, -1),
    alpha_dummy_4: (-1, -1),
    alpha_dummy_5: (-1, 1),
    alpha_dummy_6: (-1, 0),
    alpha_dummy_7: (0, -1),
}

#[test]
fn alphabeta_beats_random() {
    let mut s1 = strategy::RandomStrategy {};
    let mut s2 = strategy::AlphaBeta::new(4, true);
    second_strategy_wins(&mut s1, &mut s2);
}

fn second_strategy_wins<T1: strategy::Strategy, T2: strategy::Strategy>(s1: &mut T1, s2: &mut T2) {
    let mut g = game::Game::default();
    for _ in 0..30 {
        let cell = s1.run(&g);
        assert!(!g.is_taken(cell));
        g.add_cell(cell);
        if matches!(g.status(), game::GameStatus::Finished) {
            strategy::print_grid(&g);
        }
        assert!(
            matches!(g.status(), game::GameStatus::Playing),
            "First strategy won"
        );
        let cell = s2.run(&g);
        assert!(!g.is_taken(cell));
        g.add_cell(cell);
        if matches!(g.status(), game::GameStatus::Finished) {
            break;
        }
    }
    if matches!(g.status(), game::GameStatus::Playing) {
        strategy::print_grid(&g);
    }
    assert!(
        matches!(g.status(), game::GameStatus::Finished),
        "Second strategy did not win"
    );
}
