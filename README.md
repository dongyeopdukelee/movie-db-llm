# Movie DB LLM

A small FastAPI movie-catalog API built as a system-design learning project.

See the [product roadmap](docs/roadmap.md) for the planned path from a catalog
API to grounded natural-language movie recommendations.

## Local development

Install the locked dependencies:

```bash
uv sync
```

Prepare the local database:

```bash
uv run alembic upgrade head
uv run movie-db-llm import-cmu
```

Run the API with automatic reload:

```bash
uv run uvicorn movie_db_llm.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

## API

- `GET /health` reports whether the API is running.
- `GET /movies` returns the imported movie catalog.
- `GET /docs` opens FastAPI's interactive API documentation.

The API does not create or modify its schema at startup. Apply migrations before
starting it.

`import-cmu` reads the CMU source files in this repository and requires an
empty movie catalog. It validates all source files before writing the catalog.

## Tests and checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

## Docker Compose

For a new Docker Compose database volume, build the image, apply migrations,
then start the API:

```bash
docker compose build
docker compose run --rm api alembic upgrade head
docker compose run --rm api movie-db-llm import-cmu
docker compose up
```

Open `http://127.0.0.1:8000/docs` or call:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/movies
```

Docker Compose stores the SQLite database in the `movie-db-data` named volume.
Stop the service with `Ctrl+C`, then remove the containers with:

```bash
docker compose down
```
