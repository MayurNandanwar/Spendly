# Spec: Edit Expense

## 1. Routes & Endpoints

### GET /expenses/<id>/edit
- **Purpose**: Display pre-populated form for editing an existing expense
- **Access**: Logged-in user only; user must own the expense
- **Parameters**: 
  - `id` (URL path parameter) — expense ID from expenses table
- **Response**: 
  - **200 OK**: Render `edit_expense.html` with expense data pre-filled in form
  - **302 Found**: Redirect to `/login` if user not authenticated
  - **404 Not Found**: If expense not found OR user does not own the expense (never reveal 403 to frontend)
- **Template**: `templates/edit_expense.html` extending `base.html`
- **Session**: Requires `user_id` in session

### POST /expenses/<id>/edit
- **Purpose**: Process form submission and update expense in database
- **Access**: Logged-in user only; user must own the expense
- **Parameters**: 
  - `id` (URL path parameter) — expense ID
  - Form data: `amount`, `category`, `date`, `description` (optional)
- **Validation**: 
  - Server-side validation of all fields
  - Return errors dict if validation fails
  - Keep form values on error (pre-fill form)
- **Response**: 
  - **302 Found**: Redirect to `/profile` with flash message "Expense updated successfully" on success
  - **200 OK**: Re-render form with errors dict on validation failure
  - **302 Found**: Redirect to `/login` if user not authenticated
  - **404 Not Found**: If expense not found OR user does not own the expense
- **Database**: Update single row in expenses table, set `updated_at` timestamp if column exists (or skip if not in schema)
- **Flash Message**: "Expense updated successfully" on success

---

## 2. Database Schema & Data Integrity

### No schema changes required
- Expense table already exists with required columns:
  - `id` (INTEGER PRIMARY KEY)
  - `user_id` (INTEGER NOT NULL, FK→users.id)
  - `amount` (REAL NOT NULL)
  - `category` (TEXT NOT NULL)
  - `date` (TEXT NOT NULL, YYYY-MM-DD format)
  - `description` (TEXT, nullable)
  - `created_at` (TEXT DEFAULT current_timestamp)

### New Database Functions in `database/db.py`

#### 1. `get_expense_by_id(user_id, expense_id)`
- **Purpose**: Fetch single expense by ID, verify ownership
- **Signature**: `def get_expense_by_id(user_id, expense_id):`
- **Parameters**:
  - `user_id` (int) — user_id from session
  - `expense_id` (int) — expense ID to fetch
- **Query**:
  ```sql
  SELECT id, user_id, amount, category, date, description, created_at 
  FROM expenses 
  WHERE id = ? AND user_id = ?
  ```
- **Returns**: 
  - Single expense dict: `{'id': ..., 'user_id': ..., 'amount': ..., 'category': ..., 'date': ..., 'description': ..., 'created_at': ...}` on success
  - `None` if expense not found or user doesn't own it
- **Parameterization**: Use `?` placeholders; never f-string SQL

#### 2. `update_expense(user_id, expense_id, amount, category, date, description)`
- **Purpose**: Update expense record with ownership validation
- **Signature**: `def update_expense(user_id, expense_id, amount, category, date, description):`
- **Parameters**:
  - `user_id` (int) — user_id from session
  - `expense_id` (int) — expense ID to update
  - `amount` (float) — new expense amount
  - `category` (str) — new category
  - `date` (str) — new date (YYYY-MM-DD)
  - `description` (str) — new description (can be empty string)
- **Query**:
  ```sql
  UPDATE expenses 
  SET amount = ?, category = ?, date = ?, description = ? 
  WHERE id = ? AND user_id = ?
  RETURNING id
  ```
- **Returns**: 
  - Updated expense ID on success
  - `None` if expense not found or user doesn't own it (integrity check before update)
- **Parameterization**: Use `?` placeholders only
- **Ownership**: WHERE clause includes `user_id = ?` to prevent cross-user updates
- **FK Enforcement**: SQLite PRAGMA foreign_keys = ON (already enabled via `get_db()`)

