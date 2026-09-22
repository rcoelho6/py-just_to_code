from __future__ import annotations

from peewee import AutoField, IntegerField, Model, TextField

from . import Base


class ValidationError(ValueError):
    """Raised when a task does not satisfy the API domain rules."""


class BaseModel(Model):
    class Meta:
        database = None


class Task(BaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)

    class Meta:
        table_name = "task"


def validate_task(description: str | None, priority: int | None) -> None:
    if description is None or not isinstance(description, str) or not description.strip():
        raise ValidationError("Description cannot be null or blank")
    if priority is None or isinstance(priority, bool) or not isinstance(priority, int) or priority < 0:
        raise ValidationError("Priority cannot be null or negative")


def build_task(description: str | None, priority: int | None, *, task_id: int | None = None, updating: bool = False) -> Task:
    if updating and (task_id is None or task_id <= 0):
        raise ValidationError("Id cannot be null or less than or equals 0")
    validate_task(description, priority)
    return Task(id=task_id, description=description, priority=priority)


def task_dto(task: Task) -> dict:
    return {"description": task.description, "priority": task.priority}
