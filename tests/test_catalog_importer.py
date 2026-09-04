"""Tests for writing parsed catalog records to the database."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from movie_db_llm.catalog_importer import (
    CatalogNotEmptyError,
    ImportResult,
    import_catalog,
)
from movie_db_llm.cmu_parser import CatalogMovie
from movie_db_llm.models import Base, Movie, MovieGenre


def test_import_catalog_writes_movies_and_genres() -> None:
    """A validated catalog is written with optional years and empty genres."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    catalog_movies = [
        CatalogMovie(
            title="Dated Movie",
            synopsis="A dated synopsis.",
            release_year=2001,
            genres=("Drama", "Mystery"),
        ),
        CatalogMovie(
            title="Undated Movie",
            synopsis="An undated synopsis.",
            release_year=None,
            genres=(),
        ),
    ]

    with Session(engine) as session:
        result = import_catalog(session, catalog_movies)
        movies = session.scalars(select(Movie).order_by(Movie.title)).all()
        genres = session.scalars(
            select(MovieGenre.genre).order_by(MovieGenre.genre)
        ).all()

    assert result == ImportResult(movie_count=2, genre_assignment_count=2)
    assert [movie.title for movie in movies] == [
        "Dated Movie",
        "Undated Movie",
    ]
    assert movies[1].release_year is None
    assert genres == ["Drama", "Mystery"]


def test_import_catalog_rejects_a_nonempty_catalog() -> None:
    """An import does not mix a new catalog with existing movie rows."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            Movie(
                title="Existing Movie",
                synopsis="An existing synopsis.",
                release_year=2026,
            )
        )
        session.commit()

        with pytest.raises(CatalogNotEmptyError):
            import_catalog(session, [])

        assert session.scalar(select(Movie.title)) == "Existing Movie"
