from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import build_server
from app.models import Task, TaskValidationError
from app.services import TaskNotFoundError, TaskService


class InMemoryRepository:
    def __init__(self) -> None:
        self.tasks: dict[int, Task] = {}

    def create(self, task: Task) -> Task:
        created = Task(id=len(self.tasks) + 1, description=task.description, priority=task.priority)
        self.tasks[created.id] = created
        return created

    def find(self, task_id: int) -> Task | None:
        return self.tasks.get(task_id)

    def update(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task


class NoFrameworkTests(unittest.TestCase):
    def test_domain_validation(self) -> None:
        with self.assertRaises(TaskValidationError):
            Task(description="", priority=1)

    def test_service_uses_repository_protocol(self) -> None:
        repository = InMemoryRepository()
        service = TaskService(repository)
        created = service.create(Task(description="created", priority=1))
        self.assertEqual(created, Task(id=1, description="created", priority=1))
        with self.assertRaises(TaskNotFoundError):
            service.update(Task(id=2, description="missing", priority=1))

    def test_http_and_sqlite_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            server = build_server("127.0.0.1", 0, Path(directory) / "test.db")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, headers, body = self._request("POST", f"{base_url}/tasks", {"description": "created", "priority": 5})
                self.assertEqual(status, 201)
                self.assertEqual(headers["Location"], "/tasks/1")
                self.assertEqual(body, {"description": "created", "priority": 5})

                status, _, body = self._request("PUT", f"{base_url}/tasks/1", {"description": "updated", "priority": 2})
                self.assertEqual(status, 200)
                self.assertEqual(body, {"description": "updated", "priority": 2})

                status, _, body = self._request("GET", f"{base_url}/tasks/1")
                self.assertEqual(status, 405)
                self.assertEqual(body["status"], 405)

                status, _, body = self._request("POST", f"{base_url}/tasks/1", {"description": "x", "priority": 1})
                self.assertEqual(status, 405)
                self.assertEqual(body["status"], 405)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def _request(self, method: str, url: str, payload: dict | None = None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(url, method=method, data=data, headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        return response.status, response.headers, json.loads(response.read())


if __name__ == "__main__":
    unittest.main()
