import random
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash
from database.db import get_db

# Realistic Indian first names across regions
FIRST_NAMES = [
    "Rajesh", "Priya", "Amit", "Neha", "Vikram", "Anjali", "Arjun", "Divya",
    "Rohan", "Pooja", "Nikhil", "Shreya", "Arun", "Sakshi", "Karan", "Isha",
    "Rahul", "Ananya", "Sanjay", "Nisha", "Aditya", "Riya", "Varun", "Meera",
    "Deepak", "Priyanka", "Sandeep", "Anjali", "Ashok", "Divyanka", "Harshit", "Tanya"
]

# Realistic Indian last names across regions
LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Verma", "Gupta", "Mishra", "Nair",
    "Reddy", "Iyer", "Menon", "Deshmukh", "Chopra", "Banerjee", "Mukherjee", "Bhat",
    "Rao", "Trivedi", "Joshi", "Pandey", "Dwivedi", "Saxena", "Malhotra", "Khanna",
    "Srivastava", "Pillai", "Krishnan", "Varma", "Dasgupta", "Roy", "Chatterjee", "Dutta"
]

def generate_unique_email():
    """Generate a unique email until one is found that doesn't exist."""
    conn = get_db()
    try:
        while True:
            first_name = random.choice(FIRST_NAMES).lower()
            last_name = random.choice(LAST_NAMES).lower()
            random_suffix = random.randint(10, 999)
            email = f"{first_name}.{last_name}{random_suffix}@gmail.com"

            # Check if email already exists
            cursor = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            )
            if cursor.fetchone() is None:
                return email, first_name.capitalize(), last_name.capitalize()
    finally:
        conn.close()

def seed_indian_user():
    """Create and insert a realistic Indian user."""
    email, first_name, last_name = generate_unique_email()
    name = f"{first_name} {last_name}"
    password_hash = generate_password_hash("password123")

    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid

        print(f"\n✓ User created successfully!")
        print(f"  ID:    {user_id}")
        print(f"  Name:  {name}")
        print(f"  Email: {email}")
        print(f"  Password: password123\n")

        return user_id
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    seed_indian_user()
