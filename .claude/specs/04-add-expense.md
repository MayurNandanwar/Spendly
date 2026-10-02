
# Spec: Add Expense

## 1. Routes & Endpoints

### `GET /expenses/add`
- **Purpose:** Display the add expense form
- **Access:** Logged-in users only
- **Returns:** Render `templates/add_expense.html` with empty form
- **Status:** 200 OK
- **Auth check:** Redirect to login if not authenticated

### `POST /expenses/add`
- **Purpose:** Validate and save a new expense
- **Access:** Logged-in users only
- **Returns:** On success, redirect to `/profile` (302); on error, re-render form with validation messages and submitted values
- **Status:** 200 (form re-render) or 302 (redirect on success)
- **Auth check:** Redirect to login if not authenticated
- **Form data:**
  - `amount` (required, float)
  - `category` (required, text)
  - `date` (required, YYYY-MM-DD)
  - `description` (optional, text)
- **Flash message on success:** "Expense added successfully"
- **Flash message on error:** Display per-field validation errors

---

## 2. Database Schema & Data Integrity

### Existing `expenses` table (no changes needed)
```sql
CREATE TABLE expenses (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  category TEXT NOT NULL,
  date TEXT NOT NULL,
  description TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Constraints & Integrity
- `user_id`: Foreign key to `users.id`, ON DELETE CASCADE (if user deleted, all their expenses deleted)
- `amount`: REAL, must be > 0 (checked in validation, not SQL constraint)
- `category`: TEXT, non-empty (checked in validation)
- `date`: TEXT YYYY-MM-DD format, must be today or earlier (checked in validation)
- `description`: TEXT, optional, max 500 chars (checked in validation)
- `created_at`: Auto-set to current timestamp

### No schema changes required
- Use existing `expenses` table as-is
- Foreign key enforcement enabled via `PRAGMA foreign_keys = ON` in `get_db()`

---

## 3. Auth & Authorization

### Authentication
- Route protected with `@login_required` decorator
- User must be logged in; store `user_id` and `user_name` in Flask `session`
- Unauthenticated user: redirect to `/login`

### Authorization
- Expense is owned by the currently logged-in user (session `user_id`)
- On insert, set `user_id = session['user_id']` from the database function, not from form input
- Never trust `user_id` from form submission

### Session-based auth
- Use existing session storage: `session['user_id']` (set by login route)
- CSRF protection: Flask's `WTForms` (if used) or manual CSRF token on form submission
- For now, use session-based implicit CSRF (Flask default)

---

## 4. Input Validation

### Server-side validation (required)
All validation happens on the server before inserting into database.

#### `amount` (required)
- Must be provided (not empty)
- Must be a valid number (float or int)
- Must be > 0 (positive amount only)
- Error: "Amount must be greater than 0"

#### `category` (required)
- Must be provided (not empty)
- Must be a string
- Max 50 characters
- Allowed values: "Food", "Transport", "Bills", "Entertainment", "Health", "Other" (or open-ended)
- Error: "Category is required" or "Invalid category"

#### `date` (required)
- Must be provided (not empty)
- Must be valid YYYY-MM-DD format
- Must be today or earlier (no future dates)
- Error: "Date must be in YYYY-MM-DD format" or "Date cannot be in the future"

#### `description` (optional)
- If provided, max 500 characters
- Can be empty
- Error: "Description cannot exceed 500 characters"

### Client-side validation (optional)
- HTML5 input `type="number"` for amount (min="0.01", step="0.01")
- HTML5 input `type="date"` for date (max today's date)
- Provides user feedback but is NOT authoritative
- Server always re-validates

### Validation flow
1. Receive form data from POST request
2. Validate each field
3. If validation fails:
   - Store errors dict: `{"field": "error message"}`
   - Keep form values in template context
   - Re-render form with `<span class="error">{{ errors.field }}</span>`
   - HTTP 200 (no redirect)
4. If validation passes:
   - Insert into database via `database/db.py` function
   - Flash success message
   - Redirect to `/profile` (HTTP 302)

---

## 5. Testing & Acceptance Criteria

### Happy path
- [ ] GET `/expenses/add` renders form with empty fields
- [ ] POST `/expenses/add` with valid data:
  - Amount: 50.00, Category: "Food", Date: today, Description: "Lunch"
  - Database receives the row with correct `user_id`
  - User redirected to `/profile` (HTTP 302)
  - Flash message: "Expense added successfully"
  - Expense appears in user's expense list on `/profile`

### Validation errors
- [ ] POST with missing `amount`: form re-renders with error message, form values preserved
- [ ] POST with `amount` = -10: form re-renders with error "Amount must be greater than 0"
- [ ] POST with `amount` = "abc": form re-renders with error
- [ ] POST with missing `category`: form re-renders with error
- [ ] POST with missing `date`: form re-renders with error
- [ ] POST with date in future (e.g., 2026-12-31): form re-renders with error
- [ ] POST with `description` > 500 chars: form re-renders with error
- [ ] No data inserted into database on any validation error

### Authorization
- [ ] Unauthenticated user accessing `GET /expenses/add`: redirect to `/login`
- [ ] Unauthenticated user POST to `/expenses/add`: redirect to `/login`
- [ ] Logged-in user A adds expense, user B cannot see it (only in user A's list on `/profile`)

### Database integrity
- [ ] Expense row inserted with correct `user_id` from session
- [ ] Foreign key constraint enforced (user_id points to existing user)
- [ ] `created_at` timestamp auto-set correctly
- [ ] Amount stored as REAL (decimal)
- [ ] Category stored exactly as entered
- [ ] Date stored in YYYY-MM-DD format

### Edge cases
- [ ] Amount with many decimal places (99.999): stored correctly
- [ ] Amount as integer (50): converted to float (50.0), stored correctly
- [ ] Description with special chars (quotes, <, >, &): stored and displayed safely
- [ ] Description empty: allowed (optional field)
- [ ] Multiple expenses added in sequence: all appear on `/profile`, all have correct user_id

### Security
- [ ] CSRF: no explicit CSRF token needed (Flask session-based implicit)
- [ ] SQL injection: parameterized queries in `database/db.py` with `?` placeholders
- [ ] XSS: template escaping (Jinja2 auto-escapes by default)
- [ ] Expense amount never comes from URL, only form POST
- [ ] User cannot set their own `user_id` in form (set server-side only)

### Manual testing checklist
1. Run dev server: `python app.py`
2. Register test account or log in as `demo@spendly.com` / `demo123`
3. Navigate to `/expenses/add`
4. Test happy path: fill form with valid data, submit, verify redirect and flash message
5. Test validation: submit invalid amounts, missing fields, future dates
6. Verify expense appears on `/profile` dashboard
7. Log out, try to access `/expenses/add`, verify redirect to login
8. Test with another user account to verify data isolation

### Acceptance checklist
- [ ] Route returns correct HTTP status (200, 302, redirect)
- [ ] User can only add expenses for themselves
- [ ] Form validation works on server (all fields validated)
- [ ] Database constraints enforced (foreign key, data types)
- [ ] Tests pass: `pytest tests/test_add_expense.py`
- [ ] Flash messages appear on success/error
- [ ] POST request redirects (prevents resubmit on F5)
- [ ] All links use `url_for()`, not hardcoded
- [ ] Form renders with pre-filled values on validation error
- [ ] Amount accepts decimals (e.g., 19.99)
- [ ] Date picker defaults to today (HTML5)
- [ ] Description is optional

---

## Supporting Details

### Files to Create
- `templates/add_expense.html` — Form to add a new expense (extends `base.html`)
- `tests/test_add_expense.py` — Test suite (happy path, validation, auth, DB integrity)

### Files to Modify
- `app.py` — Add `GET /expenses/add` and `POST /expenses/add` route handlers
- `database/db.py` — Add `add_expense(user_id, amount, category, date, description)` function
  - Validates input (all 5 fields)
  - Inserts into `expenses` table
  - Returns success/error tuple
  - Uses parameterized queries

### Flash Messages
- **Success:** "Expense added successfully" (on redirect to `/profile`)
- **Validation errors:**
  - "Amount must be greater than 0"
  - "Amount is required"
  - "Amount must be a valid number"
  - "Category is required"
  - "Invalid category"
  - "Date is required"
  - "Date must be in YYYY-MM-DD format"
  - "Date cannot be in the future"
  - "Description cannot exceed 500 characters"

### Template structure (`add_expense.html`)
```html
{% extends "base.html" %}