### Data Integrity Constraints
- Foreign key enforcement via PRAGMA enabled at connection time
- User cannot update expense they don't own (WHERE clause filters)
- Cannot update to non-existent category (no FK on category column, but app validates against EXPENSE_CATEGORIES)
- Amount must be > 0 (app validation)
- Date must be valid YYYY-MM-DD (app validation)
- Description max 500 chars (app validation)

---

## 3. Auth & Authorization

### Authentication (Route Protection)
- Both routes require `@login_required` decorator
- If user not logged in: redirect to `/login` with next URL preserved
- Session must contain `user_id` and `user_name`

### Authorization (Ownership Verification)
- GET /expenses/<id>/edit: 
  - Fetch expense using `get_expense_by_id(session['user_id'], id)`
  - If returns None: abort(404) — never reveal 403
  - Render template with expense data
  
- POST /expenses/<id>/edit:
  - Fetch expense to verify ownership using `get_expense_by_id(session['user_id'], id)`
  - If returns None before processing form: abort(404)
  - If validation fails: stay on same page showing errors
  - If validation passes: call `update_expense(session['user_id'], id, ...)`
  - Check result; if None: abort(404) — expense was deleted between GET and POST
  - Redirect to `/profile` with flash message

### Password Security
- Not applicable (editing existing expense, not changing password)

### CSRF Protection
- All POST forms include hidden `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- Flask session-based CSRF protection via `@app.before_request` (already configured)

### Never Reveal User Not Owner
- Return 404 instead of 403 when user is not the owner
- Example: /expenses/999/edit for expense belonging to another user → 404 (not "forbidden")

---

## 4. Input Validation

### Server-Side Validation (Always)
All validation happens in route handler BEFORE database update.

#### Field: amount
- **Type**: float/decimal
- **Required**: Yes
- **Constraints**:
  - Must be numeric (convertible to float)
  - Must be > 0 (no zero or negative)
  - Max 2 decimal places (e.g., 99.99 valid, 99.999 invalid)
- **Error Message**: "Amount must be a positive number"
- **Stored as**: REAL in database

#### Field: category
- **Type**: string
- **Required**: Yes (dropdown select)
- **Constraints**:
  - Must be one of EXPENSE_CATEGORIES tuple (Food, Transport, Bills, Entertainment, Health, Shopping, Utilities, Other)
  - No free-form text
- **Error Message**: "Please select a valid category"
- **Source**: EXPENSE_CATEGORIES = ('Food', 'Transport', 'Bills', 'Entertainment', 'Health', 'Shopping', 'Utilities', 'Other')

#### Field: date
- **Type**: string (YYYY-MM-DD)
- **Required**: Yes
- **Constraints**:
  - Must be valid date format
  - Can be past or future (no time-based constraint)
- **Error Message**: "Please enter a valid date"
- **Stored as**: TEXT in database (YYYY-MM-DD format)

#### Field: description
- **Type**: string
- **Required**: No (optional)
- **Constraints**:
  - Max 500 characters
  - Can be empty string
- **Error Message**: "Description must be 500 characters or less"
- **Stored as**: TEXT in database (NULL if empty)

### Validation Flow
1. Check all required fields present and non-empty
2. Validate amount: numeric, > 0, max 2 decimals
3. Validate category: in EXPENSE_CATEGORIES
4. Validate date: valid YYYY-MM-DD format
5. Validate description: max 500 chars (if provided)
6. If ANY validation fails:
   - Keep form values in context dict
   - Build errors dict with field-level messages
   - Re-render template with `errors` and form values
   - Do NOT save to database
7. If ALL validation passes:
   - Call `update_expense(...)`
   - Redirect to `/profile` with flash message

### Error Messages in Template
- Use Bootstrap `is-invalid` class on form fields with errors
- Display error text below each field
- Keep user's input values in form fields using template values

### Client-Side Validation
- Input type="number" for amount (convenience only)
- Input type="date" for date (convenience only)
- Validation error handling assumes server-side is the source of truth

---

## 5. Testing & Acceptance Criteria

### Happy Path: Valid Edit
- [ ] User logged in, views GET /expenses/123/edit
- [ ] Form displays with current expense data pre-filled
- [ ] User modifies amount, category, description
- [ ] User submits POST /expenses/123/edit
- [ ] Expense updated in database (SELECT confirms new values)
- [ ] Redirects to /profile with flash "Expense updated successfully"
- [ ] Flash message appears on profile page

### Validation Errors
- [ ] Submit form with empty amount → error shown, form values kept
- [ ] Submit form with amount = -50 → error shown
- [ ] Submit form with amount = "abc" → error shown
- [ ] Submit form with invalid category → error shown
- [ ] Submit form with invalid date → error shown
- [ ] Submit form with description > 500 chars → error shown
- [ ] No database changes when validation fails

### Authorization & Authentication
- [ ] Unauthenticated user tries GET /expenses/123/edit → redirects to /login
- [ ] Unauthenticated user tries POST /expenses/123/edit → redirects to /login
- [ ] User A tries to edit User B's expense → 404 (not 403)
- [ ] Valid user tries to edit non-existent expense → 404
- [ ] Session destroyed between GET and POST, then POST → 404

### Edge Cases
- [ ] Edit expense, change category to all 8 valid categories (each works)
- [ ] Edit expense with description from "x" to empty → saved as empty
- [ ] Edit expense with date to future date → accepted and saved
- [ ] Submit form twice rapidly (race condition) → second request sees current state, updates correctly
- [ ] Delete expense in background, then try to POST /expenses/123/edit → 404

### Database Integrity
- [ ] Foreign key constraint prevents invalid user_id in expense
- [ ] Parameterized queries: grep app.py for SQL injection vulnerabilities (no f-strings in SQL)
- [ ] Update transaction: multiple fields updated atomically (no partial updates)
- [ ] created_at timestamp unchanged after edit (not modified)

### Security
- [ ] CSRF token present in form (name="csrf_token")
- [ ] POST without valid CSRF token → rejected by Flask
- [ ] No user_id visible in form fields (server-side only)
- [ ] SQL queries use ? placeholders (never string interpolation)

### Manual Testing Checklist
```
1. Setup:
   - python app.py (port 5001)
   - Login as demo@spendly.com / demo123

