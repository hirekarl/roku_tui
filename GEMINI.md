# GEMINI.md

This file provides guidance to Gemini CLI when working with code in this repository.

## Commands

```bash
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
```

## Architecture

**roku-tui** is a two-panel Textual TUI acting as a Roku remote and real-time ECP network logger.

### Layout

- **Left panel (Fluid)** — `TabbedContent` with `ConsolePanel` and `RemotePanel`. Uses `width: 1fr`.
- **Right panel (44 chars)** — `NetworkPanel`: live HTTP request/response log. Uses fixed width for data visibility.
- **Top** — `StatusBar`: connected device info.
- **F1** — `HelpScreen` modal.

### Command Flow

```
User input → ConsolePanel → CommandSubmitted message
  → RokuTuiApp.dispatch()
  → RokuTuiApp._dispatch()          # internal logic
  → CommandRegistry.parse()         # lookup by name or alias
  → handler (async)                 # in handlers.py or db_commands.py
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
| `commands/tui_commands.py` | UI-specific commands (`theme`, `guide`, `clear`). |
| `commands/handlers.py` | ~25 navigation and app control handlers. |
| `commands/db_commands.py` | Macro management, history, and stats. |
| `commands/suggester.py` | Tab completion logic. |
| `ecp/client.py` | Async HTTP client for Roku ECP. |
| `ecp/discovery.py` | SSDP and IP-based device discovery services. |
| `widgets/discovery_screen.py` | Interactive device selection modal. |
| `widgets/console_panel.py` | Command input with highlighting and dynamic hints. |
| `widgets/network_panel.py` | Interactive HTTP log with filtering. |
| `widgets/network_inspector.py` | Detailed modal for inspecting NetworkEvents. |
| `widgets/remote_panel.py` | Button-based remote with grid layout and feedback. |

### Engineering Standards

- **Type Safety:** `mypy --strict` compliance required. Use `Row[Any]` for DB rows.
- **Linting:** Ruff for both linting and formatting.
- **Async:** Use Textual workers (`@work`) for non-blocking UI tasks.
- **Documentation:** Google-style docstrings for all functions/classes.
- **Testing:** Always maintain 100% passing rate in `pytest`.

### Styling

The application uses a high-contrast true-black background (`black`) for the primary workspace (Console and Remote) to improve readability and focus. Custom themes (Tokyo Night, Nord, etc.) define the accent and panel colors. The Remote Panel uses a 3-column `Grid` layout with hybrid volume control placement.
