"""Tests for the delete expense feature (Step 9)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database.db import get_db, add_expense, get_expenses
from werkzeug.security import generate_password_hash
import sqlite3


def setup_test_db():
    """Initialize test database with test users and expenses."""
    app.config['TESTING'] = True
    conn = get_db()

    # Create test users
    password_hash = generate_password_hash("testpass")

    # User 1: test_user_1
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User 1", "user1@test.com", password_hash)
    )

    # User 2: test_user_2
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User 2", "user2@test.com", password_hash)
    )

    conn.commit()

    # Get user IDs
    user1 = conn.execute("SELECT id FROM users WHERE email = ?", ("user1@test.com",)).fetchone()
    user2 = conn.execute("SELECT id FROM users WHERE email = ?", ("user2@test.com",)).fetchone()

    conn.close()

    return user1["id"], user2["id"]


def test_delete_expense_requires_login():
    """Test that unauthenticated users are redirected to login."""
    with app.test_client() as client:
        response = client.get('/expenses/1/delete')
        assert response.status_code == 302
        assert '/login' in response.location


def test_delete_expense_page_not_found():
    """Test that accessing non-existent expense returns 404."""
    with app.test_client() as client:
        # Login first
        response = client.post('/login', data={
            'email': 'demo@spendly.com',
            'password': 'demo123'
        }, follow_redirects=False)

        # Try to access non-existent expense
        response = client.get('/expenses/99999/delete')
        assert response.status_code == 404


def test_delete_expense_page_shows_details():
    """Test that delete confirmation page displays expense details."""
    with app.test_client() as client:
        # Login
        response = client.post('/login', data={
            'email': 'demo@spendly.com',
            'password': 'demo123'
        }, follow_redirects=False)

        # Get first expense
        conn = get_db()
        expense = conn.execute(
            "SELECT id FROM expenses ORDER BY id LIMIT 1"
        ).fetchone()
        conn.close()

        if expense:
            # Access delete confirmation page
            response = client.get(f'/expenses/{expense["id"]}/delete')
            assert response.status_code == 200
            assert b'Delete Expense' in response.data
            assert b'Confirm Delete' in response.data


def test_delete_expense_removes_from_database():
    """Test that POST to delete endpoint removes expense from database."""
    with app.test_client() as client:
        # Login
        client.post('/login', data={
            'email': 'demo@spendly.com',
            'password': 'demo123'
        }, follow_redirects=False)

        # Get initial expense count
        conn = get_db()
        initial_count = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = (SELECT id FROM users WHERE email = ?)",
            ("demo@spendly.com",)
        ).fetchone()[0]

        # Get first expense ID
        expense = conn.execute(
            "SELECT id FROM expenses WHERE user_id = (SELECT id FROM users WHERE email = ?) LIMIT 1",
            ("demo@spendly.com",)
        ).fetchone()
        conn.close()

        if expense:
            expense_id = expense["id"]

            # Delete the expense
            response = client.post(f'/expenses/{expense_id}/delete', follow_redirects=False)
            assert response.status_code == 302
            assert response.location.endswith('/profile')

            # Verify expense is deleted
            conn = get_db()
            deleted_expense = conn.execute(
                "SELECT id FROM expenses WHERE id = ? AND user_id = (SELECT id FROM users WHERE email = ?)",
                (expense_id, "demo@spendly.com")
            ).fetchone()
            conn.close()

            assert deleted_expense is None, "Expense should be deleted from database"


def test_delete_other_users_expense_returns_404():
    """Test that user cannot delete another user's expense."""
    with app.test_client() as client:
        # Setup: Create two users
        user1_id, user2_id = setup_test_db()

        # Add expense for user 1
        add_expense(user1_id, 50.00, "Food", "2024-01-15", "Test expense")

        # Get expense ID
        conn = get_db()
        expense = conn.execute(
            "SELECT id FROM expenses WHERE user_id = ? LIMIT 1",
            (user1_id,)
        ).fetchone()
        conn.close()

        if expense:
            expense_id = expense["id"]

            # Login as user 2
            client.post('/login', data={
                'email': 'user2@test.com',
                'password': 'testpass'
            }, follow_redirects=False)

            # Try to delete user 1's expense
            response = client.get(f'/expenses/{expense_id}/delete')
            assert response.status_code == 404


def test_delete_expense_flash_message():
    """Test that success flash message appears after deletion."""
    with app.test_client() as client:
        # Login
        response = client.post('/login', data={
            'email': 'demo@spendly.com',
            'password': 'demo123'
        }, follow_redirects=True)

        # Get first expense
        conn = get_db()
        expense = conn.execute(
            "SELECT id FROM expenses WHERE user_id = (SELECT id FROM users WHERE email = ?) LIMIT 1",
            ("demo@spendly.com",)
        ).fetchone()
        conn.close()

        if expense:
            expense_id = expense["id"]

            # Delete expense and follow redirect
            response = client.post(f'/expenses/{expense_id}/delete', follow_redirects=True)
            assert response.status_code == 200
            assert b'Expense deleted successfully' in response.data


if __name__ == "__main__":
    print("Running delete expense tests...")
    test_delete_expense_requires_login()
    print("[PASS] Login requirement test passed")

    test_delete_expense_page_not_found()
    print("[PASS] Not found test passed")

    test_delete_expense_page_shows_details()
    print("[PASS] Page details display test passed")

    test_delete_expense_removes_from_database()
    print("[PASS] Database deletion test passed")

    test_delete_other_users_expense_returns_404()
    print("[PASS] Authorization test passed")

    test_delete_expense_flash_message()
    print("[PASS] Flash message test passed")

    print("\nAll tests passed!")
