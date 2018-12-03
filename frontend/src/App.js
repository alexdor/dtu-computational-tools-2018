import './App.css';
import 'react-s-alert/dist/s-alert-css-effects/slide.css';
import 'react-s-alert/dist/s-alert-default.css';

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
      `http://localhost:8080/api/v1/detailed_movies/?words=${tmp.join(",")}`
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
        <h1>Which Flick</h1>
        <form onSubmit={this.getResults}>
          <fieldset>
            <input
              id="input"
              placeholder="Enter 3 keywords and we'll get you a movie : )"
              defaultValue={text}
              onChange={this.handleChange}
            />
            <button className="button button-outline" type="submit">
              Search
            </button>
          </fieldset>
        </form>
        {loading ? (
          <Spinner />
        ) : (
          <div>
            {data &&
              data.map((movie, index) => (
                <Movie
                  index={index + 1}
                  title={movie.title}
                  year={movie.year}
                  page_id={movie.page_id}
                />
              ))}
          </div>
        )}

        <Alert stack={{ limit: 3 }} />
      </div>
    );
  }
}

export default App;
