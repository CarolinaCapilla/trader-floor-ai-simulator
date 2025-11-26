"""Canonical market services module.

Migrated from the legacy root `market.py` to packaged services. Root module
will import from here to preserve compatibility.
"""

from polygon import RESTClient
from dotenv import load_dotenv
import os
from datetime import datetime
import random
from functools import lru_cache
from datetime import timezone

from trader_floor_ai.services.database import write_market, read_market

load_dotenv(override=True)

polygon_api_key = os.getenv("POLYGON_API_KEY")
polygon_plan = os.getenv("POLYGON_PLAN")

is_paid_polygon = polygon_plan == "paid"
is_realtime_polygon = polygon_plan == "realtime"


def is_market_open() -> bool:
    client = RESTClient(polygon_api_key)
    status = client.get_market_status()
    # Status may be a dict-like object in some client versions
    market_value = getattr(status, "market", None)
    if market_value is None and isinstance(status, dict):
        market_value = status.get("market")
    return market_value == "open"


def get_all_share_prices_polygon_eod() -> dict[str, float]:
    """With much thanks to student Reema R. for fixing the timezone issue with this!"""
    client = RESTClient(polygon_api_key)

    # Some client versions return a sequence, others a named object
    previous = client.get_previous_close_agg("SPY")
    first = previous[0] if isinstance(previous, (list, tuple)) else previous
    ts = getattr(first, "timestamp", None)
    if ts is None and isinstance(first, dict):
        ts = first.get("timestamp")
    if not isinstance(ts, (int, float)):
        raise RuntimeError("Polygon previous close missing timestamp")
    last_close = datetime.fromtimestamp(float(ts) / 1000.0, tz=timezone.utc).date()

    results = client.get_grouped_daily_aggs(
        last_close, adjusted=True, include_otc=False
    )
    prices: dict[str, float] = {}
    for r in results:
        ticker = getattr(r, "ticker", None)
        close = getattr(r, "close", None)
        if ticker is None and isinstance(r, dict):
            ticker = r.get("ticker")
            close = r.get("close")
        if isinstance(ticker, str) and isinstance(close, (int, float)):
            prices[ticker] = float(close)
    return prices


@lru_cache(maxsize=2)
def get_market_for_prior_date(today):
    market_data = read_market(today)
    if not market_data:
        market_data = get_all_share_prices_polygon_eod()
        write_market(today, market_data)
    return market_data


def get_share_price_polygon_eod(symbol) -> float:
    today = datetime.now().date().strftime("%Y-%m-%d")
    market_data = get_market_for_prior_date(today)
    return market_data.get(symbol, 0.0)


def get_share_price_polygon_min(symbol) -> float:
    client = RESTClient(polygon_api_key)
    result = client.get_snapshot_ticker("stocks", symbol)
    # Prefer min.close; fallback to prev_day.close
    m = getattr(result, "min", None)
    prev = getattr(result, "prev_day", None)
    m_close = getattr(m, "close", None) if m is not None else None
    p_close = getattr(prev, "close", None) if prev is not None else None
    return float(m_close or p_close or 0.0)


def get_share_price_polygon(symbol) -> float:
    # Use near-realtime snapshot for paid or realtime plans; otherwise EOD
    if is_paid_polygon or is_realtime_polygon:
        return get_share_price_polygon_min(symbol)
    else:
        return get_share_price_polygon_eod(symbol)


def get_share_price(symbol) -> float:
    if polygon_api_key:
        try:
            return get_share_price_polygon(symbol)
        except Exception as e:
            print(
                f"Was not able to use the polygon API due to {e}; using a random number"
            )
    return float(random.randint(1, 100))


__all__ = [
    "is_market_open",
    "get_share_price",
    "is_paid_polygon",
    "is_realtime_polygon",
]
