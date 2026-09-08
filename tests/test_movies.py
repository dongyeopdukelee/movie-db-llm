"""Tests for the movie-list endpoint."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from movie_db_llm.main import list_movies
from movie_db_llm.models import Base, Movie, MovieGenre


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
        session.add_all(
            [
                Movie(
                    title="Action Movie",
                    synopsis="An action movie.",
                    release_year=2020,
                    genre_assignments=[MovieGenre(genre="Action")],
                ),
                Movie(
                    title="Drama Movie",
                    synopsis="A drama movie.",
                    release_year=None,
                    genre_assignments=[MovieGenre(genre="Drama")],
                ),
            ]
        )
        session.commit()

    with test_session_factory() as session:
        response = list_movies(session)

    assert response.model_dump(mode="json") == {
        "items": [
            {
                "id": 1,
                "title": "Action Movie",
                "release_year": 2020,
                "genres": ["Action"],
            },
            {
                "id": 2,
                "title": "Drama Movie",
                "release_year": None,
                "genres": ["Drama"],
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


def test_list_movies_applies_limit_and_offset() -> None:
    """Movie pages follow the title and identifier ordering."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    with test_session_factory() as session:
        session.add_all(
            [
                Movie(title="Alpha", synopsis=".", release_year=2001),
                Movie(title="Bravo", synopsis=".", release_year=2002),
                Movie(title="Charlie", synopsis=".", release_year=2003),
            ]
        )
        session.commit()

    with test_session_factory() as session:
        first_page = list_movies(session, limit=2, offset=0)
        second_page = list_movies(session, limit=2, offset=2)
        empty_page = list_movies(session, limit=2, offset=3)

    assert [movie.title for movie in first_page.items] == ["Alpha", "Bravo"]
    assert [movie.title for movie in second_page.items] == ["Charlie"]
    assert empty_page.items == []
