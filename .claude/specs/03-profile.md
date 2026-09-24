# Spec: Profile Page

## Overview
Implement a user profile page that displays the logged-in user's account information (name, email, account creation date) and provides options to update their profile or log out. The profile page is the central hub for account management and gives users visibility into their account details. This is a prerequisite for future account management features like password change and profile updates.

## Depends on
- Step 1: Database Setup (users table with all account fields)
- Step 2: Registration (user accounts exist and can be created)
- Login/Logout (user authentication and session management)

## Routes
- `GET /profile` — display logged-in user's profile page — logged-in only

## Database changes
No database changes. Uses existing `users` table schema.

## Templates
- **Create:** `templates/profile.html` — display user name, email, account creation date; show logout button; show edit profile link (placeholder for future step)

## Files to change
- `app.py` — add `GET /profile` route handler that fetches the logged-in user's data and renders profile template
- `database/db.py` — add `get_user_by_id(user_id)` function to fetch a user record by ID

## Files to create
- `templates/profile.html` — new profile page template extending `base.html`
- `static/css/profile.css` — profile page styles (card layout, info display, buttons)

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite with `get_db()`
- Parameterized queries only — use `?` placeholders, never f-strings in SQL
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Route must be protected by `@login_required` decorator
- Display user's account creation date formatted as "Month DD, YYYY" (e.g., "September 24, 2026")
- Profile page uses consistent design language with rest of app (warm, editorial "paper and ink" style)
- Logout button redirects to `POST /logout` route
- Edit profile link is a placeholder for Step X (future feature) — link to `url_for('profile')` for now, no action yet
- Use the seeded demo user for testing: name: Demo User, email: demo@spendly.com

## Exception handling
- Every `get_db()` connection opened in the route must be closed in a `finally` block
- If user not found in database (edge case where session is stale), return 404 (should never happen in practice, but handle gracefully)
- No other database exceptions should be caught — those are infrastructure failures and should surface as 500

## Definition of done
- [ ] Logged-in user can navigate to `/profile` and see their account information (name, email, created_at)
- [ ] Account creation date is displayed in human-readable format (Month DD, YYYY)
- [ ] Profile page shows a logout button that POSTs to `/logout`
- [ ] Profile page shows an edit profile link (placeholder, links back to profile for now)
- [ ] Logged-out users accessing `/profile` are redirected to `/login`
- [ ] Profile page matches the design system of the app (colors, fonts, spacing from style.css variables)
- [ ] All internal links use `url_for()`, not hardcoded URLs
- [ ] `get_user_by_id(user_id)` function exists in `database/db.py` and is used by the route
- [ ] All DB connections are closed via `finally` on every code path, including error paths
- [ ] Profile page is responsive on mobile (400px+) and desktop (1000px+)
- [ ] Flash messages from logout appear on the landing page after redirect
