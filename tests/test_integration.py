import pytest
from app import app
import database


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    rv = client.get("/")
    assert rv.status_code == 200


def test_active_targets_api(client):
    # Add a target to the test database
    database.get_or_create_target("1.1.1.1")

    rv = client.get("/api/active-targets")
    assert rv.status_code == 200
    targets = rv.get_json()
    assert "1.1.1.1" in targets


def test_get_history_empty(client):
    rv = client.get("/api/history/nonexistent.com")
    assert rv.status_code == 200
    assert rv.get_json() == []


def test_clear_history_api(client):
    address = "8.8.8.8"
    database.get_or_create_target(address)
    rv = client.post(f"/api/clear-history/{address}")
    assert rv.status_code == 200
    assert rv.get_json() == {"status": "success"}
