import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.models import Task


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}"})


@pytest.fixture
def client(app):
    return TestClient(app)


def test_create_returns_201_location_and_persists(client):
    response = client.post("/tasks", json={"description": "created", "priority": 5})
    assert response.status_code == 201
    assert response.headers["Location"] == "/tasks/1"
    assert response.json() == {"description": "created", "priority": 5}
    task = Task.get_by_id(1)
    assert task.description == "created"
    assert task.priority == 5


def test_create_accepts_trailing_slash(client):
    response = client.post("/tasks/", json={"description": "created", "priority": 5})
    assert response.status_code == 201


@pytest.mark.parametrize(
    "payload",
    [{"priority": 5}, {"description": ""}, {"description": "created"}, {"description": "created", "priority": -1}],
)
def test_create_invalid_payload_returns_400(client, payload):
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    assert response.json()["status"] == 400


def test_update_returns_200(client):
    client.post("/tasks", json={"description": "old", "priority": 1})
    response = client.put("/tasks/1", json={"description": "new", "priority": 2})
    assert response.status_code == 200
    assert response.json() == {"description": "new", "priority": 2}


def test_update_not_found_returns_404(client):
    response = client.put("/tasks/1", json={"description": "new", "priority": 2})
    assert response.status_code == 404
    assert response.json() == {"message": "Erro with status 404: ID not found", "status": 404}


def test_update_same_values_is_successful(client):
    client.post("/tasks", json={"description": "same", "priority": 1})
    response = client.put("/tasks/1", json={"description": "same", "priority": 1})
    assert response.status_code == 200


@pytest.mark.parametrize("method", ["get", "delete"])
def test_unimplemented_methods_are_not_available(client, method):
    response = getattr(client, method)("/tasks/1")
    assert response.status_code == 405


def test_post_with_id_is_not_allowed(client):
    response = client.post("/tasks/1", json={"description": "created", "priority": 5})
    assert response.status_code == 405
