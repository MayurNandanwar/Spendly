from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3

from database.db import get_db, init_db, seed_db
from werkzeug.security import check_password_hash

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

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register")
def register():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get('user_id'):
        return redirect(url_for('profile'))

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
                    return redirect(url_for("profile"))
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
