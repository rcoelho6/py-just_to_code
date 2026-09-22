from __future__ import annotations

import os

from fastapi import FastAPI
from peewee import SqliteDatabase


def _sqlite_path(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only SQLite DATABASE_URL values are supported by this branch")
    path = database_url.removeprefix("sqlite:///")
    if not path:
        raise ValueError("SQLite DATABASE_URL must include a database path")
    return path


def create_app(test_config: dict | None = None) -> FastAPI:
    settings = {
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///tasks.db"),
        "TESTING": False,
    }
    if test_config:
        settings.update(test_config)

    from .models import Task
    from .routes import register_routes
    from .services import TaskService

    database = SqliteDatabase(_sqlite_path(settings["DATABASE_URL"]), pragmas={"foreign_keys": 1})
    database.bind([Task], bind_refs=False, bind_backrefs=False)
    database.connect(reuse_if_open=True)
    database.create_tables([Task])
    database.close()

    app = FastAPI(title="just_to_code", docs_url="/docs", redoc_url="/redoc")
    app.state.database = database
    app.state.task_service = TaskService(database)
    register_routes(app)

    @app.middleware("http")
    async def database_lifecycle(request, call_next):
        if database.is_closed():
            database.connect()
        try:
            return await call_next(request)
        finally:
            if not database.is_closed():
                database.close()

    return app


app = create_app()
