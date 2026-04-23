# GEMINI.md

This file provides guidance to Gemini CLI when working with code in this repository.

## Commands

```bash
# Run with auto-discovery
uv run roku-tui

# Run (no Roku needed)
uv run roku-tui --mock

# Run against real device
uv run roku-tui --ip 192.168.1.X

# Lint & Format
uv run ruff check . --fix
uv run ruff format .

# Type check
uv run mypy .

# Tests
uv run pytest

# Single test
uv run pytest tests/test_handlers.py::test_launch_fuzzy_match

# Dev mode — live CSS reloading (no restart needed for .tcss changes)
uv run textual run --dev roku_tui/__main__.py

# Dev console — log sink in a separate terminal (use self.log() in code)
uv run textual console
```

## Architecture

**roku-tui** is a two-panel Textual TUI acting as a Roku remote and real-time ECP network logger.

### Layout

- **Left panel (Fluid)** — `TabbedContent` with `ConsolePanel` and `RemotePanel`. Uses `width: 1fr`.
- **Right panel (44 chars)** — `NetworkPanel`: live HTTP request/response log. Uses fixed width for data visibility.
- **Top** — `StatusBar`: connected device info.
- **F1** — `GuideScreen` modal (user manual).
- **F2** — `TourScreen` modal (interactive guided tour).
- **F3** — `AboutScreen` modal (project info + mascot).

### Command Flow

```
User input → ConsolePanel → CommandSubmitted message
  → RokuTuiApp.dispatch()
  → RokuTuiApp._dispatch()          # internal logic
  → CommandRegistry.parse()         # lookup by name or alias
  → handler (async)                 # in commands/handlers/ modules
  → EcpClient / MockEcpClient       # HTTP to Roku port 8060
  → NetworkEvent callback           # routed to NetworkPanel + DB
  → output rendered in ConsolePanel
```

### Key Modules

| Path | Role |
|------|------|
| `app.py` | Textual `App` — lifecycle, messaging, top-level orchestration. |
| `actions.py` | Mixin for UI actions, event handlers, and shared app logic. |
| `constants.py` | Global bindings, hotkeys, and behavioral constants. |
| `themes.py` | Centralized Textual `Theme` definitions. |
| `mascot.py` | Rat mascot ASCII art and `ratsay()` speech-bubble formatter. |
| `commands/tui_commands.py` | UI-specific commands (`theme`, `guide`, `clear`). |
| `commands/handlers/` | Modular command handlers (navigation, apps, fun, etc.). |
| `commands/db_commands.py` | Macro management, history, and stats. |
| `commands/suggester.py` | Tab completion logic. |
| `ecp/client.py` | Async HTTP client for Roku ECP. |
| `ecp/discovery.py` | SSDP and IP-based device discovery services. |
| `widgets/discovery_screen.py` | Device selection modal (shown at startup). |
| `widgets/tour_screen.py` | Interactive guided tour — 11 steps, F2 or `tour` command. |
| `widgets/about_screen.py` | About modal with mascot and project info, F3. |
| `widgets/console_panel.py` | Command input with highlighting and dynamic hints. |
| `widgets/network_panel.py` | Interactive HTTP log with filtering. |
| `widgets/network_inspector.py` | Detailed modal for inspecting NetworkEvents. |
| `widgets/remote_panel.py` | Button-based remote with grid layout and feedback. |

## UI/UX

- **Theme:** Tokyo Night palette (custom Textual `Theme`), switchable via `theme` command. Additional themes (Nord, Catppuccin, Gruvbox) available.
- **Interactivity:** Tab completion for commands and fuzzy app names; command history (↑↓); visual remote feedback for keyboard/console input.
- **Console:** Real-time syntax highlighting (commands/aliases/errors) and dynamic inline usage hints.
- **Network Panel:** Toggle with `Ctrl+N`. Filter with `/`. Select a row to open the network inspector modal (JSON/XML pretty-printing).

## Features

- **Headless Mode:** Automation via `-c` flag for cron jobs and scripts.
- **Network Inspector:** Interactive `DataTable` with real-time filtering and detailed modal inspection of headers/payloads.
- **Deep Links:** Launch specific content via `link` and `yt` commands.
- **YouTube:** Direct search and launch without API keys using InnerTube.
- **Macros:** Capture and replay sequences including deep link content.
- **Guided Tour:** Interactive walkthrough via `F2` or `tour` command.
- **Mascot & Brand:** Rat mascot in discovery, tour, and about screens. `ratsay <msg>` prints a cowsay-style message — works headless too.

## Engineering Standards

- **Releases:** Follow the "Release Ceremony" in `CONTRIBUTING.md`. Never tag a release unless specifically performing the ceremony for a stable state of `main`.
- **Type Safety:** `mypy --strict` compliance required. Use `Row[Any]` for DB rows.
- **Quality Control:** Pre-commit hooks (`ruff`, `mypy`, `pytest`) — run `uv run pre-commit install` to set up. GitHub CI runs on every push/PR; releases trigger on `v*` tags.
- **Linting:** Ruff for both linting and formatting.
- **Async:** Use Textual workers (`@work`) for non-blocking UI tasks.
- **Documentation:** Google-style docstrings for all functions/classes.
- **Testing:** Always maintain 100% passing rate in `pytest`.
- **Message handlers:** Textual handler names follow `on_{defining_class_snake_case}_{message_name}` — the namespace comes from the class where the `Message` subclass is *defined*, not the class that posts or receives it.

## Styling

The application uses a high-contrast true-black background (`black`) for the primary workspace (Console and Remote) to improve readability and focus. Custom themes (Tokyo Night, Nord, etc.) define the accent and panel colors. The Remote Panel uses a 3-column `Grid` layout with hybrid volume control placement.
