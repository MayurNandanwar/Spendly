from datetime import date, timedelta

import database.db as db


def test_get_edit_expense_requires_login(client):
    """Unauthenticated users are redirected to login."""
    resp = client.get("/expenses/1/edit")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_post_edit_expense_requires_login(client):
    """Unauthenticated users are redirected to login on POST."""
    resp = client.post("/expenses/1/edit", data={"amount": "10", "category": "Food", "date": "2026-01-01"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_get_edit_expense_nonexistent_returns_404(auth_client):
    """Trying to edit a non-existent expense returns 404."""
    resp = auth_client.get("/expenses/9999/edit")
    assert resp.status_code == 404


def test_get_edit_expense_wrong_owner_returns_404(auth_client, client):
    """User cannot edit another user's expense - returns 404."""
    # Create a second user and add an expense
    client.post(
        "/register",
        data={"name": "Other User", "email": "other@example.com", "password": "password123"},
    )
    client.post("/login", data={"email": "other@example.com", "password": "password123"})

    resp = client.post(
        "/expenses/add",
        data={"amount": "50.00", "category": "Food", "date": date.today().isoformat(), "description": "Other's expense"},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    # Get the expense ID (should be 1 since demo user's last expense was seeded as id 8)
    # Let's query the database to get the ID
    other_user_id = 2  # Second user created in test
    expenses = db.get_expenses(other_user_id)
    if expenses:
        expense_id = expenses[0]["id"]

        # Now try to edit it as auth_client (demo user, id=1)
        resp = auth_client.get(f"/expenses/{expense_id}/edit")
        assert resp.status_code == 404


def test_get_edit_expense_renders_form_with_values(auth_client):
    """GET /expenses/<id>/edit displays form pre-populated with expense data."""
    # First add an expense
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.50", "category": "Transport", "date": "2026-09-20", "description": "Taxi"},
        follow_redirects=True,
    )

    # Get expenses to find the ID
    expenses = db.get_expenses(1)  # demo user is id 1
    expense = [e for e in expenses if e["description"] == "Taxi"][0]

    # Now access the edit form
    resp = auth_client.get(f"/expenses/{expense['id']}/edit")
    assert resp.status_code == 200
    assert b"Edit Expense" in resp.data
    assert b"25.5" in resp.data
    assert b"Transport" in resp.data
    assert b"2026-09-20" in resp.data
    assert b"Taxi" in resp.data


def test_happy_path_edit_expense_updates_and_redirects(auth_client):
    """Editing with valid data updates the expense and redirects to profile with success message."""
    # Add initial expense
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    # Get the expense ID
    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    # Edit the expense
    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "35.50", "category": "Transport", "date": "2026-09-21", "description": "Taxi ride"},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    # Follow redirect and verify success message
    follow = auth_client.get(resp.headers["Location"])
    assert b"Expense updated successfully" in follow.data

    # Verify the expense was actually updated in database
    updated = db.get_expense_by_id(1, expense["id"])
    assert updated["amount"] == 35.5
    assert updated["category"] == "Transport"
    assert updated["date"] == "2026-09-21"
    assert updated["description"] == "Taxi ride"


def test_edit_expense_missing_amount_shows_error(auth_client):
    """Editing with empty amount shows error."""
    # Add initial expense
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    # Try to edit with empty amount
    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "", "category": "Food", "date": "2026-09-20"},
    )

    assert resp.status_code == 200
    assert b"Please enter an amount" in resp.data

    # Verify expense was NOT updated
    unchanged = db.get_expense_by_id(1, expense["id"])
    assert unchanged["amount"] == 25.0


def test_edit_expense_negative_amount_rejected(auth_client):
    """Editing with negative amount shows error."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "-10", "category": "Food", "date": "2026-09-20"},
    )

    assert resp.status_code == 200
    assert b"greater than 0" in resp.data


def test_edit_expense_non_numeric_amount_rejected(auth_client):
    """Editing with non-numeric amount shows error."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "abc", "category": "Food", "date": "2026-09-20"},
    )

    assert resp.status_code == 200
    assert b"valid number" in resp.data


def test_edit_expense_invalid_category_rejected(auth_client):
    """Editing with invalid category shows error."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "25.00", "category": "InvalidCategory", "date": "2026-09-20"},
    )

    assert resp.status_code == 200
    assert b"select a valid category" in resp.data


def test_edit_expense_missing_date_rejected(auth_client):
    """Editing with missing date shows error."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "25.00", "category": "Food", "date": ""},
    )

    assert resp.status_code == 200
    assert b"enter a date" in resp.data


def test_edit_expense_future_date_rejected(auth_client):
    """Editing with future date shows error."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    future = (date.today() + timedelta(days=1)).isoformat()
    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "25.00", "category": "Food", "date": future},
    )

    assert resp.status_code == 200
    assert b"cannot be in the future" in resp.data


def test_edit_expense_description_over_500_chars_rejected(auth_client):
    """Editing with description > 500 chars shows error."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={
            "amount": "25.00",
            "category": "Food",
            "date": "2026-09-20",
            "description": "x" * 501,
        },
    )

    assert resp.status_code == 200
    assert b"500 characters" in resp.data


def test_edit_expense_validation_failure_preserves_submitted_values(auth_client):
    """When validation fails, form displays submitted values."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "", "category": "Bills", "date": "2026-09-20", "description": "Rent"},
    )

    assert resp.status_code == 200
    assert b'value="Rent"' in resp.data
    assert b"Bills" in resp.data


def test_edit_expense_clear_description(auth_client):
    """Editing to clear the description (empty string) works."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    # Edit to remove description
    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": ""},
        follow_redirects=False,
    )

    assert resp.status_code == 302

    # Verify description is None/empty in database
    updated = db.get_expense_by_id(1, expense["id"])
    assert updated["description"] is None or updated["description"] == ""


def test_edit_expense_all_categories_work(auth_client):
    """Editing with each valid category works."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Test"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Test"][0]

    categories = ("Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other")

    for i, cat in enumerate(categories):
        resp = auth_client.post(
            f"/expenses/{expense['id']}/edit",
            data={"amount": "25.00", "category": cat, "date": "2026-09-20", "description": f"Cat{i}"},
            follow_redirects=False,
        )

        assert resp.status_code == 302

        # Verify in database
        updated = db.get_expense_by_id(1, expense["id"])
        assert updated["category"] == cat


def test_edit_expense_past_date_accepted(auth_client):
    """Editing with a past date is accepted."""
    auth_client.post(
        "/expenses/add",
        data={"amount": "25.00", "category": "Food", "date": "2026-09-20", "description": "Lunch"},
        follow_redirects=True,
    )

    expenses = db.get_expenses(1)
    expense = [e for e in expenses if e["description"] == "Lunch"][0]

    past = (date.today() - timedelta(days=10)).isoformat()
    resp = auth_client.post(
        f"/expenses/{expense['id']}/edit",
        data={"amount": "25.00", "category": "Food", "date": past},
        follow_redirects=False,
    )

    assert resp.status_code == 302

    updated = db.get_expense_by_id(1, expense["id"])
    assert updated["date"] == past
