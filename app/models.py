from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ValidationError(ValueError):
    """Raised when a task does not satisfy the API domain rules."""


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)

    def __init__(self, description: str, priority: int, id: int | None = None, *, updating: bool = False):
        if updating and (id is None or id <= 0):
            raise ValidationError("Id cannot be null or less than or equals 0")
        validate_task(description, priority)
        if id is not None:
            self.id = id
        self.description = description
        self.priority = priority


def validate_task(description: str | None, priority: int | None) -> None:
    if description is None or not isinstance(description, str) or not description.strip():
        raise ValidationError("Description cannot be null or blank")
    if priority is None or isinstance(priority, bool) or not isinstance(priority, int) or priority < 0:
        raise ValidationError("Priority cannot be null or negative")


def task_dto(task: Task) -> dict:
    return {"description": task.description, "priority": task.priority}
