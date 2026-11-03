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

For recommendations, install [Ollama for Linux](https://docs.ollama.com/linux)
inside WSL, then run it in another terminal with cloud inference disabled:

```bash
OLLAMA_NO_CLOUD=1 ollama serve
```

Download the selected local model once:

```bash
ollama pull qwen3.5:2b
```

If Ollama already runs as a service, configure `OLLAMA_NO_CLOUD=1` for that
service instead of starting a second server. Catalog browsing works without
Ollama. The model can run on CPU; no hosted API key is required.

For a project-local manual installation in `.tools/ollama` (as used in this
workspace), start the server with the same local model storage directory:

```bash
OLLAMA_MODELS="$PWD/.tools/ollama/models" OLLAMA_NO_CLOUD=1 \
  .tools/ollama/bin/ollama serve
```

Use `.tools/ollama/bin/ollama pull qwen3.5:2b` for the download command in
that setup. Runtime files and downloaded weights are ignored by Git.

The API is available at `http://127.0.0.1:8000`.

## API

- `GET /health` reports whether the API is running.
- `GET /movies` returns an ordered page of imported movie cards. It accepts
  `limit` (default 20, maximum 100) and `offset` (default 0) query parameters.
- `POST /recommendations` interprets a natural-language request using local
  Qwen3.5 2B and returns up to 10 matching movie cards plus the parsed intent.
- `GET /docs` opens FastAPI's interactive API documentation.

The API does not create or modify its schema at startup. Apply migrations before
starting it.

`import-cmu` reads the CMU source files in this repository and requires an
empty movie catalog. It validates all source files before writing the catalog.

Example recommendation request:

```bash
curl http://127.0.0.1:8000/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"query":"Comedies from the 1990s with love in the title"}'
```

The response uses an `items` envelope with lightweight movie cards and an
`intent` object containing `genres`, `year_min`, `year_max`,
`year_min_inclusive`, `year_max_inclusive`, `title_keywords`, and
`unsupported_constraints`. All requested genres and title keywords must match.
Title matching uses literal, case-insensitive substrings. Exact years, decades,
since, and until use inclusive year bounds; before and after use exclusive
bounds. The model copies the year and the database applies the comparison,
avoiding year arithmetic in model output. Undated movies only match when no
year filter is requested.
Results are ordered by title and identifier, with no relevance ranking yet.
No matching movies returns an empty `items` list without relaxing filters.

This step supports genres, release years, and title keywords. Requests for
plot subjects (such as dogs), mood, actors, exclusions, or OR conditions
return HTTP 422 rather than silently dropping those constraints. Empty or
oversized request text also returns 422. Model parsing is probabilistic:
schema validation prevents invalid queries but cannot guarantee that every
request is interpreted correctly. Semantic synopsis search comes next.

HTTP 503 means Ollama could not complete inference (including a missing model
or timeout); HTTP 502 means the model returned invalid or incomplete intent.
The API never executes model-generated SQL.

Local inference configuration:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama service URL |
| `OLLAMA_MODEL` | `qwen3.5:2b` | Locally downloaded model tag |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | HTTP inference timeout in seconds |

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
docker compose up -d ollama
docker compose exec ollama ollama pull qwen3.5:2b
docker compose up
```

Open `http://127.0.0.1:8000/docs` or call:

```bash
curl http://127.0.0.1:8000/health
curl 'http://127.0.0.1:8000/movies?limit=20&offset=0'
```

Docker Compose stores the SQLite database in the `movie-db-data` named volume.
It runs Ollama on CPU, disables Ollama cloud inference, and stores downloaded
models in `ollama-models`. The inference port stays on the Compose network.
Stop the service with `Ctrl+C`, then remove the containers with:

```bash
docker compose down
```
