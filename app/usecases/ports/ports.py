from __future__ import annotations

from typing import Protocol

from app.usecases.domain.entities import Task


class TaskRepository(Protocol):
    def create(self, task: Task) -> Task:
        ...

    def get_by_id(self, task_id: int) -> Task | None:
        ...

    def update(self, task: Task) -> None:
        ...

