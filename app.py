from flask import Flask, render_template, request, redirect, url_for, flash, abort, g
from functools import wraps
from datetime import date, datetime, timedelta, timezone
import hashlib
import os
import re
import secrets
import sqlite3

import jwt

from database.db import (
    CATEGORIES, get_db, init_db, seed_db, get_expenses, get_expense_summary, get_user_by_id,
    store_refresh_token, get_user_by_refresh_token_hash, clear_refresh_token,
    add_expense, get_expense_by_id, update_expense, delete_expense,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Secrets come from the environment. If unset, a random per-process value is
# used so nothing forgeable is ever committed; sessions/tokens then reset on
# every restart. Set SPENDLY_SECRET_KEY / SPENDLY_JWT_SECRET for stable values.
app.secret_key = os.environ.get("SPENDLY_SECRET_KEY") or secrets.token_hex(32)

JWT_SECRET_KEY = os.environ.get("SPENDLY_JWT_SECRET") or secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=7)
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"

# The demo account (demo@spendly.com / demo123) has a public password, so it is
# only seeded for development: set SPENDLY_SEED_DEMO=1 or run with FLASK_DEBUG=1.
SEED_DEMO = (
    os.environ.get("SPENDLY_SEED_DEMO") == "1"
    or os.environ.get("FLASK_DEBUG") == "1"
)

with app.app_context():
    init_db()
    if SEED_DEMO:
        seed_db()


# ------------------------------------------------------------------ #
# JWT helpers                                                         #
# ------------------------------------------------------------------ #

def create_access_token(user_id, name):
    """Return a signed, short-lived JWT carrying the user's identity."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "name": name,
        "type": "access",
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token():
    """Return (raw_token, token_hash, expires_at_iso) for a new refresh token.

    The raw token is opaque (not a JWT) since it must be looked up by its
    hash in the database for server-side revocation. Only the hash is ever
    stored, so a database leak alone can't be used to impersonate a user.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + REFRESH_TOKEN_TTL).isoformat()
    return raw_token, token_hash, expires_at


def decode_access_token(token):
    """Return the JWT payload if valid, or None if missing/expired/invalid."""
    if not token:
        return None
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None


def issue_auth_cookies(response, user_id, name):
    """Create a fresh access+refresh token pair, persist the refresh hash, and set cookies."""
    access_token = create_access_token(user_id, name)
    raw_refresh_token, refresh_hash, refresh_expires_at = create_refresh_token()
    store_refresh_token(user_id, refresh_hash, refresh_expires_at)

    # Secure cookies by default; relaxed only in debug so plain-HTTP dev works.
    secure_cookie = not app.debug

    response.set_cookie(
        ACCESS_COOKIE_NAME, access_token,
        max_age=int(ACCESS_TOKEN_TTL.total_seconds()),
        httponly=True, secure=secure_cookie, samesite="Lax", path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME, raw_refresh_token,
        max_age=int(REFRESH_TOKEN_TTL.total_seconds()),
        httponly=True, secure=secure_cookie, samesite="Lax", path="/",
    )
    return response


def clear_auth_cookies(response):
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    return response


# ------------------------------------------------------------------ #
# Request hooks                                                       #
# ------------------------------------------------------------------ #

@app.before_request
def load_current_user():
    payload = decode_access_token(request.cookies.get(ACCESS_COOKIE_NAME))
    g.current_user = None
    if payload:
        try:
            g.current_user = {"id": int(payload["sub"]), "name": payload["name"]}
        except (KeyError, TypeError, ValueError):
            g.current_user = None


@app.context_processor
def inject_current_user():
    return {"current_user": g.current_user}


# ------------------------------------------------------------------ #
# Decorators                                                          #
# ------------------------------------------------------------------ #

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.current_user:
            flash("Please sign in to continue")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

DASHBOARD_RANGE_PRESETS = ("month", "3months", "6months", "custom")


