"""Command-line interface for local project operations."""

import argparse

from movie_db_llm.database import SessionLocal
from movie_db_llm.main import main as run_server
from movie_db_llm.seed import seed_catalog


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(prog="movie-db-llm")
    subcommands = parser.add_subparsers(dest="command")
    subcommands.add_parser(
        "seed-demo",
        help="Seed the development database with the demo catalog.",
    )
    return parser


def seed_demo() -> None:
    """Seed the configured database with the demo catalog."""
    with SessionLocal() as session:
        seed_catalog(session)


def main() -> None:
    """Run the requested project command."""
    arguments = build_parser().parse_args()
    if arguments.command == "seed-demo":
        seed_demo()
        return

    run_server()
