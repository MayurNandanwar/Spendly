"""Tests for the Spendly profile page (spec: .claude/specs/03-profile.md).

Uses the `client` / `auth_client` fixtures from tests/conftest.py, which
provide an isolated, seeded database (demo@spendly.com / demo123).
"""
import re
import sqlite3
from datetime import datetime

import pytest

import app as app_module
import database.db as db

DEMO_EMAIL = "demo@spendly.com"
DEMO_NAME = "Demo User"


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _query(sql, params=()):
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def _execute(sql, params=()):
    conn = sqlite3.connect(db.DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def _demo_row():
    return _query("SELECT * FROM users WHERE email = ?", (DEMO_EMAIL,))[0]


def _expected_date_strings(created_at):
    """Acceptable 'Month DD, YYYY' renderings (zero-padded or not)."""
    parsed = datetime.strptime(created_at[:10], "%Y-%m-%d")
    padded = parsed.strftime("%B %d, %Y")
    unpadded = f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"
    return {padded, unpadded}


def _register_and_login(name, email, password="password123"):
    """Create a second user and return a fresh client logged in as them."""
    other = app_module.app.test_client()
    other.post("/register", data={"name": name, "email": email, "password": password})
    other.post("/login", data={"email": email, "password": password})
    return other


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

class TestProfileAuthGuard:
    def test_profile_logged_out_redirects_to_login(self, client):
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302, "Expected redirect for logged-out user"
        assert "/login" in response.headers["Location"], "Expected redirect to /login"

    def test_profile_logged_out_follow_shows_login_page(self, client):
        response = client.get("/profile", follow_redirects=True)
        assert response.status_code == 200
        assert b"password" in response.data.lower(), "Expected login form after redirect"

    def test_profile_logged_out_does_not_leak_user_data(self, client):
        response = client.get("/profile", follow_redirects=True)
        assert DEMO_EMAIL.encode() not in response.data, "Email must not be shown to logged-out users"

    def test_profile_with_garbage_access_cookie_redirects_to_login(self, client):
        client.set_cookie("access_token", "not-a-real-jwt")
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# Happy path                                                          #
# ------------------------------------------------------------------ #

class TestProfileHappyPath:
    def test_profile_logged_in_returns_200(self, auth_client):
        response = auth_client.get("/profile")
        assert response.status_code == 200, "Logged-in user should see profile page"

    def test_profile_shows_user_name(self, auth_client):
        response = auth_client.get("/profile")
        assert DEMO_NAME.encode() in response.data, "Expected user's name on profile"

    def test_profile_shows_user_email(self, auth_client):
        response = auth_client.get("/profile")
        assert DEMO_EMAIL.encode() in response.data, "Expected user's email on profile"

    def test_profile_shows_created_at_in_month_dd_yyyy_format(self, auth_client):
        created_at = _demo_row()["created_at"]
        html = auth_client.get("/profile").get_data(as_text=True)
        expected = _expected_date_strings(created_at)
        assert any(e in html for e in expected), (
            f"Expected one of {expected} (Month DD, YYYY) in profile page"
        )

    def test_profile_does_not_show_raw_iso_timestamp(self, auth_client):
        created_at = _demo_row()["created_at"]
        html = auth_client.get("/profile").get_data(as_text=True)
        assert created_at not in html, "Raw DB timestamp should not be displayed"

    def test_profile_extends_base_layout(self, auth_client):
        html = auth_client.get("/profile").get_data(as_text=True)
        assert "<html" in html.lower() and "</html>" in html.lower(), "Expected full page from base.html"

    def test_landing_redirects_logged_in_user_to_profile(self, auth_client):
        response = auth_client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]


# ------------------------------------------------------------------ #
# Logout button and edit link                                         #
# ------------------------------------------------------------------ #

