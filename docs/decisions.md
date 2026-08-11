# Project decisions

This is the living record of high-level decisions for Movie DB LLM. Update it
when a decision is made, changed, or removed.

## Product scope

- The initial product is an API-first movie catalog for browsing and title search.
- The first catalog will use a small, locally seeded dataset.
- LLM features, user accounts, external movie-data providers, and a frontend
  are deferred until after the core movie API works.

## Technology

- The backend language is Python.
- The web API framework is FastAPI.
- Uvicorn will serve the FastAPI application locally and in containers.
- The initial database is SQLite.
- SQLAlchemy ORM 2 will access the database.
- Dependencies and the project-local virtual environment will be managed with uv.
- Docker will containerize the application.
- Docker Compose will define and run the local application stack.
