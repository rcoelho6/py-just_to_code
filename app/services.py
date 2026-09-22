from __future__ import annotations

from peewee import Database

from .models import Task


class TaskNotFoundError(LookupError):
    """Raised when an update targets a task that does not exist."""


class TaskService:
    def __init__(self, database: Database):
        self.database = database

    def create(self, task: Task) -> Task:
        with self.database.atomic():
            task.save(force_insert=True)
        return task

    def update(self, task: Task) -> None:
        with self.database.atomic():
            existing = Task.get_or_none(Task.id == task.id)
            if existing is None:
                raise TaskNotFoundError("ID not found")
            if existing.description == task.description and existing.priority == task.priority:
                return
            existing.description = task.description
            existing.priority = task.priority
            existing.save(only=[Task.description, Task.priority])
