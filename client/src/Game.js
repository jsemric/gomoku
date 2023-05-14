import { Component } from "react";
import { Alert, Button } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import "./Game.css";

const gridrows = 25;

const GameStatus = {
  PLAYING: "PLAYING",
  VICTORY: "VICTORY",
  DEFEAT: "DEFEAT",
};

export class CellData {
  constructor(firstPlayer = null, backgroundColor = "white") {
    this.firstPlayer = firstPlayer;
    this.backgroundColor = backgroundColor;
  }
}

class Game extends Component {
  constructor(props) {
    super(props);
    this.state = {
      cells: Array(gridrows * gridrows).fill(null),
      playerCells: [],
      opponentCells: [],
      status: GameStatus.PLAYING,
    };
    this.handleClick = this.handleClick.bind(this);
    this.setCells = this.setCells.bind(this);
    this.undo = this.undo.bind(this);
  }

  isPlayerTurn() {
    return this.state.playerCells.length == this.state.opponentCells.length;
  }

  handleClick(pos) {
    if (
      this.state.cells[pos] === null &&
      this.state.status === GameStatus.PLAYING &&
      this.isPlayerTurn()
    ) {
      this.setCells(pos, false);
      this.nextStep();
    }
  }

  nextStep() {
    const body = {
      player_cells: this.state.playerCells,
      opponent_cells: this.state.opponentCells,
      player_last_step:
        this.state.playerCells[this.state.playerCells.length - 1],
    };
    fetch("/api/next-move", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        this.setCells(data.next_step, true);
      });
  }

  setCells(cell, isOpponent) {
    let cellList = isOpponent
      ? this.state.opponentCells
      : this.state.playerCells;
    let cells = this.state.cells;
    let status = this.state.status;
    if (status != GameStatus.PLAYING) {
      return;
    }
    // clear last cell
    if (cellList.length > 0) {
      const prevCellIndex = cellList[cellList.length - 1];
      cells[prevCellIndex].backgroundColor = "white";
    }
    // set new cell
    cells[cell] = new CellData(isOpponent, isOpponent ? "yellow" : "white");
    cellList.push(cell);

    // check and mark vicotry
    const winningCells = this.getWinningCells(cellList, cell);
    if (winningCells !== null) {
      status = isOpponent ? GameStatus.DEFEAT : GameStatus.VICTORY;
      for (const i of winningCells) {
        cells[i] = new CellData(isOpponent, "yellow");
      }
    }

    if (isOpponent) {
      this.setState({ cells: cells, opponentCells: cellList, status: status });
    } else {
      this.setState({ cells: cells, playerCells: cellList, status: status });
    }
  }

  clearCellsBackground(cells, isOpponent) {
    for (const i of cells) {
      cells[i] = new CellData(isOpponent, "white");
    }
    return cells;
  }

  getWinningCells(cells, last_cell) {
    const set = new Set(cells);
    const directions = [
      this.checkDirection(set, last_cell, 1),
      this.checkDirection(set, last_cell, gridrows),
      this.checkDirection(set, last_cell, gridrows - 1),
      this.checkDirection(set, last_cell, gridrows + 1),
    ];
    const winningDirections = directions.filter((x) => {
      return x.end - x.start >= 4;
    });
    if (!winningDirections.length) {
      return null;
    }
    const { start, end, inc } = winningDirections[0];
    let ret = [];
    for (let i = start; i <= end; i++) {
      ret.push(last_cell + i * inc);
    }
    return ret;
  }

  checkDirection(cells, last_cell, inc) {
    let start = 0;
    let end = 0;
    for (let i = 1; i < 5; i++) {
      if (cells.has(last_cell - i * inc)) {
        start--;
      } else {
        break;
      }
    }
    for (let i = 1; i < 5; i++) {
      if (cells.has(last_cell + i * inc)) {
        end++;
      } else {
        break;
      }
    }
    return { start: start, end: end, inc: inc };
  }

  undo() {
    if (!this.isPlayerTurn()) {
      return;
    }
    let { cells, status, opponentCells, playerCells } = this.state;
    // clear up highligh after defeat
    if (status === GameStatus.DEFEAT) {
      const winningCells = this.getWinningCells(
        opponentCells,
        opponentCells[opponentCells.length - 1]
      );
      winningCells.forEach((cell) => {
        cells[cell] = new CellData(true, "white");
      });
    }
    // remove 1 cell from player and opponent
    if (playerCells.length > 0) {
      cells[playerCells.pop()] = null;
      cells[opponentCells.pop()] = null;
    }
    // highlight last opponent cell
    if (opponentCells.length > 0) {
      cells[opponentCells[opponentCells.length - 1]] = new CellData(
        true,
        "yellow"
      );
    }
    this.setState({
      status: GameStatus.PLAYING,
      cells: cells,
      opponentCells: opponentCells,
      playerCells: playerCells,
    });
  }

  render() {
    const status = this.state.status;
    const isPlayerTurn = this.isPlayerTurn();
    var alert;
    switch (status) {
      case GameStatus.PLAYING:
        alert = (
          <Alert variant="info">
            {isPlayerTurn ? "Your Turn" : "Opponent Turn"}
          </Alert>
        );
        break;
      case GameStatus.DEFEAT:
        alert = <Alert variant="danger">Defeat</Alert>;
        break;
      case GameStatus.VICTORY:
        alert = <Alert variant="success">Victory</Alert>;
        break;
      default:
        break;
    }
    return (
      <div>
        {alert}
        <div>
          <Board cells={this.state.cells} onClick={this.handleClick} />
        </div>
        <div>
          <Button onClick={this.undo}>Undo</Button>
        </div>
      </div>
    );
  }
}

class Board extends Component {
  renderCell(i) {
    return (
      <Cell
        id={`cell_${i}`}
        cell={this.props.cells[i]}
        onClick={() => this.props.onClick(i)}
      />
    );
  }

  render() {
    const board = [];
    for (let i = 0; i < gridrows; i++) {
      const row = [];
      for (let j = 0; j < gridrows; j++) {
        row.push(this.renderCell(j * gridrows + i));
      }
      board.push(<div className="board-row">{row}</div>);
    }
    return <div>{board}</div>;
  }
}

class Cell extends Component {
  render() {
    const cell = this.props.cell;
    if (cell === null) {
      return (
        <div
          id={this.props.id}
          className={"grid-cell"}
          onClick={this.props.onClick}
        >
          {Svg(this.props, <></>)}
        </div>
      );
    }
    return (
      <div
        id={this.props.id}
        className={"grid-cell"}
        onClick={this.props.onClick}
        style={{ backgroundColor: cell.backgroundColor }}
      >
        {cell.firstPlayer === true
          ? Circle(this.props, cell.backgroundColor)
          : Cross(this.props)}
      </div>
    );
  }
}

function Svg(props, element) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      display="inline"
      width="100%"
      viewBox="0 0 50 50"
    >
      {element}
    </svg>
  );
}

function Circle(props, fill = "white") {
  return Svg(
    props,
    <circle
      id="circle1"
      r="20"
      cx="25"
      cy="25"
      style={{ fill: fill, stroke: "green", "stroke-width": 10 }}
    />
  );
}

function Cross(props) {
  return Svg(
    props,
    <>
      <line x1="5" y1="5" x2="45" y2="45" stroke="red" stroke-width="10" />
      <line x1="45" y1="5" x2="5" y2="45" stroke="red" stroke-width="10" />
    </>
  );
}

export default Game;
