---
title: "Trader Floor AI Simulator"
emoji: "📈"
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "5.47.2"
app_file: app.py
pinned: false
---

# Trader Floor AI Simulator

An agentic trading floor simulator where multiple AI traders research, decide, and trade on a schedule. Includes a real-time Gradio dashboard, local account database, and pluggable MCP servers for market data, accounts, and push notifications.

## 🚀 Features

- **AI-Powered Trading Loop**: Each trader researches, generates a plan, and executes trades
- **Multi-Agent Composition**: Trader agents leverage a dedicated Researcher agent via MCP
- **Web Interface (Gradio)**: Live dashboard with portfolio values, charts, logs, holdings, and transactions
- **Pluggable Market Data**: Use Polygon MCP (paid or realtime) or a local market server
- **Persistent State**: SQLite-backed accounts and logs in `accounts.db`
- **Push Notifications**: Optional Pushover integration for post-trade summaries
- **Configurable Scheduling**: Run continuously or a fixed number of iterations

## 🏗️ Architecture

Core components:

- **Trader agents** (`traders.Trader`): Orchestrate research and trading using tools
- **Researcher agent**: Exposed as a tool to each trader via MCP servers
- **MCP servers** (`mcp_params.py`):
  - `accounts_server.py` for account tools and resources
  - `push_server.py` for push notifications (optional)
  - Market data via:
    - Polygon MCP (`uvx --from git+https://github.com/polygon-io/mcp_polygon@v0.1.0 mcp_polygon`) when configured, or
    - Local `market_server.py`
- **Scheduler** (`trading_floor.py`): Runs all traders every N minutes (or a fixed number of iterations)
- **UI** (`app.py`): Gradio dashboard polling live account data and logs
- **Database** (`database.py`): SQLite tables for `accounts`, `logs`, and `market`

## 📋 Prerequisites

- Python 3.12+ (Hugging Face Spaces defaults to Python 3.10 unless you set a runtime. If using HF Spaces, either:
   - Add a `runtime.txt` with `python-3.12` OR
   - Remove dependencies that require newer stdlib behavior.)
- [`uv`](https://github.com/astral-sh/uv) for fast installs/runs (or pip)
- Optional: Polygon API key (for market data MCP)
- Optional: Pushover credentials (for notifications)

## 🛠️ Installation

1. Clone the repository

   ```bash
   git clone <your-repo-url>
   cd trader-floor-ai-simulator
   ```

2. Install dependencies

   ```bash
   # with uv (recommended)
   uv sync

   # or with pip
   pip install -r requirements.txt
   ```

3. Set up environment variables
   Create a `.env` in the project root:

   ```env
   # Server and scheduling
   RUN_EVERY_N_MINUTES=60
   RUN_EVEN_WHEN_MARKET_IS_CLOSED=false
   USE_MANY_MODELS=false
   MAX_ITERATIONS=1

   # Market data
   POLYGON_API_KEY=
   POLYGON_PLAN=free   # free | paid | realtime

   # Research tools
   BRAVE_API_KEY=

   # Model providers (use any you plan to call)
   DEEPSEEK_API_KEY=
   GOOGLE_API_KEY=
   GROK_API_KEY=
   OPENROUTER_API_KEY=

   # Push notifications (optional)
   PUSHOVER_USER=
   PUSHOVER_TOKEN=
   ```

## 🚀 Usage

### Run the Gradio Dashboard

```bash
uv run app.py
```

- Opens the dashboard in your browser. It auto-refreshes logs (~0.5s) and portfolio/chart/holdings/transactions (~120s). Adjust timers in `app.py` if needed.

### Run Traders on a Schedule

```bash
# run once (default MAX_ITERATIONS=1)
uv run trading_floor.py

# run N iterations
MAX_ITERATIONS=3 uv run trading_floor.py

# run continuously every N minutes
MAX_ITERATIONS=1000000 RUN_EVERY_N_MINUTES=60 uv run trading_floor.py
```

- Press Ctrl+C to stop when running continuously.

## 📁 Project Structure

```
trader-floor-ai-simulator/
├── accounts.py               # Account model and operations
├── accounts_client.py        # MCP client for accounts server
├── accounts_server.py        # MCP server exposing account tools/resources
├── account.db                # SQLite database (ignored by git)
├── app.py                    # Gradio UI
├── database.py               # SQLite setup and CRUD helpers
├── market.py                 # Market data integration (Polygon or fallback)
├── market_server.py          # Local MCP server for market data
├── mcp_params.py             # MCP server parameters (accounts, push, market)
├── push_server.py            # Pushover MCP server (optional)
├── traders.py                # Trader and Researcher agent glue
├── trading_floor.py          # Scheduler to run traders periodically
├── requirements.txt / pyproject.toml
└── README.md
```

## 🔧 Configuration

- **Scheduling**: `RUN_EVERY_N_MINUTES`, `MAX_ITERATIONS`, `RUN_EVEN_WHEN_MARKET_IS_CLOSED`
- **Models**: Toggle `USE_MANY_MODELS` to run traders with multiple model backends
- **Market Data**: Set `POLYGON_PLAN` to `free`, `paid`, or `realtime`; provide `POLYGON_API_KEY`
- **Push**: Provide `PUSHOVER_USER` and `PUSHOVER_TOKEN` to enable notifications
- **Memory (MCP)**: Local memory DBs are created under `memory/` automatically

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License — add a `LICENSE` file if missing.

## 🐛 Troubleshooting

### Common Issues

1. `Failed to spawn: accounts_server.py`: Ensure file exists and `mcp_params.py` references `accounts_server.py`
2. `Unable to open connection to local database ./memory/<name>.db: 14`:
   - Ensure the `memory/` folder exists (the app now creates it automatically)
   - Use absolute `LIBSQL_URL` if running tools elsewhere
3. Polygon API errors: Set `POLYGON_API_KEY` and `POLYGON_PLAN`
4. UI not updating: Lower timers in `app.py` or trigger a new trader run

### Debug Mode

Enable additional logging in your shell as needed (example):

```bash
export MAX_ITERATIONS=1
export RUN_EVERY_N_MINUTES=1
```

## 🔄 Future Enhancements

- [ ] Migrate UI to Vue.js/Nuxt.js
- [ ] Export reports (CSV/PDF)

## 📞 Support

- Open an issue with logs, steps to reproduce, and environment details.
