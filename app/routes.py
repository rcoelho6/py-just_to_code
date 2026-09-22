from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .models import Task, TaskValidationError
from .services import TaskNotFoundError, TaskService


class TaskRequestHandler(BaseHTTPRequestHandler):
    server_version = "JustToCode/NoFramework"

    def do_POST(self) -> None:
        if self.path not in ("/tasks", "/tasks/"):
            self._method_not_allowed() if self.path.startswith("/tasks/") else self._error(HTTPStatus.NOT_FOUND, "Not found")
            return
        try:
            task = self.server.task_service.create(self._task_from_body())
            self._json(HTTPStatus.CREATED, self._task_payload(task), {"Location": f"/tasks/{task.id}"})
        except (TaskValidationError, ValueError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, f"Erro with status 400: {exc}")
        except Exception as exc:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Unexpected error {exc}")

    def do_PUT(self) -> None:
        if not self.path.startswith("/tasks/"):
            self._error(HTTPStatus.NOT_FOUND, "Not found")
            return
        try:
            task_id = int(self.path.removeprefix("/tasks/"))
            if task_id <= 0:
                raise ValueError("Invalid task id")
            task = self._task_from_body(task_id=task_id)
            self.server.task_service.update(task)
            self._json(HTTPStatus.OK, self._task_payload(task))
        except (TaskValidationError, ValueError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, f"Erro with status 400: {exc}")
        except TaskNotFoundError as exc:
            self._error(HTTPStatus.NOT_FOUND, f"Erro with status 404: {exc}")
        except Exception as exc:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Unexpected error {exc}")

    def do_GET(self) -> None:
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        self._method_not_allowed()

    def do_PATCH(self) -> None:
        self._method_not_allowed()

    def _task_from_body(self, task_id: int | None = None) -> Task:
        body = self._read_json()
        return Task(id=task_id, description=body.get("description"), priority=body.get("priority"))

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Request must contain a valid JSON object") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request must contain a valid JSON object")
        return payload

    def _method_not_allowed(self) -> None:
        self._error(HTTPStatus.METHOD_NOT_ALLOWED, "Method not allowed")

    def _json(self, status: HTTPStatus, payload: dict[str, Any], headers: dict[str, str] | None = None) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(encoded)

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json(status, {"message": message, "status": status.value})

    @staticmethod
    def _task_payload(task: Task) -> dict[str, Any]:
        return {"description": task.description, "priority": task.priority}

    def log_message(self, format: str, *args: Any) -> None:
        return


class TaskHTTPServer(ThreadingHTTPServer):
    task_service: TaskService


def create_server(host: str, port: int, task_service: TaskService) -> TaskHTTPServer:
    server = TaskHTTPServer((host, port), TaskRequestHandler)
    server.task_service = task_service
    return server
