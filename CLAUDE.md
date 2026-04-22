# roku-tui

A Textual TUI for Roku remote control and ECP network traffic logging.

## Core Commands
- Run: `uv run roku-tui` (auto-discovery)
- Headless / Automation: `uv run roku-tui -c "home; sleep 2; launch Netflix"`
- Mock Mode: `uv run roku-tui --mock`
- Connect by IP: `uv run roku-tui --ip <IP>`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type Check: `uv run mypy .`
- Test: `uv run pytest`

## Standards & Practices
- **Workflow:** ALL changes MUST follow the process in `CONTRIBUTING.md` (Branching -> Quality Control -> Merge -> Release Ceremony).
- **Style:** Google-style docstrings, PEP-8 compliance, strict type hints (`mypy --strict`).
- **Pre-commit:** Hooks installed for `ruff`, `mypy`, and `pytest`. Run `uv run pre-commit install` to set up.
- **Releases:** Follow the "Release Ceremony" in `CONTRIBUTING.md`. Never tag a release unless performing the ceremony for a stable state of `main`.
- **CI/CD:** Automated CI on every push/PR; automated releases on tag push (`v*`).

## New Features
- **Headless Mode:** Automation via `-c` flag for cron jobs and scripts.
- **Network Inspector:** Interactive `DataTable` with real-time filtering (`/` hotkey) and detailed modal inspection of headers/payloads (with JSON/XML pretty-printing).
- **Deep Links:** Support for launching specific content via `link` and `yt` commands.
- **YouTube:** Direct YouTube search and launch without API keys using InnerTube.
- **Macros:** Capture and replay sequences including deep link content.
- **Guided Tour:** Interactive walkthrough of features via `F2` or `tour` command.

## Key Bindings
- **F1:** User Manual (Guide)
- **F2:** Guided Tour (Interactive)
- **F3:** About (Project Info)
- **Ctrl+T:** Console/Remote Tab
- **Ctrl+N:** Network Panel
- **Ctrl+L:** Clear Console
- **Ctrl+Q:** Quit

## Codebase Structure
- `roku_tui/app.py`: Main `App` class and top-level UI orchestration.
- `roku_tui/service.py`: Core logic for command dispatch and connection management (UI-agnostic).
- `roku_tui/service_yt.py`: YouTube InnerTube API client.
- `roku_tui/actions.py`: Mixin class for UI actions and event handlers.
- `roku_tui/constants.py`: Centralized configuration (bindings, hotkeys).
- `roku_tui/themes.py`: Centralized Textual `Theme` definitions.
- `roku_tui/mascot.py`: Rat mascot ASCII art and `ratsay()` speech-bubble formatter.
- `roku_tui/commands/`: Command registry and handlers (db, tui, network).
- `roku_tui/db/`: Database schema and persistence logic.
- `roku_tui/ecp/`: Roku ECP client, discovery, and mock simulations.
- `roku_tui/widgets/`: Interactive TUI components.
