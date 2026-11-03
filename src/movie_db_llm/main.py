"""FastAPI application entry point."""

from typing import Annotated, Literal

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from movie_db_llm.database import get_session
from movie_db_llm.models import Movie
from movie_db_llm.ollama import get_intent_parser
from movie_db_llm.recommendations import (
    IntentParser,
    InvalidModelResponseError,
    ModelUnavailableError,
    MovieIntent,
    RecommendationRequest,
    UnsupportedRequestError,
    recommend_movies,
)

app = FastAPI(title="Movie DB LLM")


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    status: Literal["ok"]


class MovieListItem(BaseModel):
    """Lightweight movie data returned by the catalog list."""

    id: int
    title: str
    release_year: int | None
    genres: list[str]


class MovieListResponse(BaseModel):
    """Response returned by the movie-list endpoint."""

    items: list[MovieListItem]


class RecommendationResponse(MovieListResponse):
    """Grounded movie cards together with the interpreted search filters."""

    intent: MovieIntent


def movie_card(movie: Movie) -> MovieListItem:
    """Serialize a catalog movie without including its synopsis."""
    return MovieListItem(
        id=movie.id,
        title=movie.title,
        release_year=movie.release_year,
        genres=sorted(
            assignment.genre for assignment in movie.genre_assignments
        ),
    )


@app.get("/health")
def health_check() -> HealthResponse:
    """Report that the API is running."""
    return HealthResponse(status="ok")


@app.get("/movies")
def list_movies(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MovieListResponse:
    """Return one ordered page of movies."""
    movies = session.scalars(
        select(Movie)
        .options(selectinload(Movie.genre_assignments))
        .order_by(Movie.title, Movie.id)
        .limit(limit)
        .offset(offset)
    ).all()

    return MovieListResponse(items=[movie_card(movie) for movie in movies])


@app.post("/recommendations")
def get_recommendations(
    request: RecommendationRequest,
    session: Annotated[Session, Depends(get_session)],
    parser: Annotated[IntentParser, Depends(get_intent_parser)],
) -> RecommendationResponse:
    """Interpret a natural-language request and return up to ten matches."""
    try:
        intent, movies = recommend_movies(request.query, session, parser)
    except UnsupportedRequestError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Use genres, release years, and title keywords.",
                "unsupported_constraints": error.constraints,
            },
        ) from error
    except ModelUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except InvalidModelResponseError as error:
        raise HTTPException(
            status_code=502,
            detail="Local model returned invalid or incomplete intent.",
        ) from error

    return RecommendationResponse(
        intent=intent, items=[movie_card(movie) for movie in movies]
    )


def main() -> None:
    """Run the application server locally."""
    uvicorn.run(app, host="127.0.0.1", port=8000)
