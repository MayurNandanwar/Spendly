#!/usr/bin/env python
"""Check what expenses exist in the database."""

from app import app
from database.db import get_db

def check_expenses():
    """Check all expenses in database."""
    with app.app_context():
        conn = get_db()

        # Get all users
        users = conn.execute("SELECT id, name, email FROM users").fetchall()
        print("Users in database:")
        for user in users:
            print(f"  ID {user['id']}: {user['name']} ({user['email']})")

        # Get all expenses
        expenses = conn.execute("""
            SELECT id, user_id, amount, category, date, description
            FROM expenses
            ORDER BY id
        """).fetchall()

        print(f"\nExpenses in database ({len(expenses)} total):")
        for exp in expenses:
            print(f"  ID {exp['id']}: {exp['category']} ₹{exp['amount']} on {exp['date']} (user_id={exp['user_id']})")

        conn.close()

if __name__ == '__main__':
    check_expenses()
