from typing import List
import asyncio
import os
from dotenv import load_dotenv

from trader_floor_ai.agents.trader import Trader  # type: ignore
from trader_floor_ai.services.market import is_market_open  # type: ignore

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "1"))

names = ["Jose Manuel", "Jaime", "Garbi", "Carmen"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto"]

if USE_MANY_MODELS:
    model_names = [
        "gpt-4.1-mini",
        "deepseek-chat",
        "gemini-2.5-flash-preview-04-17",
        "grok-3-mini-beta",
    ]
    short_model_names = [
        "GPT 4.1 Mini",
        "DeepSeek V3",
        "Gemini 2.5 Flash",
        "Grok 3 Mini",
    ]
else:
    model_names = ["gpt-4o-mini"] * 4
    short_model_names = ["GPT 4o mini"] * 4


def create_traders() -> List[Trader]:
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders


async def run_every_n_minutes():
    traders = create_traders()
    iterations_completed = 0
    while iterations_completed < MAX_ITERATIONS:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            await asyncio.gather(*[trader.run() for trader in traders])
            iterations_completed += 1
        else:
            print("Market is closed, skipping run")
        if iterations_completed < MAX_ITERATIONS:
            await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


__all__ = [
    "names",
    "lastnames",
    "short_model_names",
    "run_every_n_minutes",
    "create_traders",
]
