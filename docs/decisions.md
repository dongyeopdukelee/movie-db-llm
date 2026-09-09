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
