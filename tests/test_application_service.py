from dataclasses import dataclass

import pytest

from app.application.ports import TaskIncomeBoundary
from app.usecases.services.services import TaskNotFoundError, TaskService
from app.usecases.domain.entities import Task


@dataclass
class InMemoryTaskRepository:
    tasks: dict[int, Task]

    def create(self, task: Task) -> Task:
        created = Task(id=len(self.tasks) + 1, description=task.description, priority=task.priority)
        self.tasks[created.id] = created
        return created

    def get_by_id(self, task_id: int) -> Task | None:
        return self.tasks.get(task_id)

    def update(self, task: Task) -> None:
        self.tasks[task.id] = task


def test_service_creates_without_knowing_the_persistence_technology():
    repository = InMemoryTaskRepository({})
    service = TaskService(repository)

    created = service.create(Task(description="unit test", priority=1))

    assert created.id == 1
    assert repository.tasks[1] == created


def test_service_implements_the_application_input_port():
    service = TaskService(InMemoryTaskRepository({}))

    assert isinstance(service, TaskIncomeBoundary)


def test_service_updates_only_when_values_change():
    repository = InMemoryTaskRepository({1: Task(id=1, description="old", priority=1)})
    service = TaskService(repository)

    service.update(Task(id=1, description="new", priority=2))

    assert repository.tasks[1] == Task(id=1, description="new", priority=2)


def test_service_raises_when_task_does_not_exist():
    service = TaskService(InMemoryTaskRepository({}))

    with pytest.raises(TaskNotFoundError, match="ID not found"):
        service.update(Task(id=1, description="missing", priority=1))
