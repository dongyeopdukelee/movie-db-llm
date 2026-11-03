"""Exercise the HTTP boundary, local model adapter, and real SQL retrieval."""

import json
from collections.abc import Callable, Generator
from contextlib import contextmanager

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from movie_db_llm.database import configure_sqlite_connection, get_session
from movie_db_llm.main import app
from movie_db_llm.models import Base, Movie, MovieGenre
from movie_db_llm.ollama import OllamaIntentParser, get_intent_parser


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", configure_sqlite_connection)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def intent_data(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "genres": [],
        "year_filters": [],
        "title_keywords": [],
        "unsupported_constraints": [],
    }
    result.update(overrides)
    return result


def model_reply(
    intent: dict[str, object], *, done_reason: str = "stop"
) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "message": {"content": json.dumps(intent)},
            "done": True,
            "done_reason": done_reason,
        },
    )


@contextmanager
def recommendation_client(
    session: Session,
    handler: Callable[[httpx.Request], httpx.Response],
) -> Generator[httpx.Client]:
    previous_overrides = app.dependency_overrides.copy()
    with httpx.Client(
        base_url="http://ollama.test", transport=httpx.MockTransport(handler)
    ) as model_client:
        parser = OllamaIntentParser(model_client)
        app.dependency_overrides[get_session] = lambda: session
        app.dependency_overrides[get_intent_parser] = lambda: parser
        try:
            with TestClient(app) as client:
                yield client
        finally:
            app.dependency_overrides = previous_overrides


def add_movie(
    session: Session,
    title: str,
    year: int | None = 1995,
    genres: tuple[str, ...] = ("Comedy", "Drama"),
) -> None:
    session.add(
        Movie(
            title=title,
            synopsis="This full synopsis must not appear on movie cards.",
            release_year=year,
            genre_assignments=[MovieGenre(genre=genre) for genre in genres],
        )
    )
    session.commit()


def test_combines_filters_and_sends_catalog_schema(session: Session) -> None:
    add_movie(session, "Dog Days")
    add_movie(session, "Dog Days", 2005)
    add_movie(session, "Dog Show")
    add_movie(session, "Dog Days", genres=("Drama",))
    add_movie(session, "Dog Days", None)
    parsed = intent_data(
        genres=["Comedy", "Drama"],
        year_filters=[
            {"comparison": "since", "year": 1990},
            {"comparison": "until", "year": 1999},
        ],
        title_keywords=["DOG", "days"],
    )

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert request.url.path == "/api/chat"
        assert payload["model"] == "qwen3.5:2b"
        assert payload["stream"] is False
        assert payload["think"] is False
        assert payload["format"]["additionalProperties"] is False
        assert '["Comedy", "Drama"]' in payload["messages"][0]["content"]
        assert (
            payload["messages"][-1]["content"] == "90s comedy dramas, Dog Days"
        )
        return model_reply(parsed)

    with recommendation_client(session, handler) as client:
        response = client.post(
            "/recommendations", json={"query": "90s comedy dramas, Dog Days"}
        )

    assert response.status_code == 200
    assert response.json() == {
        "intent": {
            "genres": ["Comedy", "Drama"],
            "year_min": 1990,
            "year_max": 1999,
            "year_min_inclusive": True,
            "year_max_inclusive": True,
            "title_keywords": ["DOG", "days"],
            "unsupported_constraints": [],
        },
        "items": [
            {
                "id": 1,
                "title": "Dog Days",
                "release_year": 1995,
                "genres": ["Comedy", "Drama"],
            }
        ],
    }


