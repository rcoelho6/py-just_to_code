from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.clean_architecture.usecases.domains import Task


class TaskDatasourceBoundary(Protocol):
    """Output boundary implemented by a persistence adapter."""

    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> Task:
        ...

    def find(self, task_id: int) -> Task | None:
        ...


@runtime_checkable
class TaskIncomeBoundary(Protocol):
    """Input boundary exposed to delivery applications."""

    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> None:
        ...
