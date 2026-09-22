from __future__ import annotations

from peewee import Database

from app.clean_architecture.usecases.domains import Task
from app.clean_architecture.infrastructures.peewee_models import TaskModel
from app.clean_architecture.usecases.service import TaskNotFoundError


class PeeweeTaskDatasource:
    def __init__(self, database: Database):
        self._database = database

    def create(self, task: Task) -> Task:
        with self._database.atomic():
            model = TaskModel.create(description=task.description, priority=task.priority)
        return model.to_domain()

    def find(self, task_id: int) -> Task | None:
        model = TaskModel.get_or_none(TaskModel.id == task_id)
        return model.to_domain() if model is not None else None

    def update(self, task: Task) -> Task:
        with self._database.atomic():
            model = TaskModel.get_or_none(TaskModel.id == task.id)
            if model is None:
                raise TaskNotFoundError("ID not found")
            model.description = task.description
            model.priority = task.priority
            model.save(only=[TaskModel.description, TaskModel.priority])
        return model.to_domain()
