#!/usr/bin/env python3
"""
Initialize database if it doesn't exist or is empty.
This runs automatically when the app starts.
"""
import asyncio
import os
import sqlite3


def needs_initialization():
    """Check if database needs initialization."""
    db_path = os.getenv("DB_PATH", "accounts.db")

    print(f"Checking database at: {db_path}")

    if not os.path.exists(db_path):
        print("Database file does not exist, needs initialization")
        return True

    # Check if database has any traders AND trading activity
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if we have accounts
        cursor.execute("SELECT COUNT(*) FROM accounts")
        account_count = cursor.fetchone()[0]

        if account_count == 0:
            print("No accounts found, needs initialization")
            conn.close()
            return True

        # Check if any account has trading activity (non-empty holdings or transactions)
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE holdings != '{}'")
        active_count = cursor.fetchone()[0]

        conn.close()
        print(
            f"Database has {account_count} accounts, {active_count} with trading activity"
        )

        # Need initialization if no accounts have any holdings
        return active_count == 0

    except Exception as e:
        print(f"Error checking database (will initialize): {e}")
        return True


async def run_initial_trades():
    """Run one trading cycle to populate data."""
    print("Running initial trading cycle to populate data...")
    from trader_floor_ai.scheduler.run import create_traders

    traders = create_traders()
    print(f"Created {len(traders)} traders, running sequentially...")

    # Run traders sequentially to avoid MCP server conflicts
    for trader in traders:
        print(f"Running {trader.name}...")
        await trader.run()

    print("Initial trading cycle complete!")


def initialize_database():
    """Initialize database with traders and run initial trades."""
    print("Database is empty, initializing...")
    from trader_floor_ai.scheduler.reset import reset_traders

    reset_traders()
    print("Database initialized with 4 traders")

    # Run one trading cycle to populate data
    asyncio.run(run_initial_trades())
    print("Database populated with trading data")


if __name__ == "__main__":
    if needs_initialization():
        initialize_database()
    else:
        print("Database already initialized")
