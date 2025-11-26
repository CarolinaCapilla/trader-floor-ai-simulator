"""UI entry point."""

from trader_floor_ai.app.ui import launch  # type: ignore


def _launch():
    # Initialize database if empty (for Railway first run)
    try:
        from init_db_if_empty import needs_initialization, initialize_database

        if needs_initialization():
            initialize_database()
    except Exception as e:
        print(f"Warning: Could not check/initialize database: {e}")

    # Import lazily to avoid startup side-effects
    from trader_floor_ai.app.ui import launch  # type: ignore

    launch()


if __name__ == "__main__":
    _launch()
