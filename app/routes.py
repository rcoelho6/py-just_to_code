from __future__ import annotations

from flask import Blueprint, jsonify, request

from . import get_session
from .models import Task, ValidationError, task_dto
from .services import TaskNotFoundError, TaskService


tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def error_response(message: str, status: int):
    return jsonify({"message": message, "status": status}), status


def read_payload() -> tuple[dict | None, tuple | None]:
    if not request.is_json:
        return None, error_response("Erro with status 400: Request must be JSON", 400)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, error_response("Erro with status 400: Invalid JSON body", 400)
    return payload, None


@tasks_bp.route("", methods=["POST"])
@tasks_bp.route("/", methods=["POST"])
def create():
    payload, error = read_payload()
    if error:
        return error
    try:
        task = Task(description=payload.get("description"), priority=payload.get("priority"))
        TaskService(get_session()).create(task)
        response = jsonify(task_dto(task))
        response.status_code = 201
        response.headers["Location"] = f"/tasks/{task.id}"
        return response
    except ValidationError as exc:
        get_session().rollback()
        return error_response(f"Erro with status 400: {exc}", 400)
    except Exception as exc:
        get_session().rollback()
        return error_response(f"Unexpected error {exc}", 500)


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
def update(task_id: int):
    payload, error = read_payload()
    if error:
        return error
    try:
        task = Task(description=payload.get("description"), priority=payload.get("priority"), id=task_id, updating=True)
        TaskService(get_session()).update(task)
        return jsonify(task_dto(task)), 200
    except ValidationError as exc:
        get_session().rollback()
        return error_response(f"Erro with status 400: {exc}", 400)
    except TaskNotFoundError as exc:
        get_session().rollback()
        return error_response(f"Erro with status 404: {exc}", 404)
    except Exception as exc:
        get_session().rollback()
        return error_response(f"Unexpected error {exc}", 500)


@tasks_bp.errorhandler(405)
def method_not_allowed(_error):
    return error_response("Method not allowed", 405)


@tasks_bp.errorhandler(404)
def not_found(_error):
    return error_response("Not found", 404)
