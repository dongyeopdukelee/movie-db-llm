# Product roadmap

The target experience is a user request such as "I want to watch a sad movie
with dogs in it" becoming grounded movie recommendations.

## 1. Database lifecycle — Complete

- [x] Use Alembic migrations to track schema changes. The initial
  `create_movie_catalog` revision creates the catalog schema.
- [x] Set up the database explicitly before starting the API with
  `uv run alembic upgrade head`.

## 2. Catalog API

- Add a movie-detail endpoint with the full synopsis.
- Add title search and genre filtering.
- Add pagination.

## 3. Catalog ingestion — Complete

- [x] Keep the CMU Movie Summary Corpus source snapshot and attribution in the
  repository.
- [x] Parse and validate the metadata and plot-summary source files before
  writing any catalog rows.
- [x] Import the validated CMU catalog into an empty database with
  `uv run movie-db-llm import-cmu`.

## 4. Semantic retrieval

- Generate embeddings for movie synopses.
- Add vector search over the catalog.
- Combine semantic retrieval with structured metadata filters.

## 5. LLM recommendations

- Add an API endpoint for natural-language movie requests.
- Use an LLM to interpret requests and explain retrieved recommendations.
- Ground responses in catalog results.

## 6. Evaluation and operations

- Create a representative set of recommendation queries.
- Measure retrieval quality, cost, and latency.
- Handle ambiguous and unsupported requests safely.
