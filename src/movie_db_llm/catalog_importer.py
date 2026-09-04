"""Write validated catalog records to the database."""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from movie_db_llm.cmu_parser import CatalogMovie
from movie_db_llm.models import Movie, MovieGenre


@dataclass(frozen=True)
class ImportResult:
    """Counts produced by a successful catalog import."""

    movie_count: int
    genre_assignment_count: int


class CatalogNotEmptyError(RuntimeError):
    """Raised when an import would mix with an existing catalog."""


def import_catalog(
    session: Session,
    catalog_movies: Sequence[CatalogMovie],
) -> ImportResult:
    """Write a fully parsed catalog to an otherwise empty database."""
    if session.scalar(select(Movie.id).limit(1)) is not None:
        raise CatalogNotEmptyError(
            "The movie catalog must be empty to import."
        )

    movie_count = len(catalog_movies)
    genre_assignment_count = sum(
        len(catalog_movie.genres) for catalog_movie in catalog_movies
    )
    session.add_all(
        [
            Movie(
                title=catalog_movie.title,
                synopsis=catalog_movie.synopsis,
                release_year=catalog_movie.release_year,
                genre_assignments=[
                    MovieGenre(genre=genre) for genre in catalog_movie.genres
                ],
            )
            for catalog_movie in catalog_movies
        ]
    )

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise

    return ImportResult(
        movie_count=movie_count,
        genre_assignment_count=genre_assignment_count,
    )
