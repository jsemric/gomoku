import { Component } from "react";
import { Container, Row, Col} from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import { v4 as uuid4 } from "uuid";
import Game from "./Game.js";

class App extends Component {
  componentDidMount() {
    if (localStorage.getItem("token") === null) {
      localStorage.setItem("token", uuid4());
    }
    document.title = "Gomoku";
  }

  render() {
    return (
      <Container>
        <Row>
          <Col>
            <Game></Game>
          </Col>
        </Row>
      </Container>
    );
  }
}

export default App;
