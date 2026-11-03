# Project decisions

This is the living record of high-level decisions for Movie DB LLM. Update it
when a decision is made, changed, or removed.

## Product scope

- The initial product is an API-first movie catalog for browsing and title search.
- The first catalog will be imported from the CMU Movie Summary Corpus.
- Movies and genres will use a normalized `movies` / `movie_genres`
  association-table design; a separate genre lookup table is not needed yet.
- Imported genre values are stored as trimmed raw source labels without
  canonicalization.
- Catalog-list responses will use an `items` envelope and return lightweight
  movie cards; full synopses belong to a future movie-detail endpoint.
- Catalog movie release years are optional.
- Catalog ingestion will use downloadable public dataset snapshots; live
  provider APIs and freshness automation are deferred.
- The initial importer will parse the CMU Movie Summary Corpus source files
  directly; generic multi-source ingestion is deferred.
- Initial catalog imports will validate the complete dataset before writing;
  malformed data rejects the entire import.
- The initial CMU import requires an empty catalog.
- Natural-language recommendation will be implemented in two steps before
  release: structured catalog retrieval first, then semantic vector search.
- The structured-retrieval step will use an LLM to parse a user request and
  the application to query the catalog database.
- The request-parsing LLM will be Qwen3.5 2B, running locally through Ollama
  using the `qwen3.5:2b` model tag.
- Structured request intent will support catalog genre labels, an optional
  release-year range, and title keywords.
- Each recommendation request will return at most 10 movie cards.
- Structured filters are combined with AND. Title keywords match literal,
  case-insensitive substrings. Intent records year bounds and whether each is
  inclusive; database comparisons apply exclusivity without model arithmetic.
  Movies without a release year cannot match a year filter.
- Model output names year comparisons (`released_after`, `released_before`,
  `released_since`, `released_until`); the adapter maps them to the public
  year bounds and inclusive flags without arithmetic. Until includes its year.
- Structured-retrieval results are ordered by title and identifier, without
  relevance ranking. Unsupported constraints or requests without any supported
  filters are rejected instead of returning arbitrary or partial matches.
- The LLM will not write SQL directly; the application will construct database
  queries from constrained parsed fields.
- The vector-search step will combine semantic synopsis retrieval with the
  structured metadata filters.
- User accounts, live external movie-data provider APIs, a frontend, and
  LLM-generated recommendation explanations are deferred.

## Technology

- The backend language is Python.
- The web API framework is FastAPI.
- Uvicorn will serve the FastAPI application locally and in containers.
- The initial database is SQLite.
- SQLAlchemy ORM 2 will access the database.
- Alembic will manage database schema migrations.
- Dependencies and the project-local virtual environment will be managed with uv.
- Pyright in strict mode will enforce static type checking.
- Ruff will lint and format Python code.
- Docker will containerize the application.
- Docker Compose will define and run the local application stack.
- Docker Compose will provide `DATABASE_URL` and persist the SQLite database in
  a named Docker volume.
- Ollama will serve local model inference over HTTP. Docker Compose will run
  it as a CPU service with persistent model storage; GPU setup is deferred.
