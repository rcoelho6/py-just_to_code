from __future__ import annotations

from peewee import AutoField, Database, IntegerField, Model, TextField

from app.hexagonal.application.services import TaskNotFoundError
from app.hexagonal.domain.entities import Task
from app.hexagonal.application.ports.outbound import TaskRepositoryPort


class PeeweeBaseModel(Model):
    class Meta:
        database = None


class TaskRecord(PeeweeBaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)

    class Meta:
        table_name = "task"

    def to_domain(self) -> Task:
        return Task(id=self.id, description=self.description, priority=self.priority)


class PeeweeTaskRepository(TaskRepositoryPort):
    """Driven adapter that maps the repository port to Peewee/SQLite."""

    def __init__(self, database: Database):
        self._database = database

    def create(self, task: Task) -> Task:
        with self._database.atomic():
            record = TaskRecord.create(description=task.description, priority=task.priority)
        return record.to_domain()

    def find(self, task_id: int) -> Task | None:
        record = TaskRecord.get_or_none(TaskRecord.id == task_id)
        return record.to_domain() if record is not None else None

    def update(self, task: Task) -> Task:
        with self._database.atomic():
            record = TaskRecord.get_or_none(TaskRecord.id == task.id)
            if record is None:
                raise TaskNotFoundError("ID not found")
            record.description = task.description
            record.priority = task.priority
            record.save(only=[TaskRecord.description, TaskRecord.priority])
        return record.to_domain()
