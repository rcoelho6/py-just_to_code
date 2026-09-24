from __future__ import annotations

from app.hexagonal.domain.entities import Task
from app.hexagonal.application.ports.inbound import TaskUseCasePort
from app.hexagonal.application.ports.outbound import TaskRepositoryPort


class TaskNotFoundError(LookupError):
    """Raised when an update targets a task that does not exist."""


class TaskService(TaskUseCasePort):
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
