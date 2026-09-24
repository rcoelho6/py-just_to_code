from __future__ import annotations

import os

from flask import Flask
from peewee import SqliteDatabase

from app.hexagonal.infrastructure.adapters.inbound import create_tasks_blueprint
from app.hexagonal.infrastructure.adapters import PeeweeTaskRepository, TaskRecord
from app.hexagonal.application.services import TaskService


def _sqlite_path(database_url: str) -> str:
    """Convert a sqlite:/// URL into the path expected by Peewee."""
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only SQLite DATABASE_URL values are supported")
    path = database_url.removeprefix("sqlite:///")
    if not path:
        raise ValueError("SQLite DATABASE_URL must include a database path")
    return path


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///tasks.db"),
        TESTING=False,
    )
    if test_config:
        app.config.update(test_config)

    database = SqliteDatabase(
        _sqlite_path(app.config["DATABASE_URL"]),
        pragmas={"foreign_keys": 1},
    )
    database.bind([TaskRecord], bind_refs=False, bind_backrefs=False)
    database.connect(reuse_if_open=True)
    database.create_tables([TaskRecord])
    database.close()

    repository = PeeweeTaskRepository(database)
    task_use_case = TaskService(repository)
    app.extensions["database"] = database
    app.extensions["task_use_case"] = task_use_case
    app.register_blueprint(create_tasks_blueprint(task_use_case))

    @app.before_request
    def open_database_connection():
        if database.is_closed():
            database.connect()

    @app.teardown_request
    def close_database_connection(_exception=None):
        if not database.is_closed():
            database.close()

    return app
