from __future__ import annotations

from typing import Protocol

from app.clean_architecture.domain.task import Task


class TaskDatasourceBoundary(Protocol):
    """Output boundary implemented by a persistence adapter."""

    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> Task:
        ...

    def find(self, task_id: int) -> Task | None:
        ...


class TaskIncomeBoundary(Protocol):
    """Input boundary exposed to delivery adapters."""

    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> None:
        ...