@pytest.mark.parametrize(
    ("bounds", "expected", "interpreted_bounds"),
    [
        (
            [{"comparison": "since", "year": 2000}],
            ["New"],
            (2000, None, True, True),
        ),
        (
            [{"comparison": "since", "year": 1995}],
            ["New", "Old"],
            (1995, None, True, True),
        ),
        (
            [{"comparison": "until", "year": 1995}],
            ["Old"],
            (None, 1995, True, True),
        ),
        (
            [{"comparison": "in", "year": 1995}],
            ["Old"],
            (1995, 1995, True, True),
        ),
        (
            [
                {"comparison": "until", "year": 1995},
                {"comparison": "since", "year": 1995},
            ],
            ["Old"],
            (1995, 1995, True, True),
        ),
        (
            [{"comparison": "after", "year": 1995}],
            ["New"],
            (1995, None, False, True),
        ),
        (
            [{"comparison": "before", "year": 2005}],
            ["Old"],
            (None, 2005, True, False),
        ),
        (
            [{"comparison": "after", "year": 2005}],
            [],
            (2005, None, False, True),
        ),
        (
            [{"comparison": "before", "year": 1995}],
            [],
            (None, 1995, True, False),
        ),
        ([], ["New", "Old", "Undated"], (None, None, True, True)),
    ],
)
def test_optional_year_bounds(
    session: Session,
    bounds: list[dict[str, object]],
    expected: list[str],
    interpreted_bounds: tuple[int | None, int | None, bool, bool],
) -> None:
    """The API contract includes since/until boundaries and limits in to a year.

    Seeded years are the oracle: wrong operators admit or drop known cards;
    the adapter must also expose the literal bounds and exclude undated rows.
    """
    add_movie(session, "Old", 1995)
    add_movie(session, "New", 2005)
    add_movie(session, "Undated", None)
    parsed = intent_data(genres=["Comedy"], year_filters=bounds)
    with recommendation_client(
        session, lambda _: model_reply(parsed)
    ) as client:
        response = client.post("/recommendations", json={"query": "comedies"})
    assert response.status_code == 200
    assert [item["title"] for item in response.json()["items"]] == expected
    intent = response.json()["intent"]
    assert (
        intent["year_min"],
        intent["year_max"],
        intent["year_min_inclusive"],
        intent["year_max_inclusive"],
    ) == interpreted_bounds


def test_caps_and_orders_cards_without_duplicates(session: Session) -> None:
    for number in reversed(range(15)):
        add_movie(session, f"Comedy {number:02}")
    parsed = intent_data(genres=["Comedy", "Drama"])
    with recommendation_client(
        session, lambda _: model_reply(parsed)
    ) as client:
        response = client.post("/recommendations", json={"query": "comedies"})
    assert response.status_code == 200
    assert [item["title"] for item in response.json()["items"]] == [
        f"Comedy {number:02}" for number in range(10)
    ]


@pytest.mark.parametrize("keyword", ["100%_", "' OR 1=1 --"])
def test_title_keywords_are_literal_parameters(
    session: Session, keyword: str
) -> None:
    add_movie(session, f"The {keyword} Story")
    add_movie(session, "The 100xx Story")
    parsed = intent_data(title_keywords=[keyword])
    with recommendation_client(
        session, lambda _: model_reply(parsed)
    ) as client:
        response = client.post("/recommendations", json={"query": keyword})
    assert response.status_code == 200
    assert [item["title"] for item in response.json()["items"]] == [
        f"The {keyword} Story"
    ]


@pytest.mark.parametrize(
    ("title", "keyword", "nonmatch"),
    [
        ("Amélie", "AMÉLIE", "Amelie"),
        ("AMÉLIE", "amélie", "Amelie"),
        ("Straße", "STRASSE", "Strase"),
        ("Amélie 100%_/", "AMÉLIE 100%_/", "Amélie 100xx/"),
    ],
)
@pytest.mark.parametrize("combined_filters", [False, True])
def test_title_keywords_match_literal_unicode_case_pairs(
    session: Session,
    title: str,
    keyword: str,
    nonmatch: str,
    combined_filters: bool,
) -> None:
    """Case pairs match; accents, literal symbols, and AND filters matter."""
    add_movie(session, f"The {title} Story")
    add_movie(session, f"The {title} Story", 2005)
    add_movie(session, f"The {title} Story", genres=("Drama",))
    add_movie(session, f"The {nonmatch} Story")
    add_movie(session, f"The {title} Film")
    filters: dict[str, object] = (
        {
            "genres": ["Comedy", "Drama"],
            "year_filters": [
                {"comparison": "since", "year": 1990},
                {"comparison": "until", "year": 1999},
            ],
        }
        if combined_filters
        else {}
    )
    parsed = intent_data(title_keywords=[keyword, "STORY"], **filters)
    with recommendation_client(
        session, lambda _: model_reply(parsed)
    ) as client:
        response = client.post(
            "/recommendations", json={"query": f"title contains {keyword}"}
        )

    assert response.status_code == 200
    assert response.json()["intent"] == {
        "genres": ["Comedy", "Drama"] if combined_filters else [],
        "year_min": 1990 if combined_filters else None,
        "year_max": 1999 if combined_filters else None,
        "year_min_inclusive": True,
        "year_max_inclusive": True,
        "title_keywords": [keyword, "STORY"],
        "unsupported_constraints": [],
    }
    assert [item["id"] for item in response.json()["items"]] == (
        [1] if combined_filters else [1, 2, 3]
    )
    assert all(
        item["title"] == f"The {title} Story"
        for item in response.json()["items"]
    )


