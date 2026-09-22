from __future__ import annotations

import os
from pathlib import Path

from .database import TaskRepository
from .routes import TaskHTTPServer, create_server
from .services import TaskService


def database_path_from_environment() -> str:
    """Read a plain path or the legacy sqlite:/// form without an ORM."""
    configured = os.getenv("DATABASE_PATH")
    if configured:
        return configured
    database_url = os.getenv("DATABASE_URL", "sqlite:///tasks.db")
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    raise ValueError("DATABASE_PATH or a sqlite:/// DATABASE_URL is required")


def build_server(host: str = "0.0.0.0", port: int = 8080, database_path: str | Path | None = None) -> TaskHTTPServer:
    repository = TaskRepository(database_path or database_path_from_environment())
    return create_server(host, port, TaskService(repository))
