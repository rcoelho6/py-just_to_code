from dataclasses import dataclass

import pytest

from app.hexagonal.application.services import TaskNotFoundError, TaskService
from app.hexagonal.domain.entities import Task, TaskValidationError
from app.hexagonal.application.ports.inbound import TaskUseCasePort


@dataclass
class InMemoryRepository:
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


def test_domain_is_independent_from_adapters():
    assert Task(id=1, description="domain", priority=1).id == 1


def test_domain_rejects_invalid_description():
    with pytest.raises(TaskValidationError, match="Description cannot be null or blank"):
        Task(description="", priority=1)


def test_service_implements_driving_port():
    service = TaskService(InMemoryRepository({}))

    assert isinstance(service, TaskUseCasePort)


def test_service_creates_through_driven_port():
    repository = InMemoryRepository({})
    service = TaskService(repository)

    created = service.create(Task(description="created", priority=1))

    assert created == Task(id=1, description="created", priority=1)
    assert repository.tasks[1] == created


def test_service_updates_only_when_values_change():
    existing = Task(id=1, description="old", priority=1)
    repository = InMemoryRepository({1: existing})
    service = TaskService(repository)

    service.update(Task(id=1, description="new", priority=2))

    assert repository.tasks[1] == Task(id=1, description="new", priority=2)


def test_service_raises_for_missing_task():
    service = TaskService(InMemoryRepository({}))

    with pytest.raises(TaskNotFoundError, match="ID not found"):
        service.update(Task(id=1, description="missing", priority=1))
