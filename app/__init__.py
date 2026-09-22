from __future__ import annotations

import os

from flask import Flask
from peewee import SqliteDatabase

from app.clean_architecture.adapters.controllers import create_tasks_blueprint
from app.clean_architecture.frameworks.peewee_datasource import PeeweeTaskDatasource
from app.clean_architecture.frameworks.peewee_models import TaskModel
from app.clean_architecture.usecases.task_service import TaskService


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
    database.bind([TaskModel], bind_refs=False, bind_backrefs=False)
    database.connect(reuse_if_open=True)
    database.create_tables([TaskModel])
    database.close()

    datasource = PeeweeTaskDatasource(database)
    task_income_boundary = TaskService(datasource)
    app.extensions["database"] = database
    app.extensions["task_income_boundary"] = task_income_boundary
    app.register_blueprint(create_tasks_blueprint(task_income_boundary))

    @app.before_request
    def open_database_connection():
        if database.is_closed():
            database.connect()

    @app.teardown_request
    def close_database_connection(_exception=None):
        if not database.is_closed():
            database.close()

    return app
