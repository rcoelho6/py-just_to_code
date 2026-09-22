from __future__ import annotations

from app.clean_architecture.domain.task import Task
from app.clean_architecture.usecases.ports import TaskDatasourceBoundary, TaskIncomeBoundary


class TaskNotFoundError(LookupError):
    """Raised when an update targets a task that does not exist."""


class TaskService(TaskIncomeBoundary):
    def __init__(self, task_source: TaskDatasourceBoundary):
        self._task_source = task_source

    def create(self, task: Task) -> Task:
        return self._task_source.create(task)

    def update(self, task: Task) -> None:
        if task.id is None:
            raise TaskNotFoundError("ID not found")
        existing = self._task_source.find(task.id)
        if existing is None:
            raise TaskNotFoundError("ID not found")
        if existing.description == task.description and existing.priority == task.priority:
            return
        self._task_source.update(task)
