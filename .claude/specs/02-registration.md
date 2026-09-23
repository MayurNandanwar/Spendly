# Spec: Registration

## Overview
Implement user account registration with full form validation and account creation. Users sign up with their name, email, and password. The feature validates all inputs (name length, email format and uniqueness, password strength), hashes passwords securely with werkzeug, and creates new user accounts in the database. Registration is a prerequisite for login and all expense-tracking features.

## Depends on
- Step 1: Database Setup (users table with email uniqueness constraint, password hashing capability)

## Routes
- `POST /register` — handle form submission, validate input, create account — public

## Database changes
No database changes. Uses existing `users` table schema from Step 1.

## Templates
- **Modify:** `templates/register.html` — display per-field validation errors (below each field), fix hardcoded `action="/register"` to use `url_for()`, preserve submitted name/email values on validation failure

## Files to change
- `app.py` — add POST handler to `/register` route with input validation and user creation
- `templates/register.html` — fix form action, add per-field error display
- `static/css/style.css` — add `.field-error` CSS class for error text styling

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite with `get_db()`
- Parameterized queries only — use `?` placeholders, never f-strings in SQL
- Passwords hashed with werkzeug `generate_password_hash()`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Email validation: regex pattern `^[^@\s]+@[^@\s]+\.[^@\s]+$`
- Name: minimum 2 characters, maximum 100 characters (after strip)
- Email: stripped and lowercased before validation and storage
- Password: minimum 8 characters, maximum 128 characters
- Handle `sqlite3.IntegrityError` on insert as duplicate-email guard
- On success: flash "Account created — please sign in." and redirect to `/login`
- On failure: render form with per-field error messages, preserving name and email input (never password)
- Redirect already-logged-in users to `/profile` when accessing `/register`
- Duplicate-email error message auto-dismisses (fades out) after 3–4 seconds; all other field errors persist until the next form submission

## Exception handling
- Every `get_db()` connection opened in the route must be closed in a `finally` block, whether the query succeeds, finds no error, or raises — no connection is ever left open on an error path.
- The duplicate-email check has two layers, since a check-then-insert has a race window between two concurrent requests:
  1. **Pre-check**: `SELECT id FROM users WHERE email = ?` before attempting the insert — catches the common case and gives a fast, friendly error without touching the `users` table.
  2. **Insert-time guard**: the `INSERT` is wrapped in `try/except sqlite3.IntegrityError/finally` — if two requests race past the pre-check simultaneously, the database's `UNIQUE` constraint on `email` still rejects the second insert, and that `IntegrityError` is caught and converted to the same user-facing "account already exists" error rather than a 500.
- No other database exceptions (e.g. `sqlite3.OperationalError` for a locked/corrupt DB) are caught in this feature — those are unexpected infrastructure failures, not user input errors, and should surface as a 500 rather than being silently swallowed or mis-reported as a validation error.
- Both the pre-check path and the `IntegrityError` path set the same `errors["email"]` message and mark the error as the duplicate-email case (see auto-dismiss behavior above), so the user sees identical, consistent feedback regardless of which layer caught it.

## Definition of done
- [ ] User can navigate to `/register` and see a registration form with name, email, password fields
- [ ] Form validates name (2–100 chars after strip)
- [ ] Form validates email (valid format, unique in database)
- [ ] Form validates password (8–128 chars)
- [ ] Per-field error messages display below the appropriate field on validation failure
- [ ] Name and email input values are preserved when validation fails
- [ ] Successful registration creates a user with bcrypt-hashed password
- [ ] Successful registration redirects to `/login` with success flash message
- [ ] Duplicate email submission (via pre-check or IntegrityError race) shows an identical email-specific validation error
- [ ] Duplicate-email error message auto-dismisses after 3–4 seconds; other field errors do not
- [ ] Logged-in users accessing `/register` are redirected to `/profile`
- [ ] All form inputs are stripped of whitespace; email is lowercased
- [ ] No plaintext passwords are stored or logged
- [ ] All DB connections are closed via `finally` on every code path, including error paths
