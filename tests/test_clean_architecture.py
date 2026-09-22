from dataclasses import dataclass

import pytest

from app.clean_architecture.usecases.domains import Task, TaskValidationError
from app.clean_architecture.usecases.ports import TaskIncomeBoundary
from app.clean_architecture.usecases.service import TaskNotFoundError, TaskService


@dataclass
class InMemoryDatasource:
    tasks: dict[int, Task]

    def create(self, task: Task) -> Task:
        created = Task(id=len(self.tasks) + 1, description=task.description, priority=task.priority)
        self.tasks[created.id] = created
        return created

    def find(self, task_id: int) -> Task | None:
        return self.tasks.get(task_id)

    def update(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task


def test_domain_entity_is_framework_independent():
    task = Task(id=10, description="domain", priority=1)
    assert task.id == 10


def test_domain_rejects_invalid_data():
    with pytest.raises(TaskValidationError, match="Description cannot be null or blank"):
        Task(description="", priority=1)


def test_use_case_uses_input_and_output_boundaries():
    datasource = InMemoryDatasource({})
    service = TaskService(datasource)

    created = service.create(Task(description="created", priority=1))

    assert created == Task(id=1, description="created", priority=1)
    assert datasource.tasks[1] == created


def test_service_implements_the_input_boundary():
    service = TaskService(InMemoryDatasource({}))

    assert isinstance(service, TaskIncomeBoundary)


def test_use_case_does_not_update_when_values_are_equal():
    existing = Task(id=1, description="same", priority=1)
    datasource = InMemoryDatasource({1: existing})
    service = TaskService(datasource)

    service.update(existing)

    assert datasource.tasks[1] == existing


def test_use_case_raises_when_task_is_missing():
    service = TaskService(InMemoryDatasource({}))

    with pytest.raises(TaskNotFoundError, match="ID not found"):
        service.update(Task(id=1, description="missing", priority=1))
