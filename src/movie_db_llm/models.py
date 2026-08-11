"""SQLAlchemy ORM models for the movie catalog."""

from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from movie_db_llm.genres import Genre


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Movie(Base):
    """A movie available in the catalog."""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    synopsis: Mapped[str] = mapped_column(Text)
    release_year: Mapped[int | None]
    genre_assignments: Mapped[list[MovieGenre]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )


class MovieGenre(Base):
    """A predefined genre assigned to a movie."""

    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    )
    genre: Mapped[Genre] = mapped_column(
        Enum(Genre, native_enum=False, create_constraint=True),
        primary_key=True,
    )
    movie: Mapped[Movie] = relationship(back_populates="genre_assignments")
