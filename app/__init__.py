from __future__ import annotations

import os
from pathlib import Path

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///tasks.db"),
        TESTING=False,
    )
    if test_config:
        app.config.update(test_config)

    engine = create_engine(app.config["DATABASE_URL"], future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.extensions["engine"] = engine
    app.extensions["session_factory"] = session_factory

    from .models import Task
    Base.metadata.create_all(engine)

    from .routes import tasks_bp
    app.register_blueprint(tasks_bp)

    @app.teardown_appcontext
    def close_session(_exception=None):
        session = getattr(app, "_request_session", None)
        if session is not None:
            session.close()
            app._request_session = None

    return app


def get_session() -> Session:
    from flask import current_app

    session = getattr(current_app, "_request_session", None)
    if session is None:
        session = current_app.extensions["session_factory"]()
        current_app._request_session = session
    return session
