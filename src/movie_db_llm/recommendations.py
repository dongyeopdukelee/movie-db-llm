"""Constrained request intent and application-owned catalog retrieval."""

from collections.abc import Sequence
from typing import Annotated, Protocol, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session, load_only, selectinload

from movie_db_llm.models import Movie, MovieGenre

RECOMMENDATION_LIMIT = 10
IntentText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Year = Annotated[int, Field(ge=1, le=9999)]


class RecommendationRequest(BaseModel):
    """A bounded natural-language request for catalog matches."""

    model_config = ConfigDict(extra="forbid", strict=True)

    query: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=1000
        ),
    ]


class MovieIntent(BaseModel):
    """The complete allowlist of fields an LLM may return."""

    model_config = ConfigDict(extra="forbid", strict=True)

    genres: Annotated[list[IntentText], Field(max_length=10)]
    year_min: Year | None
    year_max: Year | None
    year_min_inclusive: bool
    year_max_inclusive: bool
    title_keywords: Annotated[list[IntentText], Field(max_length=10)]
    unsupported_constraints: Annotated[list[IntentText], Field(max_length=10)]

    @model_validator(mode="after")
    def validate_year_range(self) -> Self:
        """Reject contradictory year bounds rather than silently fixing them."""
        if (
            self.year_min is not None
            and self.year_max is not None
            and self.year_min > self.year_max
        ):
            raise ValueError("year_min must not exceed year_max")
        return self


class ModelUnavailableError(Exception):
    """The local inference service could not complete the request."""


class InvalidModelResponseError(Exception):
    """The model response cannot be trusted as a catalog query."""


class UnsupportedRequestError(Exception):
    """The request needs constraints this retrieval step cannot apply."""

    def __init__(self, constraints: list[str]) -> None:
        self.constraints = constraints
        super().__init__("The request contains unsupported constraints.")


class IntentParser(Protocol):
    """Boundary between natural-language parsing and catalog retrieval."""

    def parse(self, query: str, genres: list[str]) -> MovieIntent:
        """Extract intent using the actual catalog's genre vocabulary."""
        ...


def recommend_movies(
    query: str, session: Session, parser: IntentParser
) -> tuple[MovieIntent, Sequence[Movie]]:
    """Validate intent and combine filters using parameterized ORM queries."""
    genres = list(
        session.scalars(
            select(MovieGenre.genre).distinct().order_by(MovieGenre.genre)
        )
    )
    intent = parser.parse(query, genres)
    if intent.unsupported_constraints:
        raise UnsupportedRequestError(intent.unsupported_constraints)

    if not (
        intent.genres
        or intent.year_min is not None
        or intent.year_max is not None
        or intent.title_keywords
    ):
        raise UnsupportedRequestError(
            ["Include a genre, release year, or title keyword."]
        )

    if any(genre not in genres for genre in intent.genres):
        raise InvalidModelResponseError("Model returned an unknown genre.")

    statement = select(Movie).options(
        load_only(Movie.id, Movie.title, Movie.release_year),
        selectinload(Movie.genre_assignments),
    )
    # All requested genres and title keywords must match. EXISTS avoids
    # duplicate cards when a movie has several matching genre assignments.
    for genre in intent.genres:
        statement = statement.where(
            Movie.genre_assignments.any(MovieGenre.genre == genre)
        )
    if intent.year_min is not None:
        statement = statement.where(
            Movie.release_year >= intent.year_min
            if intent.year_min_inclusive
            else Movie.release_year > intent.year_min
        )
    if intent.year_max is not None:
        statement = statement.where(
            Movie.release_year <= intent.year_max
            if intent.year_max_inclusive
            else Movie.release_year < intent.year_max
        )
    for keyword in intent.title_keywords:
        statement = statement.where(
            func.casefold(Movie.title).contains(
                keyword.casefold(), autoescape=True
            )
        )

    movies = session.scalars(
        statement.order_by(Movie.title, Movie.id).limit(RECOMMENDATION_LIMIT)
    ).all()
    return intent, movies
