"""Tests for initial catalog seeding."""

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from movie_db_llm.models import Base, Movie, MovieGenre
from movie_db_llm.seed import seed_catalog


def test_movie_release_year_is_optional() -> None:
    """New movie records may omit a release year."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    columns = inspect(engine).get_columns("movies")
    release_year = next(
        column for column in columns if column["name"] == "release_year"
    )

    assert release_year["nullable"] is True


def test_seed_catalog_adds_each_movie_once() -> None:
    """The seed catalog creates its movies and remains idempotent."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_catalog(session)
        seed_catalog(session)

        movies = session.scalars(select(Movie).order_by(Movie.title)).all()

        assert len(movies) == 5
        john_wick = next(
            movie for movie in movies if movie.title == "John Wick"
        )
        assert {
            assignment.genre for assignment in john_wick.genre_assignments
        } == {
            "action",
            "thriller",
        }


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
