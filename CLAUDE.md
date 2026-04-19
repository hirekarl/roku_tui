# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run (no Roku needed)
uv run roku-tui --mock

# Run against real device
uv run roku-tui --ip 192.168.1.X

# Lint
uv run ruff check .

# Type check
uv run mypy roku_tui/

# Tests
uv run pytest

# Single test file
uv run pytest tests/test_registry.py

# Single test
uv run pytest tests/test_handlers.py::test_launch_fuzzy_match
```

## Architecture

**roku-tui** is a two-panel Textual TUI that acts as a Roku remote control while logging all ECP HTTP traffic in real time.

### Layout

- **Left panel (65%)** — `ReplPanel`: command input with tab completion, history navigation (↑↓), and scrollable output
- **Right panel (35%)** — `NetworkPanel`: live HTTP request/response log
- **Top** — `StatusBar`: connected device info
- **F1** — `HelpScreen` modal

### Command Flow

```
User input → ReplPanel → CommandSubmitted message
  → RokuTuiApp._dispatch()
  → CommandRegistry.parse()         # lookup by name or alias
  → handler (async)                 # in commands/handlers.py or db_commands.py
  → EcpClient / MockEcpClient       # HTTP to Roku port 8060
  → NetworkEvent callback           # routed to NetworkPanel + DB
  → output rendered in ReplPanel
```

### Key modules

| Path | Role |
|------|------|
| `app.py` | Textual `App` — lifecycle, device discovery, routes network events |
| `commands/registry.py` | Registers commands and aliases; parses raw input |
| `commands/handlers.py` | ~20 command handlers: navigation, apps, device info, help |
| `commands/db_commands.py` | Macro management, history search, stats |
| `commands/suggester.py` | Tab completion (commands + fuzzy app names) |
| `ecp/client.py` | Async HTTP client for Roku ECP protocol (port 8060) |
| `ecp/mock.py` | `MockEcpClient` — fake responses when `--mock` is passed |
| `ecp/discovery.py` | SSDP multicast discovery for Roku devices |
| `ecp/models.py` | `NetworkEvent`, `AppInfo`, `DeviceInfo` dataclasses |
| `db/database.py` | Public DB API |
| `db/schema.py` | SQLAlchemy tables: devices, commands, network_requests, macros, device_apps, app_launches |
| `db/seeds.py` | 6 builtin macros |
| `widgets/` | `ReplPanel`, `NetworkPanel`, `StatusBar`, `HelpScreen` |
| `roku_tui.tcss` | Textual CSS — 65/35 split, Tokyo Night theme |

### ECP Client contract

Both `EcpClient` and `MockEcpClient` accept a `network_callback: Callable[[NetworkEvent], None]` at construction. Every HTTP call fires that callback so the UI and DB can record it without polling.

### Database

SQLite file at `roku_tui.db` (repo root). SQLAlchemy Core (not ORM). Tracks commands, network requests, macro definitions, app launches, and device history. Used by `db_commands.py` handlers for `history`, `stats`, `macro *` commands.

### Styling

Tokyo Night palette, defined as a custom Textual `Theme` in `app.py` and applied in `roku_tui.tcss`. Rich markup (`[bold]`, `[green]`, etc.) is used in `ReplPanel` output via `RichLog`.
