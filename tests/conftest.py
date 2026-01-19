import pytest
import os
import database


@pytest.fixture(autouse=True)
def use_test_db(monkeypatch, tmp_path):
    db_file = tmp_path / "integration_test.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()
    yield
