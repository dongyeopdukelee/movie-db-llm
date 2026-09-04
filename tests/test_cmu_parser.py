"""Tests for parsing CMU Movie Summary Corpus source files."""

from pathlib import Path

import pytest

from movie_db_llm.cmu_parser import CatalogMovie, CmuParseError, parse_catalog


def _write_sources(
    tmp_path: Path,
    metadata: str,
    summaries: str,
) -> tuple[Path, Path]:
    """Create a small CMU-shaped metadata and summary-file pair."""
    metadata_path = tmp_path / "movie.metadata.tsv"
    summaries_path = tmp_path / "plot_summaries.txt"
    metadata_path.write_text(metadata, encoding="utf-8")
    summaries_path.write_text(summaries, encoding="utf-8")
    return metadata_path, summaries_path


def test_parse_catalog_joins_movies_with_summaries(tmp_path: Path) -> None:
    """Joined records keep optional years and may have no genres."""
    metadata_path, summaries_path = _write_sources(
        tmp_path,
        "1\t/m/one\t Example One \t2001-01-02\t\t\t{}\t{}\t"
        '{"/m/drama": " Drama ", "/m/drama-duplicate": "Drama"}\n'
        "2\t/m/two\tExample Two\t\t\t\t{}\t{}\t{}\n"
        "3\t/m/three\tNo Summary\t1999\t\t\t{}\t{}\t{}\n",
        "1\t First summary.\tAdditional detail. \n2\tSecond summary.\n"
        "3\t   \n",
    )

    movies = parse_catalog(metadata_path, summaries_path)

    assert movies == [
        CatalogMovie(
            title="Example One",
            synopsis="First summary.\tAdditional detail.",
            release_year=2001,
            genres=("Drama",),
        ),
        CatalogMovie(
            title="Example Two",
            synopsis="Second summary.",
            release_year=None,
            genres=(),
        ),
    ]


@pytest.mark.parametrize(
    ("metadata", "summaries", "expected_error"),
    [
        (
            "1\ttoo\tfew\tcolumns\n",
            "1\tSummary.\n",
            "expected 9 columns",
        ),
        (
            "1\t/m/one\tExample\t2001\t\t\t{}\t{}\t{bad json}\n",
            "1\tSummary.\n",
            "malformed genre mapping",
        ),
        (
            "1\t/m/one\tExample\t2001\t\t\t{}\t{}\t{}\n",
            "1\tFirst summary.\n1\tSecond summary.\n",
            "duplicate movie ID '1'",
        ),
        (
            "1\t/m/one\tExample\t2001\t\t\t{}\t{}\t{}\n",
            "Summary without an ID.\n",
            "expected an ID and a summary",
        ),
    ],
)
def test_parse_catalog_rejects_malformed_source_files(
    tmp_path: Path,
    metadata: str,
    summaries: str,
    expected_error: str,
) -> None:
    """Structural source errors reject the entire parse."""
    metadata_path, summaries_path = _write_sources(
        tmp_path,
        metadata,
        summaries,
    )

    with pytest.raises(CmuParseError, match=expected_error):
        parse_catalog(metadata_path, summaries_path)