def test_no_matches_does_not_relax_filters(session: Session) -> None:
    add_movie(session, "Comedy")
    parsed = intent_data(
        genres=["Comedy"],
        year_filters=[{"comparison": "since", "year": 2020}],
    )
    with recommendation_client(
        session, lambda _: model_reply(parsed)
    ) as client:
        response = client.post(
            "/recommendations", json={"query": "new comedy"}
        )
    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"query": " "},
        {"query": "x" * 1001},
        {"query": 123},
        {"query": "comedy", "limit": 100},
    ],
)
def test_invalid_request_never_calls_model(
    session: Session, body: dict[str, object]
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid input must be rejected before model inference.")

    with recommendation_client(session, handler) as client:
        response = client.post("/recommendations", json=body)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "parsed",
    [
        intent_data(genres=["Invented genre"]),
        intent_data(
            year_filters=[
                {"comparison": "since", "year": 2000},
                {"comparison": "until", "year": 1990},
            ]
        ),
        intent_data(year_filters=[{"comparison": "since", "year": "1990"}]),
        intent_data(year_filters=[{"comparison": "since", "year": True}]),
        intent_data(year_filters=[{"comparison": "after", "year": "1990"}]),
        intent_data(year_filters=[{"comparison": "around", "year": 1990}]),
        intent_data(year_filters=[{"comparison": "in"}]),
        intent_data(
            year_filters=[{"comparison": "in", "year": 1990, "extra": 1}]
        ),
        intent_data(year_filters=[{"comparison": "in", "year": 0}]),
        intent_data(year_filters=[{"comparison": "in", "year": 10000}]),
        intent_data(year_filters=[{"comparison": "in", "year": 1990}] * 3),
        intent_data(title_keywords=[""]),
        intent_data(title_keywords=["x"] * 11),
        intent_data(sql="SELECT * FROM movies"),
        intent_data(
            year_filters=[
                {"comparison": "after", "year": 1990},
                {"comparison": "since", "year": 1995},
            ]
        ),
        intent_data(
            year_filters=[
                {"comparison": "before", "year": 2000},
                {"comparison": "until", "year": 1995},
            ]
        ),
        intent_data(
            year_filters=[
                {"comparison": "in", "year": 1990},
                {"comparison": "since", "year": 1990},
            ]
        ),
        intent_data(
            year_filters=[
                {"comparison": "before", "year": 2000},
                {"comparison": "in", "year": 1990},
            ]
        ),
        {"genres": []},
    ],
)
def test_rejects_invalid_model_intent(
    session: Session, parsed: dict[str, object]
) -> None:
    with recommendation_client(
        session, lambda _: model_reply(parsed)
    ) as client:
        response = client.post("/recommendations", json={"query": "movies"})
    assert response.status_code == 502


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content="not JSON"),
        httpx.Response(
            200,
            json={
                "message": {"content": "not JSON"},
                "done": True,
                "done_reason": "stop",
            },
        ),
        httpx.Response(200, json={"message": {"content": "{}"}}),
        model_reply(
            intent_data(year_filters=[{"comparison": "since", "year": 1990}]),
            done_reason="length",
        ),
    ],
)
def test_rejects_malformed_or_truncated_response(
    session: Session, response: httpx.Response
) -> None:
    with recommendation_client(session, lambda _: response) as client:
        result = client.post("/recommendations", json={"query": "90s movies"})
    assert result.status_code == 502


@pytest.mark.parametrize("status", [404, 500, 503])
def test_model_service_failures_are_actionable(
    session: Session, status: int
) -> None:
    with recommendation_client(
        session,
        lambda _: httpx.Response(status, json={"error": "unavailable"}),
    ) as client:
        response = client.post("/recommendations", json={"query": "comedies"})
    assert response.status_code == 503
    assert "Start Ollama" in response.json()["detail"]


@pytest.mark.parametrize("error", [httpx.ConnectError, httpx.ReadTimeout])
def test_model_connection_errors(
    session: Session, error: type[httpx.RequestError]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error("Model unavailable", request=request)

    with recommendation_client(session, handler) as client:
        response = client.post("/recommendations", json={"query": "comedies"})
    assert response.status_code == 503


@pytest.mark.parametrize(
    "parsed",
    [
        intent_data(),
        intent_data(
            genres=["Comedy"], unsupported_constraints=["plot about dogs"]
        ),
    ],
)
def test_unsupported_or_empty_intent_returns_no_partial_matches(
    session: Session, parsed: dict[str, object]
) -> None:
    add_movie(session, "Comedy")
    with recommendation_client(
        session, lambda _: model_reply(parsed)
    ) as client:
        response = client.post(
            "/recommendations", json={"query": "dog movies"}
        )
    assert response.status_code == 422
    assert response.json()["detail"]["unsupported_constraints"]
    assert "items" not in response.json()
