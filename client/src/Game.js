import { Component } from "react";
import { Alert, Button } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import "./Game.css";

const gridrows = 25;

const GameStatus = {
  // first three must match server encoding
  PLAYING: 0,
  DRAW: 1,
  FINISHED: 2,
  WAITING: 3,
  NOT_FOUND: 4,
  OPPONENT_LEFT: 5,
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
      gameFound: null,
      opponentTurn: null,
      status: GameStatus.WAITING,
      cells: Array(gridrows * gridrows).fill(null),
      prevCellIndex: null,
      isFirstPlayer: null,
    };
    this.handleMessage = this.handleMessage.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.undo = this.undo.bind(this);
  }

  componentDidMount() {
    const token = localStorage.getItem("token");
    let params = new URLSearchParams(window.location.search);
    params.append("q", token);
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
      `${proto}://${window.location.host}/ws/play/${
        this.props.opponent
      }?${params.toString()}`
    );
    socket.onopen = function (e) {
      console.log("Opening ws connection");
    };
    socket.onmessage = this.handleMessage;
    socket.onclose = function (e) {
      console.log(`Closing ws connection with code ${e.code}`);
    };
    this.socket = socket;
  }

  handleMessage(e) {
    console.log(`received message ${e.data}`);
    // first message is GameFound message
    if (this.state.gameFound === null) {
      const { found, first } = JSON.parse(e.data);
      const status = found ? GameStatus.PLAYING : GameStatus.NOT_FOUND;
      this.setState({
        gameFound: found,
        opponentTurn: !first,
        status: status,
        isFirstPlayer: first,
      });
    } else {
      const { status, opponent, cell, valid, opponent_left, undo } = JSON.parse(
        e.data
      );
      if (undo === true) {
        let cells = this.state.cells;
        cells[cell] = null;
        // cells = this.clearCellsBackground();
        this.setState({ opponentTurn: !opponent, cells: cells, prevCellIndex: null });
      } else if (opponent_left === true) {
        this.setState({ status: GameStatus.OPPONENT_LEFT });
      } else if (valid === true) {
        let cells = this.state.cells;
        // clear highligh of the last step
        const prevCellIndex = this.state.prevCellIndex;
        if (prevCellIndex !== null) {
          cells[prevCellIndex].backgroundColor = "white"
        }
        const p = this.state.isFirstPlayer === opponent;
        cells[cell] = new CellData(p, "yellow");
        if (status === GameStatus.FINISHED) {
          const keys = [...Array(cells.length).keys()].filter((i) => {
            return cells[i] !== null && cells[i].firstPlayer === p;
          });
          const winningCells = this.getWinningCells(keys, cell);
          for (const i of winningCells) {
            cells[i] = new CellData(p, "yellow");
          }
        }
        this.setState({
          opponentTurn: !opponent,
          status: status,
          cells: cells,
          prevCellIndex: cell,
        });
      }
    }
  }

  clearCellsBackground(cells) {
      for (const i of cells) {
        cells[i] = new CellData(cells[i].firstPlayer, "white");
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
      return [];
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

  handleClick(i) {
    if (
      this.state.gameFound === true &&
      this.state.cells[i] === null &&
      !this.state.opponentTurn &&
      !this.state.status !== GameStatus.FINISHED
    ) {
      this.socket.send(JSON.stringify({ cell: i }));
    }
  }

  undo() {
    this.socket.send(JSON.stringify({ undo: true }));
  }

  render() {
    const { status, opponentTurn } = this.state;
    let alert = (
      <Alert variant="info">
        {opponentTurn ? "Opponent Turn" : "Your Turn"}
      </Alert>
    );
    switch (status) {
      case GameStatus.WAITING:
        alert = <Alert variant="info">Waiting</Alert>;
        break;
      case GameStatus.NOT_FOUND:
        alert = <Alert variant="warning">No player found</Alert>;
        break;
      case GameStatus.OPPONENT_LEFT:
        alert = <Alert variant="success">Victory - Opponent Left</Alert>;
        break;
      case GameStatus.DRAW:
        alert = <Alert variant="info">Draw</Alert>;
        break;
      case GameStatus.FINISHED:
        if (opponentTurn) {
          alert = <Alert variant="success">Victory</Alert>;
        } else {
          alert = <Alert variant="danger">Defeat</Alert>;
        }
        break;
      default:
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
    console.log("Cell is ", cell);
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
