import './App.css';
import 'react-s-alert/dist/s-alert-css-effects/slide.css';
import 'react-s-alert/dist/s-alert-default.css';

import Button from 'muicss/lib/react/button';
import Col from 'muicss/lib/react/col';
import Container from 'muicss/lib/react/container';
import Form from 'muicss/lib/react/form';
import Input from 'muicss/lib/react/input';
import Row from 'muicss/lib/react/row';
import React, { PureComponent } from 'react';
import Alert from 'react-s-alert';

import { showError } from './helpers/alerts';
import { parseJson } from './helpers/helpers';
import { Movie } from './Movie';
import { Spinner } from './Spinner';

class App extends PureComponent {
  state = {
    loading: false,
    data: [],
    text: undefined
  };

  componentDidCatch = e => {
    this.setState({ loading: false });
    showError("There was an error");
    console.error(e);
  };

  handleChange = e => {
    this.setState({ text: e.target.value });
  };

  getResults = e => {
    e.preventDefault();
    const { text, loading } = this.state;
    if (!text || loading) {
      return;
    }
    const tmp = text.split(" ");
    if (tmp.length > 3) {
      showError("Please enter up to 3 tags");
      return;
    }
    this.setState({ loading: true });

    fetch(
      `https://whichflick-api.swaco.io/api/v1/detailed_movies/?words=${tmp.join(
        ","
      )}`
    )
      .then(async response => {
        if (!response.ok) {
          showError("There was an error with your request");
          this.setState({ loading: false });
        } else {
          this.setState({
            data: parseJson(await response.text()).results,
            loading: false
          });
        }
      })
      .catch(error => {
        console.error(error);
        showError("There was an error with your request");
        this.setState({ loading: false });
      });
  };

  render() {
    const { loading, text, data } = this.state;
    return (
      <div className="App">
        <Container>
          <h1>Which Flick</h1>
          <Form onSubmit={this.getResults}>
            <Row className="form-row">
              <Col md={10}>
                <Input
                  type="text"
                  id="input"
                  placeholder="Enter 3 keywords and we'll get you a movie : )"
                  defaultValue={text}
                  onChange={this.handleChange}
                />
              </Col>
              <Col md={2}>
                <Button
                  color="primary"
                  variant="raised"
                  type="submit"
                  disabled={loading}
                >
                  Search
                </Button>
              </Col>
            </Row>
          </Form>
          {loading ? (
            <Spinner />
          ) : (
            <Row>
              {data &&
                data.map((movie, index) => (
                  <Col key={movie.id}>
                    <Movie
                      index={index + 1}
                      title={movie.title}
                      year={movie.year}
                      page_id={movie.page_id}
                    />
                  </Col>
                ))}
            </Row>
          )}

          <Alert stack={{ limit: 3 }} />
        </Container>
      </div>
    );
  }
}

export default App;
