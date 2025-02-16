pub const GRID_ROWS: usize = 25;
const GRID_ROWS_I: i32 = 25;
pub const GRID_SIZE: usize = GRID_ROWS * GRID_ROWS;
pub const EMPTY: i8 = 0;
pub const PLAYER_1: i8 = 1;
pub const PLAYER_2: i8 = 2;

pub enum GameStatus {
    Playing,
    Draw,
    Finished,
}

#[derive(Clone)]
pub struct Game {
    pub p1: Vec<usize>,
    pub p2: Vec<usize>,
    pub grid: [i8; GRID_SIZE],
}

impl Game {
    pub fn is_taken(&self, pos: usize) -> bool {
        self.grid[pos] != EMPTY
    }

    pub fn last_player(&self) -> i8 {
        if self.p1.len() == self.p2.len() {
            PLAYER_2
        } else {
            PLAYER_1
        }
    }

    pub fn last_step(&self) -> Option<usize> {
        if self.p1.len() == 0 {
            None
        } else if self.last_player() == PLAYER_1 {
            self.p1.last().copied()
        } else {
            self.p2.last().copied()
        }
    }

    pub fn status(&self) -> GameStatus {
        let mut is_full = true;
        for i in self.grid {
            if i == 0 {
                is_full = false;
                break;
            }
        }
        if is_full {
            return GameStatus::Draw;
        }
        let last_step = self.last_step();
        if last_step.is_some()
            && check_winning_step(&self.grid, last_step.unwrap(), self.last_player())
        {
            return GameStatus::Finished;
        }
        return GameStatus::Playing;
    }

    pub fn add_cell(&mut self, pos: usize) {
        if self.last_player() == PLAYER_1 {
            self.grid[pos] = PLAYER_2;
            self.p2.push(pos);
        } else {
            self.grid[pos] = PLAYER_1;
            self.p1.push(pos);
        }
    }

    pub fn pop_cell(&mut self) {
        let pos = if self.last_player() == PLAYER_1 {
            self.p1.pop()
        } else {
            self.p2.pop()
        };
        self.grid[pos.unwrap()] = EMPTY;
    }
}

pub fn create_game(p1: Vec<usize>, p2: Vec<usize>) -> Game {
    let mut grid: [i8; GRID_SIZE] = [0; GRID_SIZE];
    for i in &p1 {
        grid[*i] = PLAYER_1;
    }
    for i in &p2 {
        grid[*i] = PLAYER_2;
    }
    Game {
        p1: p1,
        p2: p2,
        grid: grid,
    }
}

impl Default for Game {
    fn default() -> Game {
        Game {
            p1: Vec::new(),
            p2: Vec::new(),
            grid: [0; GRID_SIZE],
        }
    }
}

pub fn check_winning_step(grid: &[i8; GRID_SIZE], step: usize, player: i8) -> bool {
    steps_to_win(step, grid, player, 3) == 0.0
}

pub fn steps_to_win(pos: usize, grid: &[i8; GRID_SIZE], player: i8, opponent: i8) -> f32 {
    assert_eq!(grid[pos], player);

    let check_direction = |row_inc: i32, col_inc: i32| -> f32 {
        let mut left = 0;
        let mut cell = get_row_col(pos.try_into().unwrap());

        while left < 4 && is_inside(increment_cell(cell, -row_inc, -col_inc)) {
            cell = increment_cell(cell, -row_inc, -col_inc);
            left += 1;
        }

        let mut curr_best = std::f32::INFINITY;
        let mut taken = 0;
        let mut to_take = 0;
        let mut left_cell = cell.clone();
        let mut right_cell = cell.clone();
        let loop_end = left + 5;
        for _ in 0..loop_end {
            if !is_inside(right_cell) {
                break;
            }
            let next_pos = get_pos(right_cell);
            if grid[next_pos] == opponent {
                to_take = 0;
                taken = 0;
            } else if grid[next_pos] == player || next_pos == pos {
                taken += 1;
            } else {
                to_take += 1;
            }
            if taken + to_take == 5 {
                curr_best = f32::min(curr_best, to_take as f32);
                if grid[get_pos(left_cell)] == player {
                    taken -= 1;
                } else {
                    to_take -= 1;
                }
                left_cell = increment_cell(left_cell, row_inc, col_inc)
            }
            right_cell = increment_cell(right_cell, row_inc, col_inc)
        }
        return curr_best;
    };
    f32::min(
        f32::min(check_direction(1, 0), check_direction(0, 1)),
        f32::min(check_direction(1, 1), check_direction(1, -1)),
    )
}

pub fn get_row_col(pos: usize) -> (i32, i32) {
    (
        (pos / GRID_ROWS).try_into().unwrap(),
        (pos % GRID_ROWS).try_into().unwrap(),
    )
}

pub fn increment_cell(cell: (i32, i32), row_inc: i32, col_inc: i32) -> (i32, i32) {
    (cell.0 + row_inc, cell.1 + col_inc)
}

pub fn is_inside(cell: (i32, i32)) -> bool {
    cell.0 >= 0 && cell.0 < GRID_ROWS_I && cell.1 >= 0 && cell.1 < GRID_ROWS_I
}

pub fn get_pos(cell: (i32, i32)) -> usize {
    (cell.0 * GRID_ROWS_I + cell.1)
        .try_into()
        .unwrap_or_else(|_| panic!("cell.0: {} cell.1 {}", cell.0, cell.1))
}

pub fn get_neigh(pos: usize) -> Vec<usize> {
    let increments = [
        (1, 0),
        (1, 1),
        (0, 1),
        (-1, 1),
        (-1, 0),
        (-1, -1),
        (0, -1),
        (1, -1),
    ];
    let cell = get_row_col(pos);
    let mut ret: Vec<usize> = Vec::new();
    for (r, c) in increments {
        let new_cell = increment_cell(cell, r, c);
        if is_inside(new_cell) {
            ret.push(get_pos(new_cell));
        }
    }
    return ret;
}
