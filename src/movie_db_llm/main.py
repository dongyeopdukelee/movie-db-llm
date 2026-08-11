"""FastAPI application entry point."""

from typing import Literal

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Movie DB LLM")


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
