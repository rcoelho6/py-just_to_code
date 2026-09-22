from __future__ import annotations

from app.usecases.domains import Task
from app.usecases.ports import TaskRepository, TaskNotFoundError, TaskIncomeBoundary


class TaskService(TaskIncomeBoundary):
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
