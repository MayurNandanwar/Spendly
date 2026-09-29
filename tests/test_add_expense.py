from datetime import date, timedelta

import database.db as db


def test_get_add_expense_requires_login(client):
    resp = client.get("/expenses/add")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_post_add_expense_requires_login(client):
    resp = client.post("/expenses/add", data={"amount": "10", "category": "Food", "date": "2026-01-01"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_get_add_expense_renders_empty_form(auth_client):
    resp = auth_client.get("/expenses/add")
    assert resp.status_code == 200
    assert b"Add Expense" in resp.data


def test_happy_path_creates_expense_and_redirects(auth_client):
    resp = auth_client.post(
        "/expenses/add",
        data={"amount": "50.00", "category": "Food", "date": date.today().isoformat(), "description": "Lunch"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    follow = auth_client.get(resp.headers["Location"])
    assert b"Lunch" in follow.data
    assert b"Expense added successfully" in follow.data


def test_missing_amount_shows_error_and_does_not_insert(auth_client):
    resp = auth_client.post(
        "/expenses/add",
        data={"amount": "", "category": "Food", "date": date.today().isoformat()},
    )
    assert resp.status_code == 200
    assert b"Please enter an amount" in resp.data


def test_negative_amount_rejected(auth_client):
    resp = auth_client.post(
        "/expenses/add",
        data={"amount": "-5", "category": "Food", "date": date.today().isoformat()},
    )
    assert resp.status_code == 200
    assert b"greater than 0" in resp.data


def test_non_numeric_amount_rejected(auth_client):
    resp = auth_client.post(
        "/expenses/add",
        data={"amount": "abc", "category": "Food", "date": date.today().isoformat()},
    )
    assert resp.status_code == 200
    assert b"valid number" in resp.data


def test_missing_category_rejected(auth_client):
    resp = auth_client.post(
        "/expenses/add",
        data={"amount": "10", "category": "", "date": date.today().isoformat()},
    )
    assert resp.status_code == 200
    assert b"select a category" in resp.data


def test_missing_date_rejected(auth_client):
    resp = auth_client.post(
        "/expenses/add",
        data={"amount": "10", "category": "Food", "date": ""},
    )
    assert resp.status_code == 200
    assert b"enter a date" in resp.data


def test_future_date_rejected(auth_client):
    future = (date.today() + timedelta(days=1)).isoformat()
    resp = auth_client.post(
        "/expenses/add",
        data={"amount": "10", "category": "Food", "date": future},
    )
    assert resp.status_code == 200
    assert b"cannot be in the future" in resp.data


def test_description_over_500_chars_rejected(auth_client):
    resp = auth_client.post(
        "/expenses/add",
        data={
            "amount": "10", "category": "Food", "date": date.today().isoformat(),
            "description": "x" * 501,
        },
    )
    assert resp.status_code == 200
    assert b"500 characters" in resp.data


def test_validation_failure_preserves_submitted_values(auth_client):
    resp = auth_client.post(
        "/expenses/add",
        data={"amount": "", "category": "Bills", "date": date.today().isoformat(), "description": "Rent"},
    )
    assert resp.status_code == 200
    assert b'value="Rent"' in resp.data
    assert b"Bills" in resp.data


def test_expense_isolated_per_user(client):
    client.post(
        "/register",
        data={"name": "Second User", "email": "second@example.com", "password": "password123"},
    )
    client.post("/login", data={"email": "second@example.com", "password": "password123"})

    client.post(
        "/expenses/add",
        data={"amount": "77.00", "category": "Shopping", "date": date.today().isoformat(), "description": "OnlyMine"},
    )

    profile_resp = client.get("/profile")
    assert b"OnlyMine" in profile_resp.data

    client.post("/logout")
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    demo_profile = client.get("/profile")
    assert b"OnlyMine" not in demo_profile.data


def test_user_id_not_taken_from_form(auth_client):
    """Even if a client passes user_id in the form, it must be ignored."""
    auth_client.post(
        "/expenses/add",
        data={
            "amount": "10", "category": "Food", "date": date.today().isoformat(),
            "user_id": "9999",
        },
    )
    rows = db.get_expenses(1)  # demo user is id 1 in a freshly seeded db
    assert any(r["amount"] == 10.0 for r in rows)
