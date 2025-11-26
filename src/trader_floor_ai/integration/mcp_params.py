import os
from dotenv import load_dotenv

load_dotenv(override=True)


def researcher_mcp_server_params(name: str):
    # Use persistent data volume for memory DBs (Railway provides single volume)
    # Falls back to local "memory" dir for dev environments
    data_dir = os.getenv("DB_PATH", "accounts.db").rsplit("/", 1)[0]  # Get /app/data or "."
    memory_dir = os.path.join(data_dir, "memory") if data_dir != "." else "memory"
    os.makedirs(memory_dir, exist_ok=True)
    libsql_path = os.path.abspath(os.path.join(memory_dir, f"{name}.db"))
    libsql_url = f"file:{libsql_path}"

    # Minimal env to quiet npx so stdout stays JSON-only for the MCP client
    npm_quiet = {
        "npm_config_loglevel": "silent",
        "npm_config_audit": "false",
        "npm_config_fund": "false",
        "npm_config_update_notifier": "false",
        "NO_UPDATE_NOTIFIER": "1",
        "NO_COLOR": "1",
    }

    brave_env = {**npm_quiet, "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")}
    memory_env = {**npm_quiet, "LIBSQL_URL": libsql_url}

    return [
        {"command": "mcp-server-fetch", "args": []},
        {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": memory_env,
        },
    ]