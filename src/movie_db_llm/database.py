"""Database setup and initialization."""

from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from movie_db_llm.models import Base
from movie_db_llm.seed import seed_catalog

DATABASE_URL = "sqlite:///./movie_db.sqlite3"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(
    database_connection: SQLiteConnection,
    _: ConnectionPoolEntry,
) -> None:
    """Enable SQLite foreign-key enforcement for each new connection."""
    database_connection.execute("PRAGMA foreign_keys = ON")


def initialize_database() -> None:
    """Create the schema and populate the initial catalog."""
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        seed_catalog(session)
