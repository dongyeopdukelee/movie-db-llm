"""Tests for catalog ORM models."""

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from movie_db_llm.models import Base, Movie, MovieGenre


def test_movie_release_year_is_optional() -> None:
    """New movie records may omit a release year."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    columns = inspect(engine).get_columns("movies")
    release_year = next(
        column for column in columns if column["name"] == "release_year"
    )

    assert release_year["nullable"] is True


def test_movie_genre_accepts_raw_source_labels() -> None:
    """Movie genres preserve non-canonical source labels."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        movie = Movie(
            title="Example Movie",
            synopsis="An example synopsis.",
            release_year=2026,
            genre_assignments=[MovieGenre(genre="Black-and-white")],
        )
        session.add(movie)
        session.commit()

        stored_genre = session.scalar(select(MovieGenre.genre))

    assert stored_genre == "Black-and-white"
