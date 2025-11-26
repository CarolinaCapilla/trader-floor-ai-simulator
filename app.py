"""UI entry point."""

from trader_floor_ai.app.ui import launch  # type: ignore


def _launch():
    # Import lazily to avoid startup side-effects
    from trader_floor_ai.app.ui import launch  # type: ignore

    launch()


if __name__ == "__main__":
    _launch()
