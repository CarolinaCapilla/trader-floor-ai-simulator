import os
import asyncio
from dotenv import load_dotenv

from trader_floor_ai.scheduler.run import run_every_n_minutes  # type: ignore
from trader_floor_ai.scheduler.reset import reset_traders  # type: ignore

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "1"))
RESET_ON_START = os.getenv("RESET_ON_START", "false").strip().lower() == "true"


if __name__ == "__main__":
    if RESET_ON_START:
        print("RESET_ON_START=true: resetting accounts, logs, and market cache...")
        reset_traders()
    print(
        f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes (max iterations: {MAX_ITERATIONS})"
    )
    asyncio.run(run_every_n_minutes())
