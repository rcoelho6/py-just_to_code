from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.application.ports import TaskIncomeBoundary
from app.usecases.domain.entities import Task, TaskValidationError
from app.usecases.services.services import TaskNotFoundError


def create_tasks_blueprint(service: TaskIncomeBoundary) -> Blueprint:
    blueprint = Blueprint("tasks", __name__, url_prefix="/tasks")

    @blueprint.route("", methods=["POST"])
    @blueprint.route("/", methods=["POST"])
    def create():
        payload, error = _read_payload()
        if error:
            return error
        try:
            task = Task(description=payload.get("description"), priority=payload.get("priority"))
            created = service.create(task)
            response = jsonify(_task_dto(created))
            response.status_code = 201
            response.headers["Location"] = f"/tasks/{created.id}"
            return response
        except TaskValidationError as exc:
            return _error_response(f"Erro with status 400: {exc}", 400)
        except Exception as exc:
            return _error_response(f"Unexpected error {exc}", 500)

    @blueprint.route("/<int:task_id>", methods=["PUT"])
    def update(task_id: int):
        payload, error = _read_payload()
        if error:
            return error
        try:
            task = Task(
                id=task_id,
                description=payload.get("description"),
                priority=payload.get("priority"),
            )
            service.update(task)
            return jsonify(_task_dto(task)), 200
        except TaskValidationError as exc:
            return _error_response(f"Erro with status 400: {exc}", 400)
        except TaskNotFoundError as exc:
            return _error_response(f"Erro with status 404: {exc}", 404)
        except Exception as exc:
            return _error_response(f"Unexpected error {exc}", 500)

    @blueprint.errorhandler(405)
    def method_not_allowed(_error):
        return _error_response("Method not allowed", 405)

    @blueprint.errorhandler(404)
    def not_found(_error):
        return _error_response("Not found", 404)

    return blueprint


def _read_payload() -> tuple[dict | None, tuple | None]:
    if not request.is_json:
        return None, _error_response("Erro with status 400: Request must be JSON", 400)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error_response("Erro with status 400: Invalid JSON body", 400)
    return payload, None


def _task_dto(task: Task) -> dict[str, object]:
    return {"description": task.description, "priority": task.priority}


def _error_response(message: str, status: int):
    return jsonify({"message": message, "status": status}), status
