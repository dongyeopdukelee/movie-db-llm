# Product roadmap

The target experience is a user request such as "I want to watch a sad movie
with dogs in it" becoming grounded movie recommendations.

## 1. Database lifecycle

- Use Alembic migrations to track schema changes.
- Set up the database explicitly before starting the API.
- Keep demo seed data as a separate development-only action.

## 2. Catalog API

- Add a movie-detail endpoint with the full synopsis.
- Add title search and genre filtering.
- Add pagination.

## 3. Catalog ingestion

- Build an ingestion workflow for a larger movie catalog.
- Validate imported data and record its provenance.

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
