from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Task


class TaskNotFoundError(LookupError):
    pass


class TaskService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, task: Task) -> Task:
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def update(self, task: Task) -> None:
        existing = self.session.scalar(select(Task).where(Task.id == task.id))
        if existing is None:
            raise TaskNotFoundError("ID not found")
        if existing.description == task.description and existing.priority == task.priority:
            return
        existing.description = task.description
        existing.priority = task.priority
        self.session.commit()
