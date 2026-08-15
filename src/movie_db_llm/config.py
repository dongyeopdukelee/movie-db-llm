"""Application configuration shared by runtime and migration tooling."""

from os import environ

DATABASE_URL = environ.get("DATABASE_URL", "sqlite:///./movie_db.sqlite3")
