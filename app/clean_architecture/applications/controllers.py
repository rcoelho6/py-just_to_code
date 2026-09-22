from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from app.clean_architecture.applications.dtos import TaskDto, error_to_dto, task_to_dto
from app.clean_architecture.usecases.domains import TaskValidationError
from app.clean_architecture.usecases.ports import TaskIncomeBoundary
from app.clean_architecture.usecases.service import TaskNotFoundError


def create_tasks_blueprint(task_income_boundary: TaskIncomeBoundary) -> Blueprint:
    blueprint = Blueprint("tasks", __name__, url_prefix="/tasks")

    @blueprint.route("", methods=["POST"])
    @blueprint.route("/", methods=["POST"])
    def create():
        payload, error = _read_payload()
        if error:
            return error
        try:
            task = task_income_boundary.create(TaskDto.from_payload(payload).to_domain())
            response = jsonify(task_to_dto(task))
            response.status_code = 201
            response.headers["Location"] = f"/tasks/{task.id}"
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
            task = TaskDto.from_payload(payload).to_domain(task_id=task_id)
            task_income_boundary.update(task)
            return jsonify(task_to_dto(task)), 200
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


def _read_payload() -> tuple[dict[str, Any] | None, tuple | None]:
    if not request.is_json:
        return None, _error_response("Erro with status 400: Request must be JSON", 400)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error_response("Erro with status 400: Invalid JSON body", 400)
    return payload, None


def _error_response(message: str, status: int):
    return jsonify(error_to_dto(message, status)), status
