"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Literal

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from movie_db_llm.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Initialize local application resources."""
    initialize_database()
    yield


app = FastAPI(title="Movie DB LLM", lifespan=lifespan)


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    status: Literal["ok"]


@app.get("/health")
def health_check() -> HealthResponse:
    """Report that the API is running."""
    return HealthResponse(status="ok")


def main() -> None:
    """Run the application server locally."""
    uvicorn.run(app, host="127.0.0.1", port=8000)
