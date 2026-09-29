import os
import tempfile

import pytest

import app as app_module
import database.db as db


@pytest.fixture
def client(monkeypatch):
    """A Flask test client backed by a fresh, isolated SQLite file per test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)  # let sqlite create it fresh

    monkeypatch.setattr(db, "DB_PATH", path)

    app_module.app.config.update(TESTING=True)
    with app_module.app.app_context():
        db.init_db()
        db.seed_db()

    with app_module.app.test_client() as test_client:
        yield test_client

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def auth_client(client):
    """A test client already logged in as the seeded demo user."""
    client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
        follow_redirects=False,
    )
    return client
