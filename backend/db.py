from sqlalchemy import JSON, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///parser.sqlite3", echo=True)
Base = declarative_base()


Session = sessionmaker(bind=engine)


class MovieModel(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False, index=True)
    page_id = Column(Integer, unique=True, nullable=False, index=True)
    plot = Column(String)
    response = Column(String)
    tokenized_plot = Column(String)
    year = Column(Integer, index=True)
    budget = Column(String, index=True)

    def __repr__(self):
        return f"<MovieModel(title={self.title}, pageID={self.page_id})>"


Base.metadata.create_all(engine)
