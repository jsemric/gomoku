import { Component } from "react";
import { Container, Row, Col, Navbar, Nav, NavDropdown } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import { BrowserRouter, Switch, Route } from "react-router-dom";
import { v4 as uuid4 } from "uuid";
import Game from "./Game.js";

class App extends Component {
  componentDidMount() {
    if (localStorage.getItem("token") === null) {
      localStorage.setItem("token", uuid4());
    }
    document.title = "mnk game"
  }

  render() {
    return (
      <Container>
        <Row>
          <Col>
            <Navbar bg="dark" variant="dark">
              <Nav className="me-auto">
                <NavDropdown title="New Game">
                  <NavDropdown.Item href="/ai">Against AI</NavDropdown.Item>
                  <NavDropdown.Item href="/player">
                    Against Random Person
                  </NavDropdown.Item>
                </NavDropdown>
              </Nav>
            </Navbar>
          </Col>
        </Row>
        <Row>
          <Col>
            <BrowserRouter>
              <Switch>
                <Route
                  path="/ai"
                  render={(props) => <Game opponent={"ai"} {...props} />}
                />
                <Route
                  path="/player"
                  render={(props) => <Game opponent={"player"} {...props} />}
                />
                <Route path="/" render={(props) => <div />} />
              </Switch>
            </BrowserRouter>
          </Col>
        </Row>
      </Container>
    );
  }
}

export default App;
