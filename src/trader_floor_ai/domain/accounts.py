from pydantic import BaseModel
import json
from dotenv import load_dotenv
from datetime import datetime

from trader_floor_ai.services.market import get_share_price
from trader_floor_ai.services.database import write_account, read_account, write_log

load_dotenv(override=True)

INITIAL_BALANCE = 10_000.0
SPREAD = 0.002

# Map non-equity or alias tickers to equity proxies (ETFs/trusts) we can trade
SYMBOL_SYNONYMS: dict[str, str] = {
    # Bitcoin -> spot ETF or trust
    "BTC-USD": "IBIT",
    "BTCUSD": "IBIT",
    "BTC": "IBIT",
    "XBT-USD": "IBIT",
    "XBTUSD": "IBIT",
    # Ethereum -> trust (widely available ticker)
    "ETH-USD": "ETHE",
    "ETHUSD": "ETHE",
    "ETH": "ETHE",
}


def normalize_symbol(symbol: str) -> tuple[str, str | None]:
    """Return a tradable equity symbol and a note if the symbol was mapped.

    Always uppercases the symbol. If a mapping occurs, returns (mapped, note),
    else returns (upper, None).
    """
    upper = symbol.strip().upper()
    mapped = SYMBOL_SYNONYMS.get(upper)
    if mapped and mapped != upper:
        return mapped, f"(mapped from {upper} to {mapped})"
    return upper, None


class Transaction(BaseModel):
    symbol: str
    quantity: int
    price: float
    timestamp: str
    rationale: str

    def total(self) -> float:
        return self.quantity * self.price

    def __repr__(self):
        return f"{abs(self.quantity)} shares of {self.symbol} at {self.price} each."


class Account(BaseModel):
    name: str
    balance: float
    strategy: str
    holdings: dict[str, int]
    transactions: list[Transaction]
    portfolio_value_time_series: list[tuple[str, float]]

    @classmethod
    def get(cls, name: str):
        fields = read_account(name.lower())
        if not fields:
            fields = {
                "name": name.lower(),
                "balance": INITIAL_BALANCE,
                "strategy": "",
                "holdings": {},
                "transactions": [],
                "portfolio_value_time_series": [],
            }
            write_account(name, fields)
        return cls(**fields)

    def save(self):
        write_account(self.name.lower(), self.model_dump())

    def reset(self, strategy: str):
        self.balance = INITIAL_BALANCE
        self.strategy = strategy
        self.holdings = {}
        self.transactions = []
        self.portfolio_value_time_series = []
        self.save()

    def deposit(self, amount: float):
        """Deposit funds into the account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        print(f"Deposited ${amount}. New balance: ${self.balance}")
        self.save()

    def withdraw(self, amount: float):
        """Withdraw funds from the account, ensuring it doesn't go negative."""
        if amount > self.balance:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount
        print(f"Withdrew ${amount}. New balance: ${self.balance}")
        self.save()

    def buy_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """Buy shares of a stock if sufficient funds are available."""
        symbol, map_note = normalize_symbol(symbol)
        if map_note:
            rationale = f"{rationale} {map_note}"
        price = get_share_price(symbol)
        buy_price = price * (1 + SPREAD)
        total_cost = buy_price * quantity

        if price == 0:
            raise ValueError(f"Unrecognized symbol {symbol}")

        # If not enough cash, auto-size down to the maximum affordable quantity
        if total_cost > self.balance:
            max_affordable = int(self.balance // buy_price)
            if max_affordable < 1:
                raise ValueError(
                    f"Insufficient funds to buy even 1 share of {symbol} at ${buy_price:.2f}."
                )
            # Adjust quantity and annotate rationale
            original_qty = quantity
            quantity = max_affordable
            total_cost = buy_price * quantity
            rationale = (
                rationale
                + f" (auto-sized from {original_qty} to {quantity} due to available cash)"
            )

        # Update holdings
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Record transaction
        transaction = Transaction(
            symbol=symbol,
            quantity=quantity,
            price=buy_price,
            timestamp=timestamp,
            rationale=rationale,
        )
        self.transactions.append(transaction)

        # Update balance
        self.balance -= total_cost
        self.save()
        write_log(self.name, "account", f"Bought {quantity} of {symbol}")
        return "Completed. Latest details:\n" + self.report()

    def sell_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """Sell shares of a stock if the user has enough shares."""
        symbol, map_note = normalize_symbol(symbol)
        if map_note:
            rationale = f"{rationale} {map_note}"
        if self.holdings.get(symbol, 0) < quantity:
            raise ValueError(
                f"Cannot sell {quantity} shares of {symbol}. Not enough shares held."
            )

        price = get_share_price(symbol)
        sell_price = price * (1 - SPREAD)
        total_proceeds = sell_price * quantity

        # Update holdings
        self.holdings[symbol] -= quantity

        # If shares are completely sold, remove from holdings
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Record transaction
        transaction = Transaction(
            symbol=symbol,
            quantity=-quantity,
            price=sell_price,
            timestamp=timestamp,
            rationale=rationale,
        )  # negative quantity for sell
        self.transactions.append(transaction)

        # Update balance
        self.balance += total_proceeds
        self.save()
        write_log(self.name, "account", f"Sold {quantity} of {symbol}")
        return "Completed. Latest details:\n" + self.report()

    def calculate_portfolio_value(self):
        """Calculate the total value of the user's portfolio."""
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def calculate_profit_loss(self, portfolio_value: float):
        """Calculate profit or loss from the initial spend."""
        initial_spend = sum(transaction.total() for transaction in self.transactions)
        return portfolio_value - initial_spend - self.balance

    def get_holdings(self):
        """Report the current holdings of the user."""
        return self.holdings

    def get_profit_loss(self):
        """Report the user's profit or loss at any point in time."""
        pv = self.calculate_portfolio_value()
        return self.calculate_profit_loss(pv)

    def list_transactions(self):
        """List all transactions made by the user."""
        return [transaction.model_dump() for transaction in self.transactions]

    def report(self) -> str:
        """Return a json string representing the account."""
        portfolio_value = self.calculate_portfolio_value()
        self.portfolio_value_time_series.append(
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), portfolio_value)
        )
        self.save()
        pnl = self.calculate_profit_loss(portfolio_value)
        data = self.model_dump()
        data["total_portfolio_value"] = portfolio_value
        data["total_profit_loss"] = pnl
        write_log(self.name, "account", f"Retrieved account details")
        return json.dumps(data)

    def get_strategy(self) -> str:
        """Return the strategy of the account"""
        write_log(self.name, "account", f"Retrieved strategy")
        return self.strategy

    def change_strategy(self, strategy: str) -> str:
        """At your discretion, if you choose to, call this to change your investment strategy for the future"""
        self.strategy = strategy
        self.save()
        write_log(self.name, "account", f"Changed strategy")
        return "Changed strategy"


__all__ = [
    "Account",
    "Transaction",
    "normalize_symbol",
    "INITIAL_BALANCE",
    "SPREAD",
]
