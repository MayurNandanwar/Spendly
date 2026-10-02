# Spec: Delete Expense

## 1. Routes & Endpoints

### GET /expenses/<id>/delete
- **Purpose:** Display a confirmation dialog/page before deleting an expense
- **Authentication:** Required (@login_required)
- **Access:** Owner-only (user must own the expense; otherwise return 404)
- **Response:** 
  - 200 OK — Render `delete_expense_confirmation.html` with expense details
  - 404 Not Found — Expense does not exist or user is not the owner
- **What it renders:** Confirmation page showing expense details (category, amount, date, description) with "Cancel" and "Confirm Delete" buttons

### POST /expenses/<id>/delete
- **Purpose:** Process the expense deletion
- **Authentication:** Required (@login_required)
- **Access:** Owner-only (user must own the expense; otherwise return 404)
- **Request body:** Standard form submission (CSRF token in hidden field)
- **Response:**
  - 302 Redirect — On success, redirect to `/profile` with flash message
  - 404 Not Found — Expense does not exist or user is not the owner
  - 400 Bad Request — If POST processing fails (e.g., database error)
- **Flash message on success:** "Expense deleted successfully"

---

## 2. Database Schema & Data Integrity

### No schema changes required
The `expenses` table already has:
- `id` (INTEGER PRIMARY KEY) — expense ID
- `user_id` (INTEGER NOT NULL, FK→users.id) — owner of the expense
- Other fields (amount, category, date, description, created_at)

### Deletion approach: Hard delete
- Use `DELETE FROM expenses WHERE id = ? AND user_id = ?` to permanently remove the expense
- Foreign key constraints are already enforced (PRAGMA foreign_keys = ON)
- No cascade needed: expenses table has no dependents
- Data integrity: Parameterized query ensures SQL injection prevention and constraint enforcement

### Query validation
- Always check both `id` and `user_id` in WHERE clause to prevent unauthorized access
- Verify expense exists BEFORE showing confirmation page (GET request)
- Verify expense exists BEFORE deleting (POST request)
- Use parameterized queries with `?` placeholders

---

## 3. Auth & Authorization

### Authentication
- All routes require `@login_required` decorator
- Unauthenticated users are redirected to `/login`

### Authorization (ownership check)
- User can only delete their own expenses
- Check: `WHERE id = ? AND user_id = g.current_user["id"]`
- **Strategy:** Return 404 for unauthorized access (not 403) to avoid revealing expense existence

### Implementation details
- GET /expenses/<id>/delete: Fetch expense; if not found OR user_id ≠ current_user, abort(404)
- POST /expenses/<id>/delete: Fetch expense; verify ownership; if check fails, abort(404); otherwise delete
- CSRF protection: POST form includes hidden CSRF token (Flask session-based by default)

---

## 4. Input Validation

### GET /expenses/<id>/delete
- Validate `id` parameter:
  - Must be a positive integer (Flask routing with `<int:id>` handles this)
  - Fetch expense by `id` + `user_id` combination
  - If not found, abort(404)

### POST /expenses/<id>/delete
- Validate `id` parameter (same as GET)
- Verify expense exists and is owned by current user
- If check fails, abort(404)
- If database delete operation fails, abort(400) or redirect with error flash message

### No additional user input
- Deletion is non-reversible; confirmation page is the only UX safeguard
- No form fields to validate (user confirms via button click)

---

## 5. Testing & Acceptance Criteria

### Happy path
- [ ] Logged-in user views their own expense deletion confirmation page (GET 200)
- [ ] Logged-in user clicks "Confirm Delete" button and expense is removed (POST 302 redirect)
- [ ] User is redirected to `/profile` after deletion
- [ ] Flash message "Expense deleted successfully" appears
- [ ] Expense no longer appears in expense list on `/profile`
- [ ] Expense is permanently removed from database

### Authorization / Security
- [ ] Unauthenticated user trying to access `/expenses/<id>/delete` is redirected to login
- [ ] User A cannot delete User B's expense (returns 404)
- [ ] Attempting to delete non-existent expense returns 404
- [ ] POST request without valid CSRF token is rejected (Flask handles)

### Edge cases
- [ ] Deleting last expense in a category still updates totals correctly
- [ ] Deleting an expense updates summary totals on dashboard
- [ ] Clicking "Cancel" button returns to `/profile` without deleting
- [ ] Rapid successive deletes (race condition) are prevented by database integrity

### Database integrity
- [ ] Foreign key constraints remain intact after deletion
- [ ] Expense ID is never reused (AUTOINCREMENT behavior)
- [ ] Category totals recalculate correctly after deletion

### Acceptance checklist
- [ ] Route returns correct HTTP status codes (200, 302, 404)
- [ ] User cannot delete other users' expenses
- [ ] Database constraints prevent invalid deletions
- [ ] Flash messages appear on success and error
- [ ] POST redirects to profile (no resubmit on refresh)
- [ ] Confirmation page displays all relevant expense details
- [ ] All links use `url_for()`, not hardcoded URLs
- [ ] Tests pass: `pytest tests/test_delete_expense.py`
- [ ] Manual testing with seeded demo user (demo@spendly.com / demo123)

---

## Supporting Details

### Files to Create
1. **templates/delete_expense_confirmation.html**
   - Extends `base.html`
   - Display expense details: category, amount, date, description
   - Warning message: "This action cannot be undone"
   - Two buttons: "Cancel" (link to /profile) and "Confirm Delete" (submit form)
   - Form method: POST to `/expenses/<id>/delete`

### Files to Modify
1. **app.py**
   - Replace placeholder at line 400-402
   - Implement `GET /expenses/<id>/delete` to fetch and display confirmation
   - Implement `POST /expenses/<id>/delete` to process deletion
   - Add authorization check (user_id match)
   - Add flash messages

2. **database/db.py**
   - Add new function `delete_expense(user_id, expense_id)` 
   - Executes: `DELETE FROM expenses WHERE id = ? AND user_id = ?`
   - Returns number of rows deleted (verify deletion occurred)

3. **templates/profile.html**
   - Add delete button/link to each expense row (near line 73-85)
   - Link text: "Delete" or icon button
   - Link target: `url_for('delete_expense', id=expense.id)`
   - Style: Use existing `btn-danger` class for visibility

### Flash Messages
- **Success:** "Expense deleted successfully" (category: success)
- **Error (not found):** 404 page handles this (Flask default)
- **Error (unauthorized):** 404 page handles this (Flask default)

### Integration
- Delete button visible on each expense in `/profile` page
- Clicking delete button navigates to confirmation page
- Confirmation page displays expense details with two options:
  - Cancel → returns to `/profile` without deletion
  - Confirm Delete → POSTs to `/expenses/<id>/delete`, deletes expense, redirects to `/profile`
- Dashboard totals are recalculated on `/profile` page load (no client-side cache)

### UX Flow
1. User views `/profile` page with expense list
2. User clicks "Delete" button on an expense row
3. Browser navigates to `GET /expenses/<id>/delete`
4. Server displays confirmation page with expense details
5. User clicks "Confirm Delete" button
6. Browser submits POST to `/expenses/<id>/delete`
7. Server deletes expense from database
8. Server redirects to `/profile` with success flash message
9. User sees updated dashboard without the deleted expense

### Edge case handling
- If expense already deleted before POST: abort(404)
- If user tries to delete another user's expense: abort(404)
- If user not logged in: redirect to login
- If expense ID is invalid (non-integer): Flask routing returns 404 automatically
