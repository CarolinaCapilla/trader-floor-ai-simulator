from contextlib import AsyncExitStack
import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from agents.mcp import MCPServerStdio

from trader_floor_ai.domain.accounts import Account
from trader_floor_ai.integration.mcp_params import researcher_mcp_server_params
from trader_floor_ai.integration.tools_local import make_local_tools
from trader_floor_ai.agents.templates import (
    researcher_instructions,
    trader_instructions,
    trade_message,
    rebalance_message,
    research_tool,
)


load_dotenv(override=True)

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MAX_TURNS = 30

openrouter_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key
)
deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
grok_client = AsyncOpenAI(base_url=GROK_BASE_URL, api_key=grok_api_key)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)


def get_model(model_name: str):
    if "/" in model_name:
        return OpenAIChatCompletionsModel(
            model=model_name, openai_client=openrouter_client
        )
    elif "deepseek" in model_name:
        return OpenAIChatCompletionsModel(
            model=model_name, openai_client=deepseek_client
        )
    elif "grok" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=grok_client)
    elif "gemini" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)
    else:
        return model_name


async def get_researcher(mcp_servers, model_name) -> Agent:
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=get_model(model_name),
        mcp_servers=mcp_servers,
    )
    return researcher


async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool())


class Trader:
    def __init__(self, name: str, lastname="Trader", model_name="gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.agent = None
        self.model_name = model_name
        self.do_trade = True

    async def create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        # Local in-process tools (accounts, market, push)
        local_tools = make_local_tools()
        # Researcher tool still via MCP servers
        tool = await get_researcher_tool(researcher_mcp_servers, self.model_name)
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=get_model(self.model_name),
            tools=[tool, *local_tools],
            mcp_servers=[],
        )
        return self.agent

    async def get_account_report(self) -> str:
        account = Account.get(self.name).report()
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)

    async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        self.agent = await self.create_agent(trader_mcp_servers, researcher_mcp_servers)
        account = await self.get_account_report()
        strategy = Account.get(self.name).get_strategy()
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        await Runner.run(self.agent, message, max_turns=MAX_TURNS)
        # Print a concise summary to the terminal so runs are visible
        try:
            summary = json.loads(Account.get(self.name).report())
            bal = summary.get("balance")
            holdings = summary.get("holdings")
            print(f"[{self.name}] Balance: {bal:.2f}; Holdings: {holdings}")
        except Exception as e:
            print(f"[{self.name}] Unable to print summary: {e}")

    async def run_with_mcp_servers(self):
        # Only start Researcher MCP servers; Trader tools are local now
        async with AsyncExitStack() as stack:
            researcher_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)  # type: ignore[arg-type]
                )
                for params in researcher_mcp_server_params(self.name)
            ]
            await self.run_agent(
                trader_mcp_servers=None, researcher_mcp_servers=researcher_mcp_servers
            )

    async def run_with_trace(self):
        trace_name = (
            f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
        )
        # Use default tracing without custom trace_id or processors
        with trace(trace_name):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        self.do_trade = not self.do_trade


__all__ = ["Trader", "get_researcher", "get_researcher_tool"]
