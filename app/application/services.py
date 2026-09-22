from __future__ import annotations

from app.application.ports import TaskRepository
from app.domain.entities import Task


class TaskNotFoundError(LookupError):
    """Raised when an operation references a missing task."""


class TaskService:
    def __init__(self, repository: TaskRepository):
        self._repository = repository

    def create(self, task: Task) -> Task:
        return self._repository.create(task)

    def update(self, task: Task) -> None:
        existing = self._repository.get_by_id(task.id)
        if existing is None:
            raise TaskNotFoundError("ID not found")
        if existing.description == task.description and existing.priority == task.priority:
            return
        self._repository.update(task)
