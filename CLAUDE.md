# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Spendly is a lightweight personal expense tracker built with Flask and SQLite.

---

## Architecture
```
expense-tracker/
├── app.py              # All routes — single file, no blueprints
├── database/
│   ├── __init__.py
│   └── db.py           # SQLite helpers: get_db(), init_db(), seed_db()
├── templates/
│   ├── base.html       # Shared layout — all templates must extend this
│   ├── landing.html    # Homepage
│   ├── login.html      # Login page
│   └── register.html   # Registration page
├── static/
│   ├── css/
│   │   ├── style.css       # Global styles
│   │   └── landing.css     # Landing-page-only styles
│   └── js/
│       └── main.js         # Vanilla JS only
└── requirements.txt
```

### Database schema

**users table**
- `id` (INTEGER PRIMARY KEY) — auto-incrementing user ID
- `name` (TEXT NOT NULL) — user's display name
- `email` (TEXT UNIQUE NOT NULL) — user's email for login
- `password_hash` (TEXT NOT NULL) — bcrypt-hashed password
- `created_at` (TEXT DEFAULT now) — account creation timestamp

**expenses table**
- `id` (INTEGER PRIMARY KEY) — auto-incrementing expense ID
- `user_id` (INTEGER NOT NULL, FK→users.id) — owner of the expense
- `amount` (REAL NOT NULL) — expense amount
- `category` (TEXT NOT NULL) — category (e.g., "Food", "Transport", "Bills")
- `date` (TEXT NOT NULL) — expense date (YYYY-MM-DD format)
- `description` (TEXT) — optional notes
- `created_at` (TEXT DEFAULT now) — when the expense was recorded

**Where things belong:**
- New routes → `app.py` only, no blueprints
- DB logic → `database/db.py` only, never inline in routes
- New pages → new `.html` file extending `base.html`
- Page-specific styles → new `.css` file, not inline `<style>` tags

---

## Code style

- Python: PEP 8, snake_case for all variables and functions
- Templates: Jinja2 with `url_for()` for every internal link — never hardcode URLs
- Route functions: one responsibility only — fetch data, render template, done
- DB queries: always use parameterized queries (`?` placeholders) — never f-strings in SQL
- Error handling: use `abort()` for HTTP errors, not bare `return "error string"`

---

## Tech constraints

- **Flask only** — no FastAPI, no Django, no other web frameworks
- **SQLite only** — no PostgreSQL, no SQLAlchemy ORM, no external DB
- **Vanilla JS only** — no React, no jQuery, no npm packages
- **No new pip packages** — work within `requirements.txt` as-is unless explicitly told otherwise
- Python 3.10+ assumed — f-strings and `match` statements are fine

---

## Subagent Policy
- Always use a builtin explore subagent for codebase exploration 
  before implementing any new feature
- Always use a subagent to verify test results 
  after any implementation
- When asked to plan, delegate codebase research 
  to a subagent before presenting the plan
- always use a builtin plan subagent in plan mode

---

## Commands
```bash
# Setup
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run dev server (port 5001)
python app.py

# Run all tests
pytest

# Run a specific test file
pytest tests/test_foo.py

# Run a specific test by name
pytest -k "test_name"

# Run tests with output visible
pytest -s
```

---

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` only (GET); no POST handling, validation, or account creation yet |
| `GET /login` | Implemented — renders `login.html`; handles POST for login |
| `POST /logout` | Implemented — clears session and redirects to landing |
| `GET /profile` | Placeholder — will display user profile (Step 4) |
| `GET /expenses/add` | Placeholder — will add new expense form (Step 7) |
| `GET /expenses/<id>/edit` | Placeholder — will edit expense form (Step 8) |
| `GET /expenses/<id>/delete` | Placeholder — will delete expense (Step 9) |

**Do not implement a placeholder route unless the active task explicitly targets that step.**

---

## Warnings and things to avoid

- **Never use raw string returns for placeholder routes** — always render a template with the feature implemented
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without explicit approval — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **Always test with the seeded demo user** — email: `demo@spendly.com`, password: `demo123`
- **FK enforcement is enabled** — `get_db()` runs `PRAGMA foreign_keys = ON` on every connection, so foreign key constraints are enforced
- The app runs on **port 5001**, not the Flask default 5000 — don't change this
- **Session-based auth** — `login_required` decorator protects routes; store `user_id` and `user_name` in Flask `session`