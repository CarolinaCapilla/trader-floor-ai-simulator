#!/usr/bin/env python3
"""
Initialize database if it doesn't exist or is empty.
This runs automatically when the app starts.
"""
import os
import sqlite3


def needs_initialization():
    """Check if database needs initialization."""
    db_path = os.getenv("DB_PATH", "accounts.db")

    print(f"Checking database at: {db_path}")

    if not os.path.exists(db_path):
        print("Database file does not exist, needs initialization")
        return True

    # Check if database has trader accounts
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"Database has {count} accounts")
        return count == 0
    except Exception as e:
        print(f"Error checking database (will initialize): {e}")
        return True


def initialize_database():
    """Initialize database with traders (accounts only, no trading yet)."""
    print("Database needs initialization...")
    from trader_floor_ai.scheduler.reset import reset_traders

    reset_traders()
    print("Database initialized with 4 trader accounts")
    print("Note: Run 'python populate_db.py' or the scheduler to populate trading data")


if __name__ == "__main__":
    if needs_initialization():
        initialize_database()
    else:
        print("Database already initialized")
