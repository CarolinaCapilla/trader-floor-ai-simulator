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

    if not os.path.exists(db_path):
        return True

    # Check if database has any traders
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        count = cursor.fetchone()[0]
        conn.close()
        return count == 0
    except:
        return True


def initialize_database():
    """Initialize database with traders."""
    print("Database is empty, initializing...")
    from trader_floor_ai.scheduler.reset import reset_traders

    reset_traders()
    print("Database initialized with traders")


if __name__ == "__main__":
    if needs_initialization():
        initialize_database()
    else:
        print("Database already initialized")
