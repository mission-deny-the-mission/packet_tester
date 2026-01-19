import pytest
from app import app, socketio, active_tasks
import database


@pytest.fixture
def socket_client():
    app.config["TESTING"] = True
    client = socketio.test_client(app)
    yield client
    if client.is_connected():
        client.disconnect()


def test_start_stop_test(socket_client, mocker):
    # Mock eventlet.spawn to avoid starting background threads
    mock_spawn = mocker.patch("eventlet.spawn")

    target = "8.8.8.8"
    socket_client.emit("start_test", {"target": target})

    # Check if target is in active_tasks
    # Note: request.sid in app.py will be different, but we can check if it's populated
    assert len(active_tasks) > 0
    sid = list(active_tasks.keys())[0]
    assert target in active_tasks[sid]
    assert mock_spawn.call_count == 2

    # Test stop_test
    socket_client.emit("stop_test", {"target": target})
    assert target not in active_tasks[sid]


def test_disconnect(socket_client, mocker):
    mocker.patch("eventlet.spawn")
    socket_client.emit("start_test", {"target": "8.8.8.8"})
    sid = list(active_tasks.keys())[0]
    assert sid in active_tasks

    socket_client.disconnect()
    # After disconnect, the sid should be removed from active_tasks
    assert sid not in active_tasks


def test_start_test_no_target(socket_client, mocker):
    mock_spawn = mocker.patch("eventlet.spawn")
    socket_client.emit("start_test", {})
    assert mock_spawn.call_count == 0
