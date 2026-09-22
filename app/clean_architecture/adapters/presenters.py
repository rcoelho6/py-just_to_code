from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.clean_architecture.domain.task import Task


@dataclass(frozen=True, slots=True)
class TaskDto:
    description: Any = None
    priority: Any = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> TaskDto:
        return cls(description=payload.get("description"), priority=payload.get("priority"))

    def to_domain(self, task_id: int | None = None) -> Task:
        return Task(id=task_id, description=self.description, priority=self.priority)


def task_to_dto(task: Task) -> dict[str, Any]:
    return {"description": task.description, "priority": task.priority}


def error_to_dto(message: str, status: int) -> dict[str, Any]:
    return {"message": message, "status": status}
