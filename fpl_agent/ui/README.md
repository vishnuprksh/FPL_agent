Dash UI for FPL_agent
=====================

This package provides a Dash-based UI that mirrors the existing Flask templates.

Run the Dash app (preferred):

1. Install dependencies from the project's `requirements.txt` (Dash and dash-bootstrap-components were added).
2. Set the environment variable USE_DASH=1 and run the normal entrypoint:

   USE_DASH=1 python -m fpl_agent.app

Or run directly:

   python -c "from fpl_agent.ui import run_dash; run_dash()"

The Dash app provides pages: Home, Players, Teams, Player History, and Null Values and reuses the query functions in `fpl_agent.queries`.
