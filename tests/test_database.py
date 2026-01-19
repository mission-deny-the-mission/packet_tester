import pytest
import sqlite3
import os
import database


@pytest.fixture
def test_db(monkeypatch, tmp_path):
    # Create a temporary database file
    db_file = tmp_path / "test_network_data.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))

    # Initialize the database
    database.init_db()

    yield str(db_file)

    # Clean up (tmp_path handles this automatically, but good to be explicit)
    if os.path.exists(db_file):
        os.remove(db_file)


def test_init_db(test_db):
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Check if tables exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='targets'"
    )
    assert cursor.fetchone() is not None

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pings'")
    assert cursor.fetchone() is not None

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hops'")
    assert cursor.fetchone() is not None

    conn.close()


def test_get_or_create_target(test_db):
    address = "8.8.8.8"
    target_id = database.get_or_create_target(address)
    assert target_id is not None

    # Second call should return same ID
    target_id_2 = database.get_or_create_target(address)
    assert target_id == target_id_2


def test_save_ping(test_db):
    target_id = database.get_or_create_target("8.8.8.8")
    database.save_ping(target_id, 14.5, 0.0)

    history = database.get_history("8.8.8.8")
    assert len(history) == 1
    assert history[0]["latency"] == 14.5
    assert history[0]["loss"] == 0.0


def test_active_targets(test_db):
    address = "google.com"
    database.get_or_create_target(address)

    active = database.get_active_targets()
    assert address in active

    database.deactivate_target(address)
    active = database.get_active_targets()
    assert address not in active


def test_save_hop(test_db):
    target_id = database.get_or_create_target("8.8.8.8")
    database.save_hop(target_id, 1, "192.168.1.1", 10.5, 0.0)

    # Verify save_hop worked (we need to check database directly since no getter exists yet)
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hops WHERE target_id = ?", (target_id,))
    hop = cursor.fetchone()
    assert hop["ip"] == "192.168.1.1"
    assert hop["hop_num"] == 1
    conn.close()


def test_clear_target_history(test_db):
    address = "8.8.8.8"
    target_id = database.get_or_create_target(address)
    database.save_ping(target_id, 14.5, 0.0)
    database.save_hop(target_id, 1, "192.168.1.1", 10.5, 0.0)

    database.clear_target_history(address)

    history = database.get_history(address)
    assert len(history) == 0

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM hops WHERE target_id = ?", (target_id,))
    assert cursor.fetchone()[0] == 0
    conn.close()
