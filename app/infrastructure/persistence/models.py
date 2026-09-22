from __future__ import annotations

from peewee import AutoField, IntegerField, Model, TextField


class PeeweeBaseModel(Model):
    class Meta:
        database = None


class PeeweeTask(PeeweeBaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)

    class Meta:
        table_name = "task"
