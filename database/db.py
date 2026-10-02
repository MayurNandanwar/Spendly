import os
import sqlite3
from contextlib import closing
from datetime import date

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SPENDLY_DB_PATH lets tests or deployments point at a different database file.
DB_PATH = os.environ.get("SPENDLY_DB_PATH") or os.path.join(BASE_DIR, "expense_tracker.db")

CATEGORIES = ("Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other")

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"

# (day of month, category, amount, description)
SAMPLE_EXPENSES = (
    (2, "Food", 12.50, "Groceries"),
    (4, "Transport", 45.00, "Monthly bus pass"),
    (5, "Bills", 89.99, "Electricity bill"),
    (9, "Health", 25.00, "Pharmacy"),
    (12, "Entertainment", 15.75, "Movie tickets"),
    (15, "Shopping", 60.20, "New shoes"),
    (18, "Other", 8.00, "Miscellaneous"),
    (21, "Food", 22.30, "Restaurant dinner"),
)

# Columns added to `users` after the original schema. They are defined only
# here and applied by init_db(), so fresh and upgraded databases always match.
USER_MIGRATION_COLUMNS = {
    "refresh_token_hash": "TEXT",
    "refresh_token_expires_at": "TEXT",
}


def get_db():
    """Open a SQLite connection with Row access and foreign keys enforced."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _add_missing_columns(conn, table, columns):
    """Add any of `columns` ({name: sql_type}) that `table` does not have yet.

    Table and column names come from constants in this module, never from
    user input, so building the DDL string here is safe (DDL cannot be
    parameterized).
    """
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, sql_type in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")


def init_db():
    """Create the users and expenses tables if needed and apply column migrations."""
    with closing(get_db()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        _add_missing_columns(conn, "users", USER_MIGRATION_COLUMNS)
        conn.commit()


def _date_filter(user_id, start_date, end_date):
    """Return (where_clause, params) scoping expenses to a user and optional date range."""
    clause = "user_id = ?"
    params = [user_id]
    if start_date:
        clause += " AND date >= ?"
        params.append(start_date)
    if end_date:
        clause += " AND date <= ?"
        params.append(end_date)
    return clause, params


def get_expenses(user_id, start_date=None, end_date=None):
    """Return a user's expenses, optionally filtered to a date range (inclusive)."""
    clause, params = _date_filter(user_id, start_date, end_date)
    query = (
        "SELECT id, amount, category, date, description FROM expenses WHERE "
        + clause
        + " ORDER BY date DESC, id DESC"
    )
    with closing(get_db()) as conn:
        return conn.execute(query, params).fetchall()


def get_expense_summary(user_id, start_date=None, end_date=None):
    """Return total amount and category breakdown for a user's expenses in a date range."""
    clause, params = _date_filter(user_id, start_date, end_date)
    query = (
        "SELECT category, SUM(amount) AS total FROM expenses WHERE "
        + clause
        + " GROUP BY category ORDER BY total DESC"
    )
    with closing(get_db()) as conn:
        rows = conn.execute(query, params).fetchall()
    grand_total = sum(row["total"] for row in rows)
    return grand_total, rows


def add_expense(user_id, amount, category, expense_date, description):
    """Insert a new expense for a user and return its new row id."""
    with closing(get_db()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, category, expense_date, description or None),
        )
        conn.commit()
        return cursor.lastrowid


def get_expense_by_id(user_id, expense_id):
    """Fetch a single expense by ID with ownership verification.

    Args:
        user_id (int): id of the logged-in user
        expense_id (int): ID of expense to fetch

    Returns:
        sqlite3.Row: expense record {id, user_id, amount, category, date, description, created_at}
        None: if expense not found or user doesn't own it
    """
    with closing(get_db()) as conn:
        return conn.execute(
            "SELECT id, user_id, amount, category, date, description, created_at "
            "FROM expenses "
            "WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        ).fetchone()


def update_expense(user_id, expense_id, amount, category, expense_date, description):
    """Update an existing expense with ownership verification.

    Args:
        user_id (int): id of the logged-in user (for ownership check)
        expense_id (int): ID of expense to update
        amount (float): new expense amount
        category (str): new category
        expense_date (str): new date (YYYY-MM-DD)
        description (str): new description (can be empty)

    Returns:
        int: updated expense ID on success
        None: if expense not found or user doesn't own it
    """
    with closing(get_db()) as conn:
        cursor = conn.execute(
            "UPDATE expenses "
            "SET amount = ?, category = ?, date = ?, description = ? "
            "WHERE id = ? AND user_id = ?",
            (amount, category, expense_date, description or None, expense_id, user_id),
        )
        conn.commit()
        return expense_id if cursor.rowcount > 0 else None


def delete_expense(user_id, expense_id):
    """Delete an expense if it belongs to the user. Return rows affected."""
    with closing(get_db()) as conn:
        cursor = conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        )
        conn.commit()
        return cursor.rowcount


def get_user_by_id(user_id):
    """Return a user record by ID, or None if not found."""
    with closing(get_db()) as conn:
        return conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def store_refresh_token(user_id, token_hash, expires_at):
    """Persist the hash and expiry of a user's active refresh token, replacing any previous one."""
    with closing(get_db()) as conn:
        conn.execute(
            "UPDATE users SET refresh_token_hash = ?, refresh_token_expires_at = ? WHERE id = ?",
            (token_hash, expires_at, user_id),
        )
        conn.commit()


def get_user_by_refresh_token_hash(token_hash):
    """Return the user owning this refresh token hash, or None if no match."""
    with closing(get_db()) as conn:
        return conn.execute(
            "SELECT id, name, email, refresh_token_expires_at FROM users WHERE refresh_token_hash = ?",
            (token_hash,),
        ).fetchone()


def clear_refresh_token(user_id):
    """Invalidate a user's stored refresh token (e.g. on logout)."""
    with closing(get_db()) as conn:
        conn.execute(
            "UPDATE users SET refresh_token_hash = NULL, refresh_token_expires_at = NULL WHERE id = ?",
            (user_id,),
        )
        conn.commit()


def seed_db():
    """Insert the demo user and sample expenses for the current month if the demo user is missing.

    Intended for development only; app.py calls it only when demo seeding is enabled.
    """
    with closing(get_db()) as conn:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (DEMO_EMAIL,)).fetchone():
            return

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", DEMO_EMAIL, generate_password_hash(DEMO_PASSWORD)),
        )
        user_id = cursor.lastrowid

        year_month = date.today().strftime("%Y-%m")
        conn.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (user_id, amount, category, f"{year_month}-{day:02d}", description)
                for day, category, amount, description in SAMPLE_EXPENSES
            ],
        )
        conn.commit()
