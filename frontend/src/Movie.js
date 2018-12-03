import Panel from 'muicss/lib/react/panel';
import React, { memo } from 'react';

const goTo = link => e => {
  e.stopPropagation();
  const a = document.createElement("a");
  a.href = link;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.click();
};

export const Movie = memo(({ title, year, page_id, index }) => {
  const link = `https://en.wikipedia.org/?curid=${page_id}`;

  return (
    <Panel className="movie-panel" onClick={goTo(link)}>
      <div className="movie mui--text-dark-secondary">
        <h3 className="mui--text-display1">{index}</h3>
        <div className="movie_content">
          <span className="mui--text-title">{title}</span>
          <span className="mui--text-caption">{year}</span>
        </div>
        <div className="right-parent">
          <span className="right" />
        </div>
      </div>
    </Panel>
  );
});
