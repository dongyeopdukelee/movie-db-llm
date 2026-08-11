"""Initial local catalog data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from movie_db_llm.genres import Genre
from movie_db_llm.models import Movie, MovieGenre


def seed_catalog(session: Session) -> None:
    """Add the initial movies once, without duplicating existing data."""
    existing_movie = session.scalar(select(Movie.id).limit(1))
    if existing_movie is not None:
        return

    session.add_all(
        [
            Movie(
                title="John Wick",
                synopsis=(
                    "A retired assassin returns to the criminal underworld "
                    "after a gang kills the dog left to him by his wife."
                ),
                release_year=2014,
                genre_assignments=[
                    MovieGenre(genre=Genre.ACTION),
                    MovieGenre(genre=Genre.THRILLER),
                ],
            ),
            Movie(
                title="The Thing",
                synopsis=(
                    "Researchers at an Antarctic outpost confront a "
                    "shape-shifting organism that imitates its victims."
                ),
                release_year=1982,
                genre_assignments=[
                    MovieGenre(genre=Genre.HORROR),
                    MovieGenre(genre=Genre.THRILLER),
                ],
            ),
            Movie(
                title="Spirited Away",
                synopsis=(
                    "A young girl enters a spirit world and works to free "
                    "her parents while finding a way home."
                ),
                release_year=2001,
                genre_assignments=[
                    MovieGenre(genre=Genre.ADVENTURE),
                    MovieGenre(genre=Genre.ANIMATION),
                    MovieGenre(genre=Genre.FANTASY),
                ],
            ),
            Movie(
                title="When Harry Met Sally...",
                synopsis=(
                    "Two longtime friends navigate changing relationships "
                    "and question whether friendship can become love."
                ),
                release_year=1989,
                genre_assignments=[
                    MovieGenre(genre=Genre.COMEDY),
                    MovieGenre(genre=Genre.ROMANCE),
                ],
            ),
            Movie(
                title="Free Solo",
                synopsis=(
                    "A climber prepares to ascend Yosemite's El Capitan "
                    "without ropes."
                ),
                release_year=2018,
                genre_assignments=[MovieGenre(genre=Genre.DOCUMENTARY)],
            ),
        ]
    )
    session.commit()
