from __future__ import annotations

from typing import Protocol

from .models import Task


class TaskNotFoundError(LookupError):
    """Raised when an update targets a task that does not exist."""


class TaskRepositoryPort(Protocol):
    def create(self, task: Task) -> Task:
        ...

    def find(self, task_id: int) -> Task | None:
        ...

    def update(self, task: Task) -> Task:
        ...


class TaskService:
    def __init__(self, repository: TaskRepositoryPort):
        self._repository = repository

    def create(self, task: Task) -> Task:
        return self._repository.create(task)

    def update(self, task: Task) -> None:
        if task.id is None:
            raise TaskNotFoundError("ID not found")
        existing = self._repository.find(task.id)
        if existing is None:
            raise TaskNotFoundError("ID not found")
        if existing.description == task.description and existing.priority == task.priority:
            return
        self._repository.update(task)
