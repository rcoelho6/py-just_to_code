from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from .models import Task


class TaskRepository:
    """Small SQLite repository implemented directly with the standard library."""

    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        path = Path(self.database_path)
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS task (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    priority INTEGER NOT NULL
                )
                """
            )

    def create(self, task: Task) -> Task:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO task (description, priority) VALUES (?, ?)",
                (task.description, task.priority),
            )
            return Task(id=cursor.lastrowid, description=task.description, priority=task.priority)

    def find(self, task_id: int) -> Task | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, description, priority FROM task WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._to_task(row) if row else None

    def update(self, task: Task) -> Task:
        with self._connect() as connection:
            connection.execute(
                "UPDATE task SET description = ?, priority = ? WHERE id = ?",
                (task.description, task.priority, task.id),
            )
        return task

    @staticmethod
    def _to_task(row: sqlite3.Row) -> Task:
        return Task(id=row["id"], description=row["description"], priority=row["priority"])