2. Add test expense:
   - GET /expenses/add
   - Fill: $50.00, Food, 2026-09-20, "Lunch at cafe"
   - POST → should redirect to /profile

3. Edit test expense (find its ID in HTML):
   - GET /expenses/<id>/edit
   - Pre-filled form should show all 4 fields
   - Change: $75.00, Transport, 2026-09-21, "Taxi fare"
   - Submit → redirect to /profile, flash message appears

4. Verify in database:
   - SELECT * FROM expenses WHERE id = <id>;
   - amount = 75.0, category = Transport, etc.

5. Test authorization:
   - Logout, login as different user
   - Try GET /expenses/<first-user-id>/edit → 404

6. Test validation:
   - Edit expense, blank amount, submit → error shown
   - Edit expense, amount = -10, submit → error shown
   - Form values preserved in form after error
```

---

## Supporting Details

### Files to Create
- `templates/edit_expense.html` — form template extending `base.html`
  - Identical structure to `add_expense.html` but pre-populated with expense data
  - Submit button says "Update Expense" (not "Add Expense")
  - Form POST to `/expenses/<id>/edit` with hidden `_method` or direct route

### Files to Modify
- `app.py`:
  - Import `get_expense_by_id`, `update_expense` from `database.db`
  - Add route `@app.get('/expenses/<int:id>/edit')` with `@login_required`
  - Add route `@app.post('/expenses/<int:id>/edit')` with `@login_required`
  - Include validation logic, error handling, flash messages
  
- `database/db.py`:
  - Add function `get_expense_by_id(user_id, expense_id)`
  - Add function `update_expense(user_id, expense_id, amount, category, date, description)`

### Files to Reference (Not Modify)
- `templates/add_expense.html` — reuse form structure and styling patterns
- `static/css/dashboard.css` — reuse form styling classes
- `static/css/style.css` — reuse color tokens and font styles

### Flash Messages
| Scenario | Message | Type |
|----------|---------|------|
| Expense updated successfully | "Expense updated successfully" | success |
| Validation error | (errors dict, field-level messages) | error (per field, not flash) |
| Unauthorized access | (404 response, no flash) | — |

### Form Fields in Template
```html
<form method="POST" action="{{ url_for('edit_expense', id=expense.id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  
  <!-- Amount -->
  <div class="form-group">
    <label for="amount">Amount *</label>
    <input type="number" class="form-control {% if errors.get('amount') %}is-invalid{% endif %}" 
           id="amount" name="amount" placeholder="0.00" step="0.01" 
           value="{{ request.form.get('amount', expense.amount) }}" required />
    {% if errors.get('amount') %}<div class="invalid-feedback">{{ errors.amount }}</div>{% endif %}
  </div>

  <!-- Category -->
  <div class="form-group">
    <label for="category">Category *</label>
    <select class="form-control {% if errors.get('category') %}is-invalid{% endif %}" 
            id="category" name="category" required>
      <option value="">Select a category</option>
      {% for cat in EXPENSE_CATEGORIES %}
        <option value="{{ cat }}" {% if request.form.get('category', expense.category) == cat %}selected{% endif %}>{{ cat }}</option>
      {% endfor %}
    </select>
    {% if errors.get('category') %}<div class="invalid-feedback">{{ errors.category }}</div>{% endif %}
  </div>

  <!-- Date -->
  <div class="form-group">
    <label for="date">Date *</label>
    <input type="date" class="form-control {% if errors.get('date') %}is-invalid{% endif %}" 
           id="date" name="date" value="{{ request.form.get('date', expense.date) }}" required />
    {% if errors.get('date') %}<div class="invalid-feedback">{{ errors.date }}</div>{% endif %}
  </div>

  <!-- Description -->
  <div class="form-group">
    <label for="description">Description</label>
    <textarea class="form-control {% if errors.get('description') %}is-invalid{% endif %}" 
              id="description" name="description" rows="3" 
              placeholder="Optional notes">{{ request.form.get('description', expense.description or '') }}</textarea>
    {% if errors.get('description') %}<div class="invalid-feedback">{{ errors.description }}</div>{% endif %}
  </div>

  <button type="submit" class="btn btn-primary">Update Expense</button>
  <a href="{{ url_for('profile') }}" class="btn btn-secondary">Cancel</a>
