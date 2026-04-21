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
- Dev Mode (live CSS reload): `uv run textual run --dev roku_tui/__main__.py`
- Dev Console (log sink): `uv run textual console` (run in a separate terminal)

## Standards & Practices
- **Style:** Google-style docstrings, PEP-8 compliance, strict type hints (`mypy --strict`).
- **Pre-commit:** Hooks installed for `ruff`, `mypy`, and `pytest`. Run `uv run pre-commit install` to set up.
- **CI/CD:** Automated CI on every push/PR; automated releases on tag push (`v*`).

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
- **Guided Tour:** Interactive walkthrough of features via `F3` or `tour` command.

## Key Bindings
- **F1:** Quick Reference
- **F2:** User Manual
- **F3:** Guided Tour
- **Ctrl+T:** Console/Remote Tab
- **Ctrl+N:** Network Panel
- **Ctrl+L:** Clear Console
- **Ctrl+Q:** Quit

## Codebase Structure
- `roku_tui/app.py`: Main `App` class and top-level UI orchestration.
- `roku_tui/actions.py`: Mixin class for UI actions and event handlers.
- `roku_tui/constants.py`: Centralized configuration (bindings, hotkeys).
- `roku_tui/themes.py`: Centralized Textual `Theme` definitions.
- `roku_tui/commands/`: Command registry and handlers (db, tui, network).
- `roku_tui/db/`: Database schema and persistence logic.
- `roku_tui/ecp/`: Roku ECP client, discovery, and mock simulations.
- `roku_tui/widgets/`: Interactive TUI components.
