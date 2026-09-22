from __future__ import annotations

import os

from flask import Flask
from peewee import SqliteDatabase


def _sqlite_path(database_url: str) -> str:
    """Convert a sqlite:/// URL into a filesystem path for Peewee."""
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only SQLite DATABASE_URL values are supported by this branch")
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

    database = SqliteDatabase(_sqlite_path(app.config["DATABASE_URL"]), pragmas={"foreign_keys": 1})
    app.extensions["database"] = database

    from .models import Task

    database.bind([Task], bind_refs=False, bind_backrefs=False)
    database.connect(reuse_if_open=True)
    database.create_tables([Task])
    database.close()

    @app.before_request
    def open_database_connection():
        if database.is_closed():
            database.connect()

    @app.teardown_request
    def close_database_connection(_exception=None):
        if not database.is_closed():
            database.close()

    from .routes import tasks_bp
    app.register_blueprint(tasks_bp)
    return app


def get_database() -> SqliteDatabase:
    from flask import current_app

    return current_app.extensions["database"]
