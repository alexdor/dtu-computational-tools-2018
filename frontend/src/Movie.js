import React, { memo } from 'react';

export const Movie = memo(({ title, year, page_id, index }) => (
  <a
    rel="noopener noreferrer"
    target="_blank"
    href={`https://en.wikipedia.org/?curid=${page_id}`}
    className="movie"
  >
    <p>{index}</p>
    <div className="movie_content">
      <p>{title}</p>
      <p>{year}</p>
    </div>
  </a>
));
