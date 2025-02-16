use crate::game;
use core::f32;
use rand::Rng;
use std::collections::HashMap;
use std::collections::HashSet;

const WIN_SCORE: i32 = 10000;

pub trait Strategy {
    fn run(&mut self, g: &game::Game) -> usize;
}

pub struct RandomStrategy;

impl Strategy for RandomStrategy {
    fn run(&mut self, g: &game::Game) -> usize {
        random_pos(g)
    }
}

pub struct DummyStrategy {
    row_inc: i32,
    col_inc: i32,
    last_pos: Option<usize>,
}

impl DummyStrategy {
    pub fn new(row_inc: i32, col_inc: i32) -> Self {
        Self {
            row_inc,
            col_inc: col_inc,
            last_pos: None,
        }
    }
}

impl Strategy for DummyStrategy {
    fn run(&mut self, g: &game::Game) -> usize {
        match self.last_pos {
            None => {
                let pos = random_pos(g);
                self.last_pos.replace(pos);
                return pos;
            }
            Some(pos) => {
                let cell = game::increment_cell(game::get_row_col(pos), self.row_inc, self.col_inc);
                let mut pos;
                if !game::is_inside(cell)
                    || g.is_taken({
                        pos = game::get_pos(cell);
                        pos
                    })
                {
                    pos = random_pos(g);
                }
                self.last_pos.replace(pos);
                return pos;
            }
        }
    }
}

pub struct AlphaBeta {
    max_depth: i32,
    use_mtd: bool,
    memory: HashMap<([i8; game::GRID_SIZE], i32, bool), (Option<usize>, f32, f32)>,
    guess: Option<usize>,
}

impl Strategy for AlphaBeta {
    fn run(&mut self, g: &game::Game) -> usize {
        let mut gs = game::create_game(g.p1.clone(), g.p2.clone());
        self.reset();
        if gs.last_step().is_none() {
            return random_pos(&gs);
        }
        if !self.use_mtd {
            let res =
                self.memorized_search(&mut gs, self.max_depth, true, -f32::INFINITY, f32::INFINITY);
            return res.0.unwrap();
        }
        let mut score = 0.0;
        let mut pos: Option<usize> = None;
        for depth in 1..=self.max_depth {
            (pos, score) = self.mtd(&mut gs, score, depth);
            self.guess = pos;
        }
        return pos.unwrap();
    }
}

impl AlphaBeta {
    pub fn new(max_depth: i32, use_mtd: bool) -> Self {
        Self {
            max_depth,
            use_mtd,
            memory: HashMap::new(),
            guess: None,
        }
    }

    fn mtd(&mut self, g: &mut game::Game, mut score: f32, depth: i32) -> (Option<usize>, f32) {
        let mut pos: Option<usize> = None;
        let mut upper_bound = f32::INFINITY;
        let mut lower_bound = -f32::INFINITY;
        while lower_bound < upper_bound {
            let beta = if score == lower_bound {
                score + 1.0
            } else {
                score
            };
            (pos, score) = self.memorized_search(g, depth, true, beta - 1.0, beta);
            if score < beta {
                upper_bound = score;
            } else {
                lower_bound = score;
            }
        }
        return (pos, score);
    }

    fn reset(&mut self) {
        self.guess = None;
        self.memory.clear();
    }

    fn memorized_search(
        &mut self,
        g: &mut game::Game,
        depth: i32,
        maximize: bool,
        mut alpha: f32,
        mut beta: f32,
    ) -> (Option<usize>, f32) {
        let (mut pos, mut lower_bound, mut upper_bound) = (None, -f32::INFINITY, f32::INFINITY);
        let key = (g.grid, depth, maximize);
        if self.use_mtd && self.memory.contains_key(&key) {
            (pos, lower_bound, upper_bound) = *self.memory.get(&key).unwrap();
            if lower_bound >= beta {
                return (pos, lower_bound);
            }
            if upper_bound <= alpha {
                return (pos, upper_bound);
            }
            alpha = f32::max(alpha, lower_bound);
            beta = f32::min(beta, upper_bound);
        }

        let (best_pos, best_score) = self.search(g, depth, maximize, alpha, beta);

        if self.use_mtd {
            if best_score <= alpha {
                self.memory.insert(key, (best_pos, lower_bound, best_score));
            }
            if beta > best_score && best_score > alpha {
                self.memory.insert(key, (best_pos, best_score, best_score));
            }
            if best_score >= beta {
                self.memory.insert(key, (best_pos, best_score, upper_bound));
            }
        }
        return (best_pos, best_score);
    }

