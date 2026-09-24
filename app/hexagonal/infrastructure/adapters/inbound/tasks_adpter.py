from __future__ import annotations

from typing import Any

from app.hexagonal.domain.entities import Task
from app.hexagonal.application.ports.inbound import TaskUseCasePort


class TasksAdapter:
    def __init__(self, task_use_case: TaskUseCasePort):
        self.task_use_case = task_use_case

    def create(self, payload: str):
        task = self._task_use_case.create(self._task_from_payload(payload))
        return self._task_to_payload(task);

    def update(self, task_id: int, payload: str):
            task = self._task_from_payload(payload, task_id=task_id)
            self._task_use_case.update(task)
            return self._task_to_payload(task)

    def _task_from_payload(payload: dict[str, Any], task_id: int | None = None) -> Task:
        return Task(
            id=task_id,
            description=payload.get("description"),
            priority=payload.get("priority"),
        )

    def _task_to_payload(task: Task) -> dict[str, Any]:
        return {"description": task.description, "priority": task.priority}
