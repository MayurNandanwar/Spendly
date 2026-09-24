from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import date, timedelta
import re
import sqlite3

from database.db import get_db, init_db, seed_db, get_expenses, get_expense_summary
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Decorators                                                          #
# ------------------------------------------------------------------ #

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please sign in to continue")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

DASHBOARD_RANGE_PRESETS = ("month", "3months", "6months", "custom")


def _resolve_date_range(range_key, start_param, end_param):
    """Turn a preset key (or custom start/end params) into concrete start/end dates."""
    today = date.today()

    if range_key == "custom":
        start_date = start_param or None
        end_date = end_param or None
        return start_date, end_date

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
    if not session.get("user_id"):
        return render_template("landing.html")

    range_key = request.args.get("range", "month")
    if range_key not in DASHBOARD_RANGE_PRESETS:
        range_key = "month"

    start_param = request.args.get("start", "")
    end_param = request.args.get("end", "")

    start_date, end_date = _resolve_date_range(range_key, start_param, end_param)

    user_id = session["user_id"]
    expenses = get_expenses(user_id, start_date, end_date)
    total, category_totals = get_expense_summary(user_id, start_date, end_date)

    return render_template(
        "landing.html",
        expenses=expenses,
        total=total,
        category_totals=category_totals,
        range_key=range_key,
        start_date=start_date or "",
        end_date=end_date or "",
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get('user_id'):
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
                flash("Account created — please sign in.", "success")
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
    if session.get('user_id'):
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
                    session["user_id"] = user["id"]
                    session["user_name"] = user["name"]
                    return redirect(url_for("landing"))
                else:
                    error = "Invalid email or password."
            finally:
                conn.close()

    return render_template("login.html", error=error)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    return "Profile page — coming in Step 4"


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