{% block title %}Add Expense{% endblock %}

{% block content %}
<div class="container">
  <h1>Add Expense</h1>
  
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        <div class="alert alert-{{ category }}">{{ message }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <form method="post" class="expense-form">
    <div class="form-group">
      <label for="amount">Amount *</label>
      <input 
        type="number" 
        id="amount" 
        name="amount" 
        value="{{ form.amount or '' }}"
        min="0.01" 
        step="0.01"
        required
        placeholder="0.00"
      >
      {% if errors and errors.amount %}
        <span class="error">{{ errors.amount }}</span>
      {% endif %}
    </div>

    <div class="form-group">
      <label for="category">Category *</label>
      <select id="category" name="category" required>
        <option value="">Select a category</option>
        <option value="Food" {% if form.category == 'Food' %}selected{% endif %}>Food</option>
        <option value="Transport" {% if form.category == 'Transport' %}selected{% endif %}>Transport</option>
        <option value="Bills" {% if form.category == 'Bills' %}selected{% endif %}>Bills</option>
        <option value="Entertainment" {% if form.category == 'Entertainment' %}selected{% endif %}>Entertainment</option>
        <option value="Health" {% if form.category == 'Health' %}selected{% endif %}>Health</option>
        <option value="Other" {% if form.category == 'Other' %}selected{% endif %}>Other</option>
      </select>
      {% if errors and errors.category %}
        <span class="error">{{ errors.category }}</span>
      {% endif %}
    </div>

    <div class="form-group">
      <label for="date">Date *</label>
      <input 
        type="date" 
        id="date" 
        name="date" 
        value="{{ form.date or '' }}"
        required
      >
      {% if errors and errors.date %}
        <span class="error">{{ errors.date }}</span>
      {% endif %}
    </div>

    <div class="form-group">
      <label for="description">Description</label>
      <textarea 
        id="description" 
        name="description" 
        placeholder="Optional notes..."
        maxlength="500"
      >{{ form.description or '' }}</textarea>
      {% if errors and errors.description %}
        <span class="error">{{ errors.description }}</span>
      {% endif %}
    </div>

    <div class="form-actions">
      <button type="submit" class="btn btn-primary">Add Expense</button>
      <a href="{{ url_for('profile') }}" class="btn btn-secondary">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}
```

### Integration notes
- After user adds an expense, they are redirected to `/profile`
- On `/profile`, the new expense should appear in the expense list immediately
- Expense filters on `/profile` should respect the new expense (appears in correct date range, category filter)
- No changes needed to authentication flow or database schema

---

## Summary

**Step:** 04
**Feature:** Add Expense
**File:** `docs/specs/04-add-expense.md`

5 Pillars:
1. ✅ **Routes:** GET and POST `/expenses/add` with redirects and error handling
2. ✅ **Database:** Use existing `expenses` table; no schema changes
3. ✅ **Auth:** Logged-in users only; `user_id` set server-side
4. ✅ **Validation:** All 5 fields validated on server; form re-renders on error
5. ✅ **Testing:** Happy path, validation, auth, DB integrity, edge cases, security

**Ready for implementation**