class TestProfileActions:
    def test_profile_has_logout_form_posting_to_logout(self, auth_client):
        html = auth_client.get("/profile").get_data(as_text=True)
        forms = re.findall(r"<form\b[^>]*>", html, flags=re.IGNORECASE)
        logout_forms = [
            f for f in forms
            if "/logout" in f and re.search(r'method\s*=\s*["\']post["\']', f, re.IGNORECASE)
        ]
        assert logout_forms, "Expected a <form method=post action=/logout> on profile page"

    def test_profile_has_edit_profile_link_pointing_to_profile(self, auth_client):
        html = auth_client.get("/profile").get_data(as_text=True)
        match = re.search(
            r'<a\b[^>]*href\s*=\s*["\']([^"\']*)["\'][^>]*>[^<]*edit\s+profile',
            html, flags=re.IGNORECASE,
        )
        assert match, "Expected an 'Edit profile' link"
        assert match.group(1).split("?")[0].split("#")[0] == "/profile", (
            "Edit profile placeholder should link back to /profile"
        )

    def test_logout_clears_session_so_profile_requires_login(self, auth_client):
        response = auth_client.post("/logout", follow_redirects=False)
        assert response.status_code == 302
        after = auth_client.get("/profile", follow_redirects=False)
        assert after.status_code == 302, "Profile must be protected after logout"
        assert "/login" in after.headers["Location"]

    def test_logout_redirects_to_landing_with_flash_message(self, auth_client):
        response = auth_client.post("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"signed out" in response.data.lower(), "Expected logout flash on landing page"

    def test_logout_requires_post(self, auth_client):
        response = auth_client.get("/logout")
        assert response.status_code == 405, "Logout must only accept POST"

    def test_logout_clears_refresh_token_in_db(self, auth_client):
        assert _demo_row()["refresh_token_hash"], "Login should have stored a refresh token"
        auth_client.post("/logout")
        assert _demo_row()["refresh_token_hash"] is None, "Logout should revoke refresh token"


# ------------------------------------------------------------------ #
# Data isolation / edge cases                                         #
# ------------------------------------------------------------------ #

class TestProfileEdgeCases:
    def test_profile_shows_each_user_their_own_details(self, client):
        other = _register_and_login("Alice Example", "alice@example.com")
        response = other.get("/profile")
        assert response.status_code == 200
        assert b"Alice Example" in response.data
        assert b"alice@example.com" in response.data
        assert DEMO_EMAIL.encode() not in response.data, "Must not show another user's email"

    def test_profile_does_not_display_password_hash(self, auth_client):
        password_hash = _demo_row()["password_hash"]
        html = auth_client.get("/profile").get_data(as_text=True)
        assert password_hash not in html, "Password hash must never be rendered"

    def test_profile_escapes_html_in_user_name(self, client):
        other = _register_and_login("<b>Bold</b> Bob", "bob@example.com")
        html = other.get("/profile").get_data(as_text=True)
        assert "<b>Bold</b> Bob" not in html, "User name must be HTML-escaped"
        assert "&lt;b&gt;Bold&lt;/b&gt;" in html

    def test_profile_stale_session_user_deleted_returns_404(self, auth_client):
        user_id = _demo_row()["id"]
        _execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
        _execute("DELETE FROM users WHERE id = ?", (user_id,))
        response = auth_client.get("/profile")
        assert response.status_code == 404, "Stale session for missing user should 404"

    def test_profile_get_has_no_db_side_effects_on_user(self, auth_client):
        before = tuple(_demo_row())
        auth_client.get("/profile")
        after = tuple(_demo_row())
        assert before == after, "Viewing profile must not modify the users row"

    def test_profile_repeated_requests_succeed(self, auth_client):
        # Connections must be closed on every request; repeated hits should not lock the DB.
        for _ in range(5):
            assert auth_client.get("/profile").status_code == 200

    @pytest.mark.parametrize("query", [
        "?range=bogus",
        "?range='; DROP TABLE users; --",
        "?range=custom&start=not-a-date&end=also-bad",
    ])
    def test_profile_odd_query_params_do_not_break_page_or_db(self, auth_client, query):
        response = auth_client.get("/profile" + query)
        assert response.status_code == 200, "Odd query params should not 500"
        assert _query("SELECT COUNT(*) AS c FROM users")[0]["c"] >= 1, "users table must survive"

    def test_profile_post_not_allowed(self, auth_client):
        response = auth_client.post("/profile")
        assert response.status_code == 405, "/profile is GET only"


# ------------------------------------------------------------------ #
# DB helper: get_user_by_id                                           #
# ------------------------------------------------------------------ #

class TestGetUserById:
    def test_get_user_by_id_returns_demo_user_fields(self, client):
        demo = _demo_row()
        user = db.get_user_by_id(demo["id"])
        assert user is not None
        assert user["name"] == DEMO_NAME
        assert user["email"] == DEMO_EMAIL
        assert user["created_at"] == demo["created_at"]

    def test_get_user_by_id_unknown_id_returns_none(self, client):
        assert db.get_user_by_id(999999) is None

    def test_get_user_by_id_sql_injection_string_is_safe(self, client):
        assert db.get_user_by_id("1 OR 1=1") is None, "Parameterized query should not match"
        assert _query("SELECT COUNT(*) AS c FROM users")[0]["c"] >= 1
