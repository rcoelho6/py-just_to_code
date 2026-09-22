from __future__ import annotations

from peewee import AutoField, IntegerField, Model, TextField

from app.clean_architecture.domain.task import Task


class PeeweeBaseModel(Model):
    class Meta:
        database = None


class TaskModel(PeeweeBaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)

    class Meta:
        table_name = "task"

    def to_domain(self) -> Task:
        return Task(id=self.id, description=self.description, priority=self.priority)
