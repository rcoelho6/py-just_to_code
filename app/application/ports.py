from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.usecases.domain.entities import Task


@runtime_checkable
class TaskIncomeBoundary(Protocol):
    """Input port exposed by application use cases to delivery adapters."""

    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> None:
        ...
