import Game from "./Game";

test("select winning cells", () => {
  const game = new Game({});
  let result = game.getWinningCells([1, 2, 3, 4, 5], 3);
  expect(result).toStrictEqual([1, 2, 3, 4, 5]);

  result = game.getWinningCells([1, 2, 3, 4, 5], 5);
  expect(result).toStrictEqual([1, 2, 3, 4, 5]);

  result = game.getWinningCells([1, 2, 3, 4, 6], 4);
  expect(result).toStrictEqual([]);
});
