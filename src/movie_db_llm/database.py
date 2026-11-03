"""Database connection and session setup."""

from collections.abc import Generator
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from movie_db_llm.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@event.listens_for(engine, "connect")
def configure_sqlite_connection(
    database_connection: SQLiteConnection,
    _: ConnectionPoolEntry,
) -> None:
    """Enable foreign keys and Unicode case folding on each connection."""
    database_connection.execute("PRAGMA foreign_keys = ON")
    database_connection.create_function(
        "casefold", 1, str.casefold, deterministic=True
    )


def get_session() -> Generator[Session]:
    """Provide a database session for one request."""
    with SessionLocal() as session:
        yield session