def _valid_iso_date(value):
    """Return value if it is a YYYY-MM-DD date, otherwise None."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    return value


def _resolve_date_range(range_key, start_param, end_param):
    """Turn a preset key (or custom start/end params) into concrete start/end dates."""
    today = date.today()

    if range_key == "custom":
        return _valid_iso_date(start_param), _valid_iso_date(end_param)

    if range_key == "3months":
        start_date = today - timedelta(days=90)
    elif range_key == "6months":
        start_date = today - timedelta(days=180)
    else:
        range_key = "month"
        start_date = today.replace(day=1)

    return start_date.isoformat(), today.isoformat()


@app.route("/")
def landing():
    if g.current_user:
        return redirect(url_for("profile"))

    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.current_user:
        return redirect(url_for('landing'))

    errors = {}
    name = ""
    email = ""
    duplicate_email = False

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name:
            errors["name"] = "Please enter your full name."
        elif len(name) < 2:
            errors["name"] = "Name must be at least 2 characters."
        elif len(name) > 100:
            errors["name"] = "Name must be 100 characters or fewer."

        if not email:
            errors["email"] = "Please enter your email address."
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors["email"] = "Please enter a valid email address."
        else:
            conn = get_db()
            try:
                cursor = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    errors["email"] = "An account with this email already exists."
                    duplicate_email = True
            finally:
                conn.close()

        if not password:
            errors["password"] = "Please enter a password."
        elif len(password) < 8:
            errors["password"] = "Password must be at least 8 characters."
        elif len(password) > 128:
            errors["password"] = "Password must be 128 characters or fewer."

        if not errors:
            password_hash = generate_password_hash(password)
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, password_hash)
                )
                conn.commit()
                flash("Account created â€” please sign in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                errors["email"] = "An account with this email already exists."
                duplicate_email = True
            finally:
                conn.close()

    return render_template(
        "register.html", errors=errors, name=name, email=email,
        duplicate_email=duplicate_email
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.current_user:
        return redirect(url_for('landing'))

    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Invalid email or password."
        else:
            conn = get_db()
            try:
                cursor = conn.execute(
                    "SELECT id, name, password_hash FROM users WHERE email = ?",
                    (email,)
                )
                user = cursor.fetchone()

                if user and check_password_hash(user["password_hash"], password):
                    response = redirect(url_for("landing"))
                    return issue_auth_cookies(response, user["id"], user["name"])
                else:
                    error = "Invalid email or password."
            finally:
                conn.close()

    return render_template("login.html", error=error)


@app.route("/refresh", methods=["POST"])
def refresh():
    """Issue a new access token (and rotate the refresh token) from a valid refresh cookie."""
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        abort(401)

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    user = get_user_by_refresh_token_hash(token_hash)

    if not user:
        abort(401)

    expires_at = datetime.fromisoformat(user["refresh_token_expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        clear_refresh_token(user["id"])
        abort(401)

    # Fixed local target: request.referrer is attacker-influenced (open redirect).
    response = redirect(url_for("profile"))
    return issue_auth_cookies(response, user["id"], user["name"])


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    clear_refresh_token(g.current_user["id"])
    flash("You have been signed out.", "success")
    response = redirect(url_for("landing"))
    return clear_auth_cookies(response)


@app.route("/profile")
@login_required
def profile():
    user_id = g.current_user["id"]
    user = get_user_by_id(user_id)

    if not user:
        abort(404)

    range_key = request.args.get("range", "month")
    if range_key not in DASHBOARD_RANGE_PRESETS:
        range_key = "month"

    start_param = request.args.get("start", "")
    end_param = request.args.get("end", "")

    start_date, end_date = _resolve_date_range(range_key, start_param, end_param)

    expenses = get_expenses(user_id, start_date, end_date)
    total, category_totals = get_expense_summary(user_id, start_date, end_date)

    return render_template(
        "profile.html",
        user=user,
        expenses=expenses,
        total=total,
        category_totals=category_totals,
        range_key=range_key,
        start_date=start_date or "",
        end_date=end_date or "",
    )


@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")


# ------------------------------------------------------------------ #
# Placeholder routes â€” students will implement these                  #
# ------------------------------------------------------------------ #

EXPENSE_CATEGORIES = CATEGORIES


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense_route():
    errors = {}
    amount = ""
    category = ""
    expense_date = ""
    description = ""

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        expense_date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        parsed_amount = None
        if not amount:
            errors["amount"] = "Please enter an amount."
        else:
            try:
                parsed_amount = float(amount)
                if parsed_amount <= 0:
                    errors["amount"] = "Amount must be greater than 0."
            except ValueError:
                errors["amount"] = "Please enter a valid number."

        if not category:
            errors["category"] = "Please select a category."
        elif category not in EXPENSE_CATEGORIES:
            errors["category"] = "Please select a valid category."

        if not expense_date:
            errors["date"] = "Please enter a date."
        else:
            try:
                parsed_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
                if parsed_date > date.today():
                    errors["date"] = "Date cannot be in the future."
            except ValueError:
                errors["date"] = "Please enter a valid date."

        if len(description) > 500:
            errors["description"] = "Description must be 500 characters or fewer."

        if not errors:
            add_expense(
                g.current_user["id"], parsed_amount, category, expense_date, description
            )
            flash("Expense added successfully", "success")
            return redirect(url_for("profile"))

    return render_template(
        "add_expense.html", errors=errors, amount=amount, category=category,
        date=expense_date, description=description, categories=EXPENSE_CATEGORIES,
        today=date.today().isoformat(),
    )


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    """Display and process edit expense form."""
    user_id = g.current_user["id"]
    
    # Fetch expense with ownership verification
    expense = get_expense_by_id(user_id, id)
    if not expense:
        abort(404)
    
    errors = {}
    amount = ""
    category = ""
    expense_date = ""
    description = ""
    
    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        expense_date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()
        
        parsed_amount = None
        if not amount:
            errors["amount"] = "Please enter an amount."
        else:
            try:
                parsed_amount = float(amount)
                if parsed_amount <= 0:
                    errors["amount"] = "Amount must be greater than 0."
            except ValueError:
                errors["amount"] = "Please enter a valid number."
        
        if not category:
            errors["category"] = "Please select a category."
        elif category not in EXPENSE_CATEGORIES:
            errors["category"] = "Please select a valid category."
        
        if not expense_date:
            errors["date"] = "Please enter a date."
        else:
            try:
                parsed_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
                if parsed_date > date.today():
                    errors["date"] = "Date cannot be in the future."
            except ValueError:
                errors["date"] = "Please enter a valid date."
        
        if len(description) > 500:
            errors["description"] = "Description must be 500 characters or fewer."
        
        if not errors:
            updated_id = update_expense(user_id, id, parsed_amount, category, expense_date, description)
            if not updated_id:
                # Race condition: expense was deleted
                abort(404)
            flash("Expense updated successfully", "success")
            return redirect(url_for("profile"))
    
    # Pre-populate form with current expense values on GET or validation error
    if request.method == "GET":
        amount = str(expense["amount"])
        category = expense["category"]
        expense_date = expense["date"]
        description = expense["description"] or ""
    
    return render_template(
        "edit_expense.html",
        expense=expense,
        errors=errors,
        amount=amount,
        category=category,
        date=expense_date,
        description=description,
        categories=EXPENSE_CATEGORIES,
    )



@app.route("/expenses/<int:id>/delete", methods=["GET"])
@login_required
def delete_expense_page(id):
    """Display confirmation page for expense deletion."""
    user_id = g.current_user["id"]
    expense = get_expense_by_id(user_id, id)

    if not expense:
        abort(404)

    return render_template("delete_expense_confirmation.html", expense=expense)


@app.route("/expenses/<int:id>/delete", methods=["POST"])
@login_required
def delete_expense_route(id):
    """Process expense deletion."""
    user_id = g.current_user["id"]

    # Verify expense exists and is owned by user before deletion
    expense = get_expense_by_id(user_id, id)
    if not expense:
        abort(404)

    # Perform deletion
    delete_expense(user_id, id)

    flash("Expense deleted successfully", "success")
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5001)

