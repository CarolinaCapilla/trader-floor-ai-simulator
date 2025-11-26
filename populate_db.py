#!/usr/bin/env python3
"""
Quick DB population script for testing.
Creates initial trader accounts and runs one trading cycle.
"""
import asyncio
import os


def init_database():
    """Initialize database with trader accounts."""
    print("Initializing database...")
    from trader_floor_ai.scheduler.reset import reset_traders

    reset_traders()
    print("Database initialized with 4 traders")


async def run_one_cycle():
    """Run one trading cycle."""
    print("Running one trading cycle...")
    from trader_floor_ai.scheduler.run import create_traders

    traders = create_traders()
    print(f"Created {len(traders)} traders")

    # Run all traders
    await asyncio.gather(*[trader.run() for trader in traders])
    print("Trading cycle complete!")


async def main():
    # Reset and initialize
    init_database()

    # Run one cycle
    await run_one_cycle()

    print("\nDatabase populated!")


if __name__ == "__main__":
    asyncio.run(main())
