from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.hexagonal.domain.entities import Task


@runtime_checkable
class TaskUseCasePort(Protocol):
    """Driving port used by HTTP, CLI or other inbound adapters."""

    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> None:
        ...
