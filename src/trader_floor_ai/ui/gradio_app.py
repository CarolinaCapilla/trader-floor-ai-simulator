"""Deprecated: use trader_floor_ai.app.ui instead.

This module now re-exports the current UI entry points from the app package
to preserve compatibility while the project structure is finalized.
"""

from trader_floor_ai.app.ui import create_ui, launch  # noqa: F401
