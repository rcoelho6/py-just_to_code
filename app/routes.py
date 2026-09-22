from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from .models import ValidationError, build_task, task_dto
from .services import TaskNotFoundError, TaskService


def register_routes(app: FastAPI) -> None:
    router = APIRouter()

    @router.post("/tasks", status_code=HTTP_201_CREATED)
    @router.post("/tasks/", status_code=HTTP_201_CREATED)
    async def create(request: Request):
        payload, error = await _read_payload(request)
        if error:
            return error
        try:
            task = build_task(description=payload.get("description"), priority=payload.get("priority"))
            app.state.task_service.create(task)
            return JSONResponse(status_code=HTTP_201_CREATED, content=task_dto(task), headers={"Location": f"/tasks/{task.id}"})
        except ValidationError as exc:
            return _error(f"Erro with status 400: {exc}", HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return _error(f"Unexpected error {exc}", HTTP_500_INTERNAL_SERVER_ERROR)

    @router.put("/tasks/{task_id}", status_code=HTTP_200_OK)
    async def update(task_id: int, request: Request):
        payload, error = await _read_payload(request)
        if error:
            return error
        try:
            task = build_task(description=payload.get("description"), priority=payload.get("priority"), task_id=task_id, updating=True)
            app.state.task_service.update(task)
            return JSONResponse(status_code=HTTP_200_OK, content=task_dto(task))
        except ValidationError as exc:
            return _error(f"Erro with status 400: {exc}", HTTP_400_BAD_REQUEST)
        except TaskNotFoundError as exc:
            return _error(f"Erro with status 404: {exc}", HTTP_404_NOT_FOUND)
        except Exception as exc:
            return _error(f"Unexpected error {exc}", HTTP_500_INTERNAL_SERVER_ERROR)

    app.include_router(router)


async def _read_payload(request: Request) -> tuple[dict[str, Any] | None, JSONResponse | None]:
    if "application/json" not in request.headers.get("content-type", ""):
        return None, _error("Erro with status 400: Request must be JSON", HTTP_400_BAD_REQUEST)
    try:
        payload = await request.json()
    except ValueError:
        return None, _error("Erro with status 400: Invalid JSON body", HTTP_400_BAD_REQUEST)
    if not isinstance(payload, dict):
        return None, _error("Erro with status 400: Invalid JSON body", HTTP_400_BAD_REQUEST)
    return payload, None


def _error(message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"message": message, "status": status})
