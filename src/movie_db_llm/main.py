"""FastAPI application entry point."""

from typing import Annotated, Literal

import uvicorn
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from movie_db_llm.database import get_session
from movie_db_llm.genres import Genre
from movie_db_llm.models import Movie

app = FastAPI(title="Movie DB LLM")


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    status: Literal["ok"]


class MovieListItem(BaseModel):
    """Lightweight movie data returned by the catalog list."""

    id: int
    title: str
    release_year: int
    genres: list[Genre]


class MovieListResponse(BaseModel):
    """Response returned by the movie-list endpoint."""

    items: list[MovieListItem]


@app.get("/health")
def health_check() -> HealthResponse:
    """Report that the API is running."""
    return HealthResponse(status="ok")


@app.get("/movies")
def list_movies(
    session: Annotated[Session, Depends(get_session)],
) -> MovieListResponse:
    """Return movies ordered by title and identifier."""
    movies = session.scalars(
        select(Movie)
        .options(selectinload(Movie.genre_assignments))
        .order_by(Movie.title, Movie.id)
    ).all()

    return MovieListResponse(
        items=[
            MovieListItem(
                id=movie.id,
                title=movie.title,
                release_year=movie.release_year,
                genres=sorted(
                    assignment.genre for assignment in movie.genre_assignments
                ),
            )
            for movie in movies
        ]
    )


def main() -> None:
    """Run the application server locally."""
    uvicorn.run(app, host="127.0.0.1", port=8000)
