"""SQLAlchemy ORM models for the movie catalog."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Movie(Base):
    """A movie available in the catalog."""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    synopsis: Mapped[str] = mapped_column(Text)
    release_year: Mapped[int]
    genre_assignments: Mapped[list[MovieGenre]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )


class MovieGenre(Base):
    """A raw source genre assigned to a movie."""

    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    )
    genre: Mapped[str] = mapped_column(Text, primary_key=True)
    movie: Mapped[Movie] = relationship(back_populates="genre_assignments")
