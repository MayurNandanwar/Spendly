import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "expense_tracker.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_expenses(user_id, start_date=None, end_date=None):
    """Return a user's expenses, optionally filtered to a date range (inclusive)."""
    conn = get_db()
    try:
        query = "SELECT id, amount, category, date, description FROM expenses WHERE user_id = ?"
        params = [user_id]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC, id DESC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_expense_summary(user_id, start_date=None, end_date=None):
    """Return total amount and category breakdown for a user's expenses in a date range."""
    conn = get_db()
    try:
        query = "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ?"
        params = [user_id]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " GROUP BY category ORDER BY total DESC"
        rows = conn.execute(query, params).fetchall()
        grand_total = sum(row["total"] for row in rows)
        return grand_total, rows
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing > 0:
            return

        password_hash = generate_password_hash("demo123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash),
        )
        user_id = cursor.lastrowid

        today = date.today()
        year_month = today.strftime("%Y-%m")

        sample_expenses = [
            (user_id, 12.50, "Food", f"{year_month}-02", "Groceries"),
            (user_id, 45.00, "Transport", f"{year_month}-04", "Monthly bus pass"),
            (user_id, 89.99, "Bills", f"{year_month}-05", "Electricity bill"),
            (user_id, 25.00, "Health", f"{year_month}-09", "Pharmacy"),
            (user_id, 15.75, "Entertainment", f"{year_month}-12", "Movie tickets"),
            (user_id, 60.20, "Shopping", f"{year_month}-15", "New shoes"),
            (user_id, 8.00, "Other", f"{year_month}-18", "Miscellaneous"),
            (user_id, 22.30, "Food", f"{year_month}-21", "Restaurant dinner"),
        ]

        conn.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            sample_expenses,
        )
        conn.commit()
    finally:
        conn.close()
