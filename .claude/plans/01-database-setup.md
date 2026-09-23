# Plan: Implement `database/db.py` (Step 1 — Database Setup)

## Context

`database/db.py` is currently empty. Every other part of the app already depends on it: `app.py` imports `get_db`, `init_db`, `seed_db` and calls `init_db()`/`seed_db()` at startup, and the working `/login` route already calls `get_db()` expecting a `sqlite3.Row`-backed connection with a `users` table. Right now, running `python app.py` would raise an `ImportError`/`AttributeError` because none of these functions exist. This step implements the data layer per `.claude/specs/01-database-setup.md` so the app can actually start and `/login` can work end-to-end. This is step 1 with no dependencies — everything else (profile, expense CRUD) builds on top of it.

Note: this task is **plan + save only** — it does not include implementing the code yet. The deliverable is this plan document saved to `.claude/plans/01-database-setup.md` in the project.

## Approach

Implement three functions in `database/db.py`, using inline SQL (no `schema.sql` file — the spec explicitly lists "no files to create").

**DB file location**: `expense_tracker.db` at the project root — chosen because `.gitignore` already excludes this exact filename (confirmed), so the generated DB won't get committed. Resolve the path relative to `database/db.py`'s own location (`os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`) so it works regardless of CWD.

### `get_db()`
- `sqlite3.connect(DB_PATH)`, set `row_factory = sqlite3.Row`, run `PRAGMA foreign_keys = ON`, return the connection.
- Returns a plain connection (not Flask `g`-cached) — required because the existing `/login` code in `app.py` calls `get_db()` directly and closes it itself in a `finally` block.

### `init_db()`
- Open a connection via `get_db()`, run two `CREATE TABLE IF NOT EXISTS` statements (schema below), commit, close in `finally`. Idempotent — safe to call every startup.

Schema (from spec):
- `users(id PK autoincrement, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')))`
- `expenses(id PK autoincrement, user_id INTEGER NOT NULL REFERENCES users(id), amount REAL NOT NULL, category TEXT NOT NULL, date TEXT NOT NULL, description TEXT, created_at TEXT DEFAULT (datetime('now')))`

### `seed_db()`
- Guard: `SELECT COUNT(*) FROM users` — if `> 0`, return early (no duplicate seeding on repeated runs).
- Insert one demo user: name "Demo User", email `demo@spendly.com`, password hashed via `werkzeug.security.generate_password_hash("demo123")`.
- Capture `cursor.lastrowid` as `user_id`, then `executemany` 8 sample expense rows covering all 7 fixed categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other — Food appears twice to reach 8), with dates built from the current month (`date.today().strftime("%Y-%m")` + fixed day-of-month values `02, 04, 05, 09, 12, 15, 18, 21`) so seed data always falls in "the current month" regardless of when the app first runs.
- All inserts use `?` placeholders — no f-strings in SQL, per project rules.

### No changes needed elsewhere
- `app.py` already imports and calls `init_db()`/`seed_db()` correctly inside `app.app_context()`, and `/login` already matches the connection contract above — verified against the file on disk. **Do not touch `app.py`.**
- `database/__init__.py` stays empty — no changes needed.

## Critical files
- `database/db.py` — implement `get_db()`, `init_db()`, `seed_db()` (currently empty)
- `app.py` — reference only, confirms the connection contract; no edits
- `.gitignore` — confirms `expense_tracker.db` is already the ignored filename
- `.claude/specs/01-database-setup.md` — source spec for schema/behavior

## Verification
1. Run `python app.py` from repo root — should start with no import errors, and `expense_tracker.db` should appear in the project root.
2. Inspect schema: `python -c "import sqlite3; c=sqlite3.connect('expense_tracker.db'); print(c.execute(\"SELECT sql FROM sqlite_master WHERE type='table'\").fetchall())"` — confirms both tables and the FK clause exist.
3. Inspect seed data: `SELECT * FROM users;` (expect 1 row, hashed password, not plaintext) and `SELECT category, date, amount FROM expenses;` (expect 8 rows, all 7 categories present, dates in `YYYY-MM-DD` within current month).
4. FK enforcement: try inserting an expense with a non-existent `user_id` (e.g. 999) — expect `sqlite3.IntegrityError: FOREIGN KEY constraint failed`.
5. Unique email: try inserting a second user with `email='demo@spendly.com'` — expect `sqlite3.IntegrityError: UNIQUE constraint failed`.
6. Browser check: start the app on port 5001, log in at `/login` with `demo@spendly.com` / `demo123`, confirm redirect to `/profile` succeeds.
7. Idempotency: stop and restart `python app.py` again without deleting the DB file — re-check `users`/`expenses` row counts stay at 1 and 8 (not doubled), confirming `seed_db()`'s guard works.

## Deliverable for this task
Once this plan is approved, save this plan's content to `.claude/plans/01-database-setup.md` in the project (implementation of `database/db.py` itself is a separate, later step — not part of this task).
