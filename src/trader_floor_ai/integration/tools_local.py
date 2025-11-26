import json
import os
from typing import List

from agents import FunctionTool
from dotenv import load_dotenv

from trader_floor_ai.domain.accounts import Account
from trader_floor_ai.services.market import get_share_price

import requests


load_dotenv(override=True)


def make_accounts_tools() -> List[FunctionTool]:
    schema_name = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
        "additionalProperties": False,
    }

    schema_trade = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "symbol": {"type": "string"},
            "quantity": {"type": "integer"},
            "rationale": {"type": "string"},
        },
        "required": ["name", "symbol", "quantity", "rationale"],
        "additionalProperties": False,
    }

    async def _get_balance(_ctx, args_json: str):
        args = json.loads(args_json)
        return Account.get(args["name"]).balance

    async def _get_holdings(_ctx, args_json: str):
        args = json.loads(args_json)
        return Account.get(args["name"]).get_holdings()

    async def _buy_shares(_ctx, args_json: str):
        args = json.loads(args_json)
        return Account.get(args["name"]).buy_shares(
            args["symbol"], int(args["quantity"]), args["rationale"]
        )

    async def _sell_shares(_ctx, args_json: str):
        args = json.loads(args_json)
        return Account.get(args["name"]).sell_shares(
            args["symbol"], int(args["quantity"]), args["rationale"]
        )

    async def _change_strategy(_ctx, args_json: str):
        args = json.loads(args_json)
        return Account.get(args["name"]).change_strategy(args["strategy"])

    return [
        FunctionTool(
            name="get_balance",
            description="Get the cash balance for the given account name.",
            params_json_schema=schema_name,
            on_invoke_tool=_get_balance,
        ),
        FunctionTool(
            name="get_holdings",
            description="Get holdings for the given account name.",
            params_json_schema=schema_name,
            on_invoke_tool=_get_holdings,
        ),
        FunctionTool(
            name="buy_shares",
            description="Buy shares of a stock for the account.",
            params_json_schema=schema_trade,
            on_invoke_tool=_buy_shares,
        ),
        FunctionTool(
            name="sell_shares",
            description="Sell shares of a stock for the account.",
            params_json_schema=schema_trade,
            on_invoke_tool=_sell_shares,
        ),
        FunctionTool(
            name="change_strategy",
            description="Change the investment strategy for the account.",
            params_json_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "strategy": {"type": "string", "description": "New strategy"},
                },
                "required": ["name", "strategy"],
                "additionalProperties": False,
            },
            on_invoke_tool=_change_strategy,
        ),
    ]


def make_market_tools() -> List[FunctionTool]:
    async def _get_share_price(_ctx, args_json: str):
        args = json.loads(args_json)
        return get_share_price(args["symbol"])

    return [
        FunctionTool(
            name="get_share_price",
            description="Get the share price for a stock symbol (EOD or realtime based on config).",
            params_json_schema={
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"],
                "additionalProperties": False,
            },
            on_invoke_tool=_get_share_price,
        )
    ]


def make_push_tools() -> List[FunctionTool]:
    pushover_user = os.getenv("PUSHOVER_USER")
    pushover_token = os.getenv("PUSHOVER_TOKEN")
    pushover_url = "https://api.pushover.net/1/messages.json"

    async def _push(_ctx, args_json: str):
        args = json.loads(args_json)
        payload = {
            "user": pushover_user,
            "token": pushover_token,
            "message": args["message"],
        }
        try:
            r = requests.post(pushover_url, data=payload, timeout=10)
            r.raise_for_status()
            return "Push notification sent"
        except Exception as e:
            return f"Failed to send push: {e}"

    return [
        FunctionTool(
            name="push",
            description="Send a brief push notification using Pushover.",
            params_json_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
                "additionalProperties": False,
            },
            on_invoke_tool=_push,
        )
    ]


def make_local_tools() -> List[FunctionTool]:
    """Return all locally-implemented tools for Trader agent."""
    return make_accounts_tools() + make_market_tools() + make_push_tools()


__all__ = [
    "make_local_tools",
    "make_accounts_tools",
    "make_market_tools",
    "make_push_tools",
]
