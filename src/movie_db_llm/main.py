"""FastAPI application entry point."""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Movie DB LLM")


def main() -> None:
    """Run the application server locally."""
    uvicorn.run(app, host="127.0.0.1", port=8000)
