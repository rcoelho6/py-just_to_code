from __future__ import annotations

from typing import Protocol

from app.hexagonal.domain.entities import Task


class TaskRepositoryPort(Protocol):
    """Driven port implemented by a persistence adapter."""

    def create(self, task: Task) -> Task:
        ...

    def find(self, task_id: int) -> Task | None:
        ...

    def update(self, task: Task) -> Task:
        ...
