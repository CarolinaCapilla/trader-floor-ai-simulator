#!/usr/bin/env python3
"""
Single execution script for Railway cron jobs.
Runs all traders once and exits.
"""
import asyncio
import sys


async def main():
    print("Starting trading floor scheduler (single run)...")
    try:
        from trader_floor_ai.scheduler.run import create_traders
        from trader_floor_ai.services.market import is_market_open
        import os

        run_anyway = (
            os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").lower() == "true"
        )

        if not run_anyway and not is_market_open():
            print("Market is closed, skipping run")
            return

        traders = create_traders()
        print(f"Created {len(traders)} traders, starting execution...")

        # Run traders sequentially to avoid MCP server resource contention
        for trader in traders:
            print(f"Running {trader.name}...")
            await trader.run()

        print("Trading run completed successfully")
    except Exception as e:
        print(f"Error during trading run: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
