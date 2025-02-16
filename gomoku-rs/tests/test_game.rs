use gomoku_rs::game::{self, check_winning_step, PLAYER_1};

#[test]
fn empty_game() {
    let g = game::Game::default();
    assert_eq!(g.last_step(), None);
    assert_eq!(g.last_player(), game::PLAYER_2);
    assert!(matches!(g.status(), game::GameStatus::Playing));
}

#[test]
fn update_game() {
    let mut g = game::Game::default();
    g.add_cell(5);
    assert_eq!(g.last_step(), Some(5));
    assert_eq!(g.last_player(), game::PLAYER_1);
    assert_eq!(g.grid[5], game::PLAYER_1);
    g.add_cell(6);
    assert_eq!(g.last_step(), Some(6));
    assert_eq!(g.last_player(), game::PLAYER_2);
    assert_eq!(g.grid[6], game::PLAYER_2);
    g.pop_cell();
    assert_eq!(g.last_step(), Some(5));
    assert_eq!(g.last_player(), game::PLAYER_1);
    assert_eq!(g.grid[6], game::EMPTY);
    g.pop_cell();
    assert_eq!(g.last_step(), None);
    assert_eq!(g.last_player(), game::PLAYER_2);
    assert_eq!(g.grid[5], game::EMPTY);
}

#[test]
fn steps_to_win() {
    let arr: [(usize, Vec<usize>, Vec<usize>, f32); 6] = [
        (0, vec![0], vec![], 4.0),
        (0, vec![0, 1, 5], vec![], 3.0),
        (0, vec![0, 1, 3, 4], vec![], 1.0),
        (
            0,
            vec![0, 1, 3, 4],
            vec![2, game::GRID_ROWS, game::GRID_ROWS + 1],
            f32::INFINITY,
        ),
        (1, vec![0, 1, 3, 4], vec![], 1.0),
        (429, vec![429], vec![405], 4.0),
    ];

    for (pos, p1, p2, expected) in arr {
        let g = game::create_game(p1, p2);
        let result = game::steps_to_win(pos, &g.grid, game::PLAYER_1, game::PLAYER_2);
        assert_eq!(result, expected);
    }
}

#[test]
fn test_victory() {
    let arr: [Vec<(i32, i32)>; 6] = [
        vec![(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],
        vec![(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
        vec![(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
        vec![(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)],
        vec![(1, 2), (4, 2), (2, 2), (3, 2), (5, 2)],
        vec![(1, 4), (2, 3), (0, 5), (3, 2), (4, 1)],
    ];

    for cells in arr {
        let mut p1: Vec<usize> = Vec::new();
        for cell in cells {
            p1.push(game::get_pos(cell));
        }
        let last_step = p1.last().copied().unwrap();
        let g = game::create_game(p1, Vec::new());
        let result = check_winning_step(&g.grid, last_step, PLAYER_1);
        assert!(result);
    }
}

#[test]
fn test_get_neigh() {
    let result = game::get_neigh(0);
    let expected = vec![game::GRID_ROWS, game::GRID_ROWS + 1, 1];
    assert_eq!(result, expected);

    let result = game::get_neigh(80);
    //        53  55  56
    //        79  80  81
    //        104 105 106
    let expected = vec![105, 106, 81, 56, 55, 54, 79, 104];
    assert_eq!(result, expected);
}
