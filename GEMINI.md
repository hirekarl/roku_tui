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
uv run mypy roku_tui/

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
  → RokuTuiApp._dispatch()
  → CommandRegistry.parse()         # lookup by name or alias
  → handler (async)                 # in handlers.py or db_commands.py
  → EcpClient / MockEcpClient       # HTTP to Roku port 8060
  → NetworkEvent callback           # routed to NetworkPanel + DB
  → output rendered in ConsolePanel
```

### Key Modules

| Path | Role |
|------|------|
| `app.py` | Textual `App` — lifecycle, theme management, messaging. |
| `commands/handlers.py` | ~25 handlers: navigation, apps, deep links, YouTube. |
| `commands/db_commands.py` | Macro management, history, stats, sleep. |
| `commands/suggester.py` | Tab completion (commands + fuzzy app names). |
| `ecp/client.py` | Async HTTP client for Roku ECP (port 8060). |
| `ecp/mock.py` | `MockEcpClient` — simulation for development. |
| `service.py` | `YouTubeClient` using InnerTube for search. |
| `db/database.py` | SQLite API wrapper with SQLAlchemy Core. |
| `db/schema.py` | Tables: devices, commands, requests, macros, links. |
| `widgets/` | `ConsolePanel`, `NetworkPanel`, `RemotePanel`, `StatusBar`. |

### Engineering Standards

- **Type Safety:** `mypy --strict` compliance required. Use `Row[Any]` for DB rows.
- **Linting:** Ruff for both linting and formatting.
- **Async:** Use Textual workers (`@work`) for non-blocking UI tasks.
- **Documentation:** Google-style docstrings for all functions/classes.
- **Testing:** Always maintain 100% passing rate in `pytest`.

### Styling

Custom themes (Tokyo Night, Nord, etc.) defined in `app.py` and applied via `roku_tui.tcss`. Tabbed content uses custom active-state indicators.
