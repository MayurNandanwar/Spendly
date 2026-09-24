---
description: Generate a production-ready specification for a Spendly feature
argument-hint: <step_number> <feature_name>
allowed-tools: Read, Write, Glob, Bash(git:*)
---

# Generate spec: $ARGUMENTS

## Parse arguments

Extract from $ARGUMENTS:
- `step_number` — zero-pad to 2 digits: 2 → 02, 11 → 11
- `feature_name` — rest of the input

Examples:
- Input: `2 logout` → step: 02, name: logout
- Input: `11 add expense` → step: 11, name: add expense
- Input: `7 monthly summary` → step: 07, name: monthly summary

Convert feature_name to:
- `feature_slug` — kebab-case for filename: "add expense" → add-expense
- `feature_title` — Title Case for heading: "add expense" → Add Expense

File will be saved as: `docs/specs/02-logout.md`

---

## 5 Critical Pillars for Production-Ready Specs

### 1. Routes & Endpoints (Interface)
- What HTTP endpoints? (GET, POST, PUT, DELETE)
- What URL paths?
- What does each endpoint do?
- Who can access it? (public / logged-in / owner-only)
- What does it return? (render template, redirect, JSON)
- What HTTP status codes? (200, 302, 404, 400, 403)

### 2. Database Schema & Data Integrity (Reliability)
- New tables and columns needed?
- Data types (INTEGER, TEXT, TIMESTAMP)?
- Constraints (NOT NULL, UNIQUE, CHECK)?
- Foreign keys and relationships?
- What happens on delete? (CASCADE, SET NULL, RESTRICT)
- Indexes for performance?

### 3. Auth & Authorization (Security)
- Which routes need logged-in user?
- Which routes need user to own the record?
- How to check ownership? (user_id in query WHERE clause)
- What if user not authenticated? (redirect to login)
- What if user not owner? (return 404, never 403)
- Password hashing: werkzeug.security
- CSRF protection: session-based tokens on all POST forms

### 4. Input Validation (Precision)
- Required fields?
- Data types and lengths? (email format, phone digits, text max 500 chars)
- Numeric ranges? (amount > 0, age 18-120)
- Date constraints? (past only, future allowed?)
- Money: stored as integer paise/cents, never float
- **Server-side always** (client-side is convenience only)
- Validation errors: keep form values, show specific error message

### 5. Testing & Acceptance Criteria (Completeness)
- Happy path: valid input, success response (200/302), data saved correctly
- Validation: invalid input, error shown, data NOT saved, form values kept
- Authorization: unauthenticated user redirected to login, other user's record returns 404
- Edge cases: empty state, not found, duplicate submissions, deleted records
- Database: relationships intact, constraints enforced, foreign keys work
- Security: CSRF token required, password hashed, parameterized queries
- Manual testing: steps to verify at http://localhost:5001

Acceptance checklist:
- [ ] All routes return correct HTTP status
- [ ] User cannot access other users' data
- [ ] Form validation works on server
- [ ] Database constraints prevent invalid data
- [ ] Tests pass: `pytest tests/test_<feature>.py`
- [ ] Flash messages appear on success/error
- [ ] POST requests redirect (no resubmit on refresh)
- [ ] All links use `url_for()`, not hardcoded

---

## Generate the spec

Create file: `docs/specs/<step>-<feature_slug>.md`

Example: `/create_spec 2 logout` → `docs/specs/02-logout.md`

Structure:
```markdown
# Spec: Feature Title

## 1. Routes & Endpoints
...

## 2. Database Schema & Data Integrity
...

## 3. Auth & Authorization
...

## 4. Input Validation
...

## 5. Testing & Acceptance Criteria
...

## Supporting Details

### Files to Create
...

### Files to Modify
...

### Flash Messages
...

### Integration
...
```

---

## Report to user

```
Step:   02
Feature: logout
File:   docs/specs/02-logout.md
Status: ✓ Spec created

5 Pillars: Routes, Database, Auth, Validation, Testing
Ready for implementation
```