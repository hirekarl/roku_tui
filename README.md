# roku-tui

A Roku remote control that lives in your terminal — built for the Pursuit AI-Native program to teach two things at once: **terminal fluency** and **HTTP networking**.

Every button press is a real HTTP call. Every call shows up live in the network inspector panel on the right. You learn the commands, you see the wire.

---

## Quick start

```bash
# No Roku? Use mock mode — all HTTP calls are simulated
uv run roku-tui --mock

# Connect to a real device by IP
uv run roku-tui --ip 192.168.1.42

# Auto-discover Roku on your local network
uv run roku-tui
```

---
## Interface

```
┌─────────────────────────────┬──────────────────────────────┐
│  REPL                        │  HTTP Inspector              │
│                              │                              │
│  > launch Netflix            │  POST /keypress/Home   200 48ms
│  ↵ Launched Netflix          │  GET  /query/apps      200 61ms
│                              │                              │
│  > up 3                      │                              │
│  ↵ Up ×3                     │                              │
│                              │                              │
│  [Tab] autocomplete          │                              │
└─────────────────────────────┴──────────────────────────────┘
```
The left panel is a command REPL with tab-completion and persistent history. The right panel shows every ECP HTTP request in real time — method, path, status code, and latency.

---

## Commands

### Navigation
| Command | ECP key sent | Shorthand |
|---|---|---|
| `up` / `down` / `left` / `right` | D-pad | `u d l r` |
| `select` | Select | `s` |
| `back` | Back | `b` |
| `play` / `pause` | Play | `p` |
| `mute` | VolumeMute | `m` |
| `home` | Home | — |
| `power` | PowerOff | — |

Add a count to repeat: `up 3`, `volume down 5`, `right 10`.

### Apps & Deep Links
| Command | Description |
|---|---|
| `launch <name | alias>` | Fuzzy-match launch an app or a saved shortcut |
| `apps` | List installed channels |
| `active` | Show currently playing app |
| `link save <alias> <app> <id>` | Save a content shortcut (e.g., `link save lofi youtube dCmq...`) |
| `link list` | List all saved shortcuts |
| `yt search <query>` | Search YouTube directly from the REPL |
| `yt launch <id | index>` | Launch a YouTube video by ID or search result index |

### Device
| Command | Description |
|---|---|
| `info` | Device name, model, serial, firmware |
| `connect <ip>` | Connect to a different Roku |
| `devices` | Known devices from history |

### Macros
| Command | Description |
|---|---|
| `macro list` | All macros (builtin + yours) |
| `macro run <name>` | Execute a saved macro |
| `macro save <name> [desc]` | Save last 10 commands as a macro |
| `macro show <name>` | Preview a macro's steps |
| `macro delete <name>` | Delete a user macro |

Six macros are pre-loaded: `morning`, `movie-night`, `sleep-timer`, `binge`, `mute-toggle`, `channel-surf`. Macros now support deep links!

### History & stats
| Command | Description |
|---|---|
| `history [N]` | Last 20 (or N) commands |
| `history search <term>` | Search command history |
| `stats` | Top apps, top commands, days active |

### Meta
| Command | Description |
|---|---|
| `help` | Command reference |
| `clear` | Clear the REPL |
| `theme [name]` | Switch between `roku-night`, `catppuccin`, `nord`, `gruvbox` |

---

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Tab` | Autocomplete command, app name, or subcommand |
| `↑` / `↓` | Walk command history |
| Arrow keys | D-pad (when not typing) |
| `Enter` | Select (when not typing) |
| `Space` | Play/Pause (when not typing) |
| `Backspace` | Back (when not typing) |
| `Ctrl+T` | Toggle between REPL and Remote mode |
| `Ctrl+N` | Toggle network inspector |
| `Ctrl+L` | Clear REPL |
| `Ctrl+Q` | Quit |
| `F1` | User guide |

---

## How it works

Roku devices expose the **ECP (External Control Protocol)** — a plain HTTP API on port 8060. Every remote-control action is a `POST /keypress/{key}`. App queries are `GET /query/apps`. Device info is `GET /query/device-info`. Deep linking uses `POST /launch/{app_id}?contentId={id}`.

This app wraps that API in a Textual TUI, logs every call to a local SQLite database, and renders the request/response in the network panel so you can watch the HTTP happen.

---

## Development

```bash
uv run roku-tui --mock   # run app
uv run ruff check .      # lint
uv run mypy roku_tui/    # type-check
uv run pytest            # tests
```

The local database lives at `roku_tui.db` in the repo root.

**Stack:** Python 3.12 · Textual · httpx · SQLAlchemy Core · SQLite · uv
