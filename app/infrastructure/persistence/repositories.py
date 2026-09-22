from __future__ import annotations

from peewee import Database

from app.domain.entities import Task
from app.infrastructure.persistence.models import PeeweeTask


class PeeweeTaskRepository:
    def __init__(self, database: Database):
        self._database = database

    def create(self, task: Task) -> Task:
        with self._database.atomic():
            record = PeeweeTask.create(
                description=task.description,
                priority=task.priority,
            )
        return self._to_domain(record)

    def get_by_id(self, task_id: int) -> Task | None:
        record = PeeweeTask.get_or_none(PeeweeTask.id == task_id)
        return self._to_domain(record) if record is not None else None

    def update(self, task: Task) -> None:
        with self._database.atomic():
            record = PeeweeTask.get_by_id(task.id)
            record.description = task.description
            record.priority = task.priority
            record.save(only=[PeeweeTask.description, PeeweeTask.priority])

    @staticmethod
    def _to_domain(record: PeeweeTask) -> Task:
        return Task(id=record.id, description=record.description, priority=record.priority)
