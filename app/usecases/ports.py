from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.usecases.domains import Task


class TaskNotFoundError(LookupError):
    """Raised when an operation references a missing task."""

@runtime_checkable
class TaskIncomeBoundary(Protocol):
    """Input port exposed by application use cases to delivery adapters."""

    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> None:
        ...


class TaskRepository(Protocol):
    def create(self, task: Task) -> Task:
        ...

    def get_by_id(self, task_id: int) -> Task | None:
        ...

    def update(self, task: Task) -> None:
        ...