    fn search(
        &mut self,
        g: &mut game::Game,
        depth: i32,
        maximize: bool,
        mut alpha: f32,
        mut beta: f32,
    ) -> (Option<usize>, f32) {
        if g.grid[g.last_step().unwrap()] != g.last_player() {
            print_grid(g);
        }
        assert_eq!(g.grid[g.last_step().unwrap()], g.last_player());
        let score = self.evaluate(&g, depth, !maximize);

        if score.is_some() {
            return (None, score.unwrap());
        }
        assert!(depth > 0);
        let mut best_pos: Option<usize> = None;
        let mut best_score = -f32::INFINITY;
        if maximize {
            for pos in self.get_possible_moves(g) {
                g.add_cell(pos);
                let (_, score) = self.memorized_search(g, depth - 1, !maximize, alpha, beta);
                g.pop_cell();
                if score > best_score {
                    best_pos.replace(pos);
                    best_score = score;
                }
                alpha = f32::max(alpha, score);
                if score >= beta {
                    break;
                }
            }
        } else {
            best_score = f32::INFINITY;
            for pos in self.get_possible_moves(g) {
                g.add_cell(pos);
                let (_, score) = self.memorized_search(g, depth - 1, !maximize, alpha, beta);
                g.pop_cell();
                if score < best_score {
                    best_pos.replace(pos);
                    best_score = score;
                }
                beta = f32::min(beta, score);
                if score <= alpha {
                    break;
                }
            }
        }
        assert!(best_pos.is_some());
        return (best_pos, best_score);
    }

    fn get_possible_moves(&self, g: &game::Game) -> Vec<usize> {
        let mut seen = HashSet::new();
        let mut get_neighs = |v: &Vec<usize>| {
            for pos in v {
                for neigh in game::get_neigh(*pos) {
                    if !g.is_taken(neigh) {
                        seen.insert(neigh);
                    }
                }
            }
        };
        get_neighs(&g.p1);
        get_neighs(&g.p2);

        let mut result = Vec::new();
        match self.guess {
            Some(pos) => {
                if !g.is_taken(pos) {
                    result.push(pos);
                    seen.remove(&pos);
                }
            }
            _ => {}
        };
        for pos in seen {
            result.push(pos);
        }
        return result;
    }

    fn evaluate(&self, g: &game::Game, depth: i32, maximize: bool) -> Option<f32> {
        let (p1, p2) = if maximize {
            (game::PLAYER_2, game::PLAYER_1)
        } else {
            (game::PLAYER_1, game::PLAYER_2)
        };
        let steps = game::steps_to_win(g.last_step()?, &g.grid, p1, p2);
        if steps == 0.0 {
            let win_score: f32 = (WIN_SCORE + depth) as f32;
            return Some(if maximize { win_score } else { -win_score });
        }
        if depth <= 0 {
            return Some(if maximize { -steps } else { steps });
        }
        return None;
    }
}

fn random_pos(g: &game::Game) -> usize {
    let pos = rand::thread_rng().gen_range(0..game::GRID_SIZE);
    if g.is_taken(pos) {
        random_pos(g)
    } else {
        pos
    }
}

pub fn print_grid(g: &game::Game) {
    for i in 0..game::GRID_ROWS {
        let mut buf = Vec::new();
        for j in 0..game::GRID_ROWS {
            let val = g.grid[i * game::GRID_ROWS + j];
            let x = match val {
                game::PLAYER_1 => 'X',
                game::PLAYER_2 => 'O',
                _ => '.',
            };
            buf.push(x);
        }
        let s: String = buf.iter().collect();
        println!("{s}");
    }
}
