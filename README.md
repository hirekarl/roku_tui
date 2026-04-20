# roku-tui

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Textual](https://img.shields.io/badge/UI-Textual-green.svg)](https://textual.textualize.io/)
[![uv](https://img.shields.io/badge/Managed%20by-uv-purple.svg)](https://github.com/astral-sh/uv)

A Roku remote control that lives in your terminal — built for the Pursuit AI-Native program to teach **terminal fluency** and **HTTP networking**.

Every button press is a real HTTP call. Every call shows up live in the network inspector panel. You learn the commands, you see the wire.

---

## The Origin: A Case for "Outdated" UI

**roku-tui** was born out of a specific MVP build assignment: take a UI you use daily and improve it. 

Most modern Roku interfaces (the physical remote and the "slick" iOS app) are surprisingly cumbersome. They rely on slow navigation, hidden menus, and touch-screen latency. This project turns that design philosophy on its head. 

While most developers build modern web apps to improve UX, **roku-tui** makes the case that a "terminal-first" approach is actually a tremendous UX gain. By reconceiving the remote as a desktop TUI, we get:
- **Zero Latency**: Commands are sent as fast as you can type.
- **Power User Features**: Macro recording, fuzzy-search app launching, and deep-link shortcuts.
- **Observability**: A real-time view of the ECP protocol "under the hood."

Sometimes, the best way to improve a modern UI is to go back to the terminal.

---

## The Power of Local Persistence

Unlike a traditional remote, **roku-tui** is backed by a SQLite database. This transforms the app from a simple "sender of keys" into a personalized command center:

- **Lightning Fast Autocomplete**: We cache every app installed on your Roku. When you type `launch n...`, the TUI autocompletes `Netflix` instantly from local state—no network round-trips required.
- **Smart History**: Every command is logged. You can search your history with `history search` or use the `stats` command to see your most-launched apps and peak activity times.
- **Programmable Macros**: Because we store state, you can record a sequence of commands (like "Open YouTube -> Wait 2s -> Select -> Search 'Lofi'") and save it as a named macro.
- **Network Observability**: We don't just log commands; we log the raw HTTP requests and their latency. You can see exactly how the Roku ECP protocol performs in your local environment.

By adding a data layer to a remote control, we've turned an ephemeral interaction into a persistent, programmable tool.

---

## Installation

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

```bash
git clone https://github.com/pursuit-ai/roku-tui.git
cd roku-tui
```

## Quick Start

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
┌──────────────────────────────┬───────────────────────────────────┐
│ Console                      │ Network Inspector                 │
│                              │                                   │
│ > launch Netflix             │ POST /keypress/Home   200  42ms   │
│ -> Launched Netflix          │ GET  /query/apps      200  12ms   │
│                              │                                   │
│ > up 3                       │                                   │
│ -> Up x3                     │                                   │
│                              │                                   │
│ [Tab] autocomplete           │                                   │
└──────────────────────────────┴───────────────────────────────────┘
```

The app features a dual-panel layout:
- **Left Panel (Fluid)**: A `TabbedContent` area featuring the **Console** and a virtual **Remote** control.
- **Right Panel (44 chars)**: A **Network Inspector** that logs every ECP HTTP request in real time — method, path, status code, and latency. Toggle it with `Ctrl+N`.

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

*Tip: Add a count to repeat: `up 3`, `volume down 5`, `right 10`.*

### Apps & Deep Links
| Command | Description |
|---|---|
| `launch <name | alias>` | Fuzzy-match launch an app or a saved shortcut |
| `apps` | List installed channels |
| `active` | Show currently playing app |
| `link save <alias> <app> <id>` | Save a content shortcut (e.g., `link save lofi youtube dCmq...`) |
| `link list` | List all saved shortcuts |
| `yt search <query>` | Search YouTube directly from the console |
| `yt launch <id | index>` | Launch a YouTube video by ID or search result index |

<details>
<summary><b>Advanced: Device & Macros</b></summary>

#### Device Management
| Command | Description |
|---|---|
| `info` | Device name, model, serial, firmware |
| `connect <ip>` | Connect to a different Roku |
| `devices` | Known devices from history |

#### Macros
| Command | Description |
|---|---|
| `macro list` | All macros (builtin + yours) |
| `macro record` | Start recording commands into a macro |
| `macro stop <name> [desc]` | Stop recording and save as a named macro |
| `macro run <name>` | Execute a saved macro |
| `macro show <name>` | Preview a macro's steps |
| `macro delete <name>` | Delete a user macro |
| `macro set <name> abort on\|off` | Stop on first failure, or keep going |

*Macros support deep links and `sleep` for timed sequences. Six macros are pre-loaded: `morning`, `movie-night`, `sleep-timer`, `binge`, `mute-toggle`, `channel-surf`.*
</details>

<details>
<summary><b>Advanced: History, Stats & Meta</b></summary>

#### History & Stats
| Command | Description |
|---|---|
| `history [N]` | Last 20 (or N) commands |
| `history search <term>` | Search command history |
| `stats` | Top apps, top commands, days active |

#### Meta
| Command | Description |
|---|---|
| `help [command]` | Command reference — `help macro`, `help yt`, etc. |
| `clear` | Clear the console |
| `theme [name]` | Switch between `roku-night`, `catppuccin`, `nord`, `gruvbox` |
| `guide` | Open the full user manual |
</details>

---

## Keyboard Shortcuts

### Global
| Key | Action |
|---|---|
| `Tab` | Autocomplete command, app name, or subcommand |
| `↑` / `↓` | Walk command history |
| `Ctrl+T` | Toggle between Console and Remote tab |
| `Ctrl+N` | Toggle network inspector |
| `Ctrl+L` | Clear console |
| `Ctrl+Q` | Quit |
| `F1` | Quick reference card |
| `F2` | Full user guide |

### Remote tab (when not typing)
| Key | Action |
|---|---|
| Arrow keys | D-pad |
| `Enter` | Select |
| `Space` | Play/Pause |
| `Backspace` | Back |
| `H` | Home |
| `M` | Mute |
| `,` / `.` | Rewind / Fast-forward |
| `-` / `=` | Volume down / up |

---

## How it Works

Roku devices expose the **ECP (External Control Protocol)** — an HTTP API on port 8060. 
- **Navigation**: `POST /keypress/{key}`
- **App Queries**: `GET /query/apps`
- **Deep Linking**: `POST /launch/{app_id}?contentId={id}`

**roku-tui** wraps this API in a Textual TUI, routing commands through a `CommandRegistry` to specialized handlers. Every interaction is logged to a local SQLite database and rendered in the real-time Network Panel so you can watch the HTTP happen.

---

## Development

```bash
# Run app in mock mode
uv run roku-tui --mock

# Lint & Format
uv run ruff check . --fix
uv run ruff format .

# Type check
uv run mypy roku_tui/

# Tests
uv run pytest
```

The local database lives at `roku_tui.db` in the repo root.

**Stack:** Python 3.12 · Textual · httpx · SQLAlchemy Core · SQLite · uv
