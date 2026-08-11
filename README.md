# Movie DB LLM

A small FastAPI movie-catalog API built as a system-design learning project.

## Local development

Install the locked dependencies:

```bash
uv sync
```

Run the API with automatic reload:

```bash
uv run uvicorn movie_db_llm.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

## API

- `GET /health` reports whether the API is running.
- `GET /movies` returns the locally seeded movie catalog.
- `GET /docs` opens FastAPI's interactive API documentation.

On its first startup, the application creates `movie_db.sqlite3` and seeds the
initial catalog. Later startups do not duplicate that data.

## Tests and checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

## Docker Compose

Build and start the API:

```bash
docker compose up --build
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