</form>
```

### Integration Points
- Link to edit form from profile page (expense list row) using `url_for('edit_expense', id=expense.id)`
- Reuse EXPENSE_CATEGORIES from app.py (line 334)
- Reuse form styling from `add_expense.html` and `dashboard.css`
- Reuse `@login_required` decorator pattern
- Follow flash message pattern from add_expense route
- Use `abort(404)` for not found cases (already imported in app.py)
- Use parameterized SQL with `get_db()` (already imported)

### Success Flow (Happy Path)
```
1. User clicks "Edit" on expense in profile
2. GET /expenses/<id>/edit
3. Route fetches expense via get_expense_by_id()
4. If owned by user: render edit_expense.html with pre-filled data
5. If not owned: abort(404)
6. User updates form fields
7. POST /expenses/<id>/edit with form data
8. Route validates all fields
9. If validation passes: update_expense() and redirect to /profile
10. If validation fails: re-render form with errors dict, keep form values
11. Profile page shows flash message "Expense updated successfully"
```

---

## Acceptance Criteria Summary
- [x] Routes: GET /expenses/<id>/edit (display) and POST /expenses/<id>/edit (process)
- [x] Database: get_expense_by_id() and update_expense() functions
- [x] Auth: @login_required on both routes, ownership check (404 if not owner)
- [x] Validation: amount, category, date, description with error messages
- [x] Template: edit_expense.html with pre-filled form
- [x] Testing: happy path, validation errors, authorization, edge cases
- [x] Security: CSRF token, parameterized SQL, no SQL injection
- [x] UX: Flash messages, form value retention on error, clear buttons
