"""Parse CMU Movie Summary Corpus files into catalog movie records."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

METADATA_COLUMN_COUNT = 9
RELEASE_YEAR_PATTERN = re.compile(r"^(\d{4})")


@dataclass(frozen=True)
class CatalogMovie:
    """A validated movie record ready for a later database import."""

    title: str
    synopsis: str
    release_year: int | None
    genres: tuple[str, ...]


@dataclass(frozen=True)
class _MetadataMovie:
    """Movie fields supplied by the metadata file before its summary is joined."""

    title: str
    release_year: int | None
    genres: tuple[str, ...]


class CmuParseError(ValueError):
    """Raised when a CMU source file is structurally invalid."""


def parse_catalog(
    metadata_path: Path,
    plot_summaries_path: Path,
) -> list[CatalogMovie]:
    """Join CMU metadata and plot summaries into validated movie records."""
    summaries = _read_summaries(plot_summaries_path)
    metadata = _read_metadata(metadata_path)
    movies: list[CatalogMovie] = []

    for movie_id, metadata_movie in metadata:
        synopsis = summaries.get(movie_id)
        if synopsis is None or not synopsis.strip():
            continue

        movies.append(
            CatalogMovie(
                title=metadata_movie.title,
                synopsis=synopsis.strip(),
                release_year=metadata_movie.release_year,
                genres=metadata_movie.genres,
            )
        )

    return movies


def _read_summaries(path: Path) -> dict[str, str]:
    """Read plot summaries keyed by their Wikipedia movie ID."""
    summaries: dict[str, str] = {}

    with path.open(encoding="utf-8") as source_file:
        for line_number, line in enumerate(source_file, start=1):
            row = line.rstrip("\n")
            if "\t" not in row:
                raise _source_error(
                    path,
                    line_number,
                    "expected an ID and a summary",
                )

            movie_id, synopsis = row.split("\t", maxsplit=1)
            if not movie_id:
                raise _source_error(path, line_number, "missing movie ID")
            if movie_id in summaries:
                raise _source_error(
                    path,
                    line_number,
                    f"duplicate movie ID {movie_id!r}",
                )

            summaries[movie_id] = synopsis

    return summaries


def _read_metadata(path: Path) -> list[tuple[str, _MetadataMovie]]:
    """Read and validate CMU metadata rows in source order."""
    metadata: list[tuple[str, _MetadataMovie]] = []
    seen_movie_ids: set[str] = set()

    with path.open(encoding="utf-8") as source_file:
        for line_number, line in enumerate(source_file, start=1):
            row = line.rstrip("\n").split("\t")
            if len(row) != METADATA_COLUMN_COUNT:
                raise _source_error(
                    path,
                    line_number,
                    f"expected {METADATA_COLUMN_COUNT} columns",
                )

            movie_id, _, raw_title, raw_date, *_, raw_genres = row
            if not movie_id:
                raise _source_error(path, line_number, "missing movie ID")
            if movie_id in seen_movie_ids:
                raise _source_error(
                    path,
                    line_number,
                    f"duplicate movie ID {movie_id!r}",
                )
            seen_movie_ids.add(movie_id)

            title = raw_title.strip()
            if not title:
                raise _source_error(
                    path,
                    line_number,
                    "missing movie title",
                )

            metadata.append(
                (
                    movie_id,
                    _MetadataMovie(
                        title=title,
                        release_year=_parse_release_year(raw_date),
                        genres=_parse_genres(
                            path,
                            line_number,
                            raw_genres,
                        ),
                    ),
                )
            )

    return metadata


def _parse_release_year(raw_date: str) -> int | None:
    """Extract a leading four-digit year when the source supplies one."""
    match = RELEASE_YEAR_PATTERN.match(raw_date.strip())
    return int(match.group(1)) if match else None


def _parse_genres(
    path: Path,
    line_number: int,
    raw_genres: str,
) -> tuple[str, ...]:
    """Return trimmed, exact-deduplicated genre labels from a JSON mapping."""
    try:
        parsed_genres: object = json.loads(raw_genres)
    except json.JSONDecodeError as error:
        raise _source_error(
            path,
            line_number,
            "malformed genre mapping",
        ) from error

    if not isinstance(parsed_genres, dict):
        raise _source_error(
            path, line_number, "genre mapping must be an object"
        )

    genre_mapping = cast(dict[object, object], parsed_genres)
    genres: list[str] = []
    for genre in genre_mapping.values():
        if not isinstance(genre, str):
            raise _source_error(
                path,
                line_number,
                "genre label must be a string",
            )

        label = genre.strip()
        if label and label not in genres:
            genres.append(label)

    return tuple(genres)


def _source_error(path: Path, line_number: int, message: str) -> CmuParseError:
    """Build a source-specific parse error with a useful location."""
    return CmuParseError(f"{path}:{line_number}: {message}")
