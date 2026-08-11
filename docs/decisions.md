# Project decisions

This is the living record of high-level decisions for Movie DB LLM. Update it
when a decision is made, changed, or removed.

## Product scope

- The initial product is an API-first movie catalog for browsing and title search.
- The first catalog will use a small, locally seeded dataset.
- Movies and predefined genres will use a normalized `movies` / `movie_genres`
  association-table design; a separate genre lookup table is not needed yet.
- Catalog-list responses will use an `items` envelope and return lightweight
  movie cards; full synopses belong to a future movie-detail endpoint.
- Initial catalog movies must have a release year.
- LLM features, user accounts, external movie-data providers, and a frontend
  are deferred until after the core movie API works.
- Future natural-language retrieval will combine structured metadata filters
  with semantic vector search; it is deferred from the initial product.

## Technology

- The backend language is Python.
- The web API framework is FastAPI.
- Uvicorn will serve the FastAPI application locally and in containers.
- The initial database is SQLite.
- SQLAlchemy ORM 2 will access the database.
- Dependencies and the project-local virtual environment will be managed with uv.
- Pyright in strict mode will enforce static type checking.
- Ruff will lint and format Python code.
- Docker will containerize the application.
- Docker Compose will define and run the local application stack.
- Docker Compose will provide `DATABASE_URL` and persist the SQLite database in
  a named Docker volume.
