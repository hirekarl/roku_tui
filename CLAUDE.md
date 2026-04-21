# roku-tui

A Textual TUI for Roku remote control and ECP network traffic logging.

## Core Commands
- Run: `uv run roku-tui` (auto-discovery)
- Mock Mode: `uv run roku-tui --mock`
- Connect by IP: `uv run roku-tui --ip <IP>`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type Check: `uv run mypy .`
- Test: `uv run pytest`
- Single Test: `uv run pytest tests/test_handlers.py::test_launch_fuzzy_match`

## Standards & Practices
- **Style:** Google-style docstrings, PEP-8 compliance, strict type hints (`mypy --strict`).
- **Imports:** `from __future__ import annotations`, sorted with Ruff (`I001`).
- **Database:** SQLAlchemy Core (no ORM) for SQLite persistence in `roku_tui.db`.
- **UI/UX:** True-black workspace for Console and Remote tabs; visual "pulse" feedback on remote buttons; interactive Network Inspector with real-time filtering.

## UI/UX
- **Theme:** Tokyo Night palette (custom Textual `Theme`), switchable via `theme` command.
- **Interactivity:** Tab completion for commands and fuzzy app names; command history (↑↓); visual remote feedback for keyboard/console input.
- **Console:** Real-time syntax highlighting (commands/aliases/errors) and dynamic inline usage hints.
- **Feedback:** Real-time HTTP logging in `NetworkPanel` with selectable rows for detailed inspection.

## New Features
- **Network Inspector:** Interactive `DataTable` with real-time filtering (`/` hotkey) and detailed modal inspection of headers/payloads (with JSON/XML pretty-printing).
- **Deep Links:** Support for launching specific content via `link` and `yt` commands.
- **YouTube:** Direct YouTube search and launch without API keys using InnerTube.
- **Macros:** Capture and replay sequences including deep link content.
