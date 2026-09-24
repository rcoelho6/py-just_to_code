from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from app.hexagonal.application.services import TaskNotFoundError
from app.hexagonal.domain.entities import TaskValidationError
from app.hexagonal.infrastructure.adapters.inbound.tasks_adpter import TasksAdapter

def create_tasks_blueprint(tasks_adpter: TasksAdapter) -> Blueprint:
    """Build the HTTP adapter around the driving use-case port."""
    blueprint = Blueprint("tasks", __name__, url_prefix="/tasks")

    @blueprint.route("", methods=["POST"])
    @blueprint.route("/", methods=["POST"])
    def create():
        payload, error = _read_payload()
        if error:
            return error
        try:
            task = tasks_adpter.create(payload)
            response = jsonify(task)
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
            tasks_adpter.update(task_id)
            return jsonify(payload), 200
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
    return jsonify({"message": message, "status": status}), status
