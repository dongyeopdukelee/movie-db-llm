"""Tests for the movie-list endpoint."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from movie_db_llm.main import list_movies
from movie_db_llm.models import Base, Movie, MovieGenre
from movie_db_llm.seed import seed_catalog


def test_list_movies_returns_ordered_movie_cards() -> None:
    """The endpoint returns lightweight, ordered movies with their genres."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    with test_session_factory() as session:
        seed_catalog(session)

    with test_session_factory() as session:
        response = list_movies(session)

    assert response.model_dump(mode="json") == {
        "items": [
            {
                "id": 5,
                "title": "Free Solo",
                "release_year": 2018,
                "genres": ["documentary"],
            },
            {
                "id": 1,
                "title": "John Wick",
                "release_year": 2014,
                "genres": ["action", "thriller"],
            },
            {
                "id": 3,
                "title": "Spirited Away",
                "release_year": 2001,
                "genres": ["adventure", "animation", "fantasy"],
            },
            {
                "id": 2,
                "title": "The Thing",
                "release_year": 1982,
                "genres": ["horror", "thriller"],
            },
            {
                "id": 4,
                "title": "When Harry Met Sally...",
                "release_year": 1989,
                "genres": ["comedy", "romance"],
            },
        ]
    }


def test_list_movies_allows_a_missing_release_year() -> None:
    """Movie cards preserve an unavailable release year as null."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    with test_session_factory() as session:
        session.add(
            Movie(
                title="Undated Movie",
                synopsis="A movie with an unavailable release year.",
                release_year=None,
                genre_assignments=[MovieGenre(genre="Drama")],
            )
        )
        session.commit()

    with test_session_factory() as session:
        response = list_movies(session)

    assert response.model_dump(mode="json") == {
        "items": [
            {
                "id": 1,
                "title": "Undated Movie",
                "release_year": None,
                "genres": ["Drama"],
            }
        ]
    }
