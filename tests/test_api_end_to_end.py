"""End-to-end tests for the HTTP movie-catalog API."""

import json
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from os import environ
from pathlib import Path
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from movie_db_llm.models import Movie, MovieGenre

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _database_url(database_path: Path) -> str:
    """Return the SQLite URL for a temporary database file."""
    return f"sqlite:///{database_path}"


def _apply_migrations(database_url: str) -> None:
    """Create the test schema through the same migration path as production."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False,
        cwd=PROJECT_ROOT,
        env={**environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def _seed_catalog(database_url: str) -> None:
    """Add a small deterministic catalog for an HTTP user journey."""
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            session.add_all(
                [
                    Movie(
                        title="Alpha",
                        synopsis="A first test movie.",
                        release_year=2001,
                        genre_assignments=[
                            MovieGenre(genre="Comedy"),
                            MovieGenre(genre="Adventure"),
                        ],
                    ),
                    Movie(
                        title="Bravo",
                        synopsis="A second test movie.",
                        release_year=None,
                    ),
                ]
            )
            session.commit()
    finally:
        engine.dispose()


def _available_port() -> int:
    """Reserve a currently unused loopback TCP port number."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return cast(int, listener.getsockname()[1])


def _get_json(url: str) -> tuple[int, object]:
    """Make a GET request and decode either a success or error JSON response."""
    try:
        with urlopen(url, timeout=1) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def _wait_until_healthy(base_url: str, process: subprocess.Popen[str]) -> None:
    """Wait for Uvicorn to accept HTTP requests or report its startup failure."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            status, body = _get_json(f"{base_url}/health")
        except TimeoutError, URLError:
            status, body = 0, None

        if status == 200 and body == {"status": "ok"}:
            return

        if process.poll() is not None:
            stderr = (
                process.stderr.read() if process.stderr is not None else ""
            )
            raise RuntimeError(f"Uvicorn exited during startup:\n{stderr}")

        time.sleep(0.05)

    raise TimeoutError("Uvicorn did not become healthy within five seconds")


@pytest.fixture
def api_url(tmp_path: Path) -> Generator[str]:
    """Run the real API against an isolated migrated SQLite database."""
    database_url = _database_url(tmp_path / "catalog.sqlite3")
    _apply_migrations(database_url)
    _seed_catalog(database_url)

    port = _available_port()
    base_url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "movie_db_llm.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=PROJECT_ROOT,
        env={**environ, "DATABASE_URL": database_url},
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        _wait_until_healthy(base_url, process)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_catalog_user_journey_over_http(api_url: str) -> None:
    """A client can check health and browse consecutive catalog pages."""
    health_status, health_body = _get_json(f"{api_url}/health")
    first_status, first_page = _get_json(f"{api_url}/movies?limit=1")
    second_status, second_page = _get_json(
        f"{api_url}/movies?limit=1&offset=1"
    )

    assert health_status == 200
    assert health_body == {"status": "ok"}
    assert first_status == 200
    assert first_page == {
        "items": [
            {
                "id": 1,
                "title": "Alpha",
                "release_year": 2001,
                "genres": ["Adventure", "Comedy"],
            }
        ]
    }
    assert second_status == 200
    assert second_page == {
        "items": [
            {
                "id": 2,
                "title": "Bravo",
                "release_year": None,
                "genres": [],
            }
        ]
    }


def test_catalog_rejects_invalid_pagination_over_http(api_url: str) -> None:
    """A client receives a validation response for an invalid page size."""
    status, body = _get_json(f"{api_url}/movies?limit=0")

    assert status == 422
    assert isinstance(body, dict)
    error_body = cast(dict[str, object], body)
    detail = error_body["detail"]
    assert isinstance(detail, list)
    first_error = cast(dict[str, object], detail[0])
    assert first_error["loc"] == ["query", "limit"]
