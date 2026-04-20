# roku-tui

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Textual](https://img.shields.io/badge/UI-Textual-green.svg)](https://textual.textualize.io/)
[![uv](https://img.shields.io/badge/Managed%20by-uv-purple.svg)](https://github.com/astral-sh/uv)

A Roku remote control that lives in your terminal — built to replace a "slick" but cumbersome interface with a high-performance, keyboard-driven cockpit.

---

## The Thesis: Why a Terminal?

The prompt for this project was: **"Take a UI you use daily and improve it."**

In an AI-Native world, the "obvious" move is to build a modern web app with gradients and animations. But for the Roku, the "modern" path is actually the source of the friction. Physical remotes and mobile apps are **"Dumb Remotes"** — they are stateless, forgetful, and have zero bandwidth.

**roku-tui** is an argument for the **Programmable Remote**. By moving the interface into a terminal, we don't just get speed; we get a remote with a **brain** (a local SQLite database) that can do things a piece of plastic never could.

### The "Unfair" TUI Advantages

1. **Macros (Scripts for your TV)**: A physical remote can't remember a sequence. In **roku-tui**, you can record a "Morning Routine" macro: `home -> sleep 2 -> launch YouTube -> sleep 1 -> select`. One command, zero menu diving.
2. **Fuzzy "Content-First" Launching**: Don't waste time scrolling through a grid of 100 apps. Use fuzzy search to launch apps instantly, or use **Deep Links** to jump directly to a specific YouTube video or Netflix show with a single keyword alias.
3. **The "God View" (Network Observability)**: Most UIs hide their complexity. **roku-tui** exposes it. The real-time network panel shows you exactly how the Roku ECP protocol works, turning your remote into an educational tool for how the internet actually functions.
4. **The Context-Switch Killer**: Reaching for a physical remote or unlocking a phone is a "context switch" that breaks your flow. If you're already at your computer, your remote is now just a `Cmd+Tab` away. You never have to leave your keyboard (or your seat) to adjust the volume or pause a show.
5. **Local Memory**: Your Roku doesn't know you. **roku-tui** does. It tracks your stats, remembers your most-launched apps, and provides instant tab-completion for your favorites based on your actual history.

---

## Quick Start

Ensure you have [uv](https://github.com/astral-sh/uv) installed, then clone and run:

```bash
git clone https://github.com/pursuit-ai/roku-tui.git
cd roku-tui

# No Roku? Use mock mode — all HTTP calls are simulated
uv run roku-tui --mock

# Connect to a real device by IP
uv run roku-tui --ip 192.168.1.42

# Auto-discover Roku on your local network
uv run roku-tui
```

---

## The Interface

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
- **Right Panel (44 chars)**: A **Network Inspector** that logs every ECP HTTP request in real time. Toggle it with `Ctrl+N`.

---

## The Power of Local Persistence

Traditional remotes are ephemeral. **roku-tui** is backed by a SQLite database, turning it into a personalized command center:

- **Instant Autocomplete**: We cache every app on your Roku. Type `launch n...` and it autocompletes `Netflix` instantly from local state—zero network round-trips.
- **Smart History**: Every command is logged. Search your history or use `stats` to see your most-launched apps and peak activity times.
- **Programmable Macros**: Record a sequence (e.g., "Open YouTube -> Wait 2s -> Select -> Search 'Lofi'") and save it as a named macro.
- **Network Observability**: Watch the HTTP latency of the Roku ECP protocol in real-time.

---

## Commands

### Navigation
| Command | ECP key sent | Shorthand |
|---|---|---|
| `up` / `down` / `left` / `right` | D-pad | `u d l r` |
| `select` | Select | `s` |
| `back` | Back | `b` |
| `play` / `pause` | Play | `p` (play) |
| `rev` / `fwd` | Rev / Fwd | — |
| `replay` | InstantReplay | — |
| `home` | Home | — |
| `mute` | VolumeMute | `m` |
| `volume <up\|down\|mute>` | Volume control | `vol` |
| `power` | Power | — |
| `info` | Info | — |
| `enter` | Enter | — |

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
| `type <text>` | Send a text string to the Roku |
| `kb` | Toggle live keyboard passthrough mode |

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
| `sleep <seconds>` | Pause execution (max 30s) — useful in macros |

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
| `clear` | Clear the console (alias: `cls`) |
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

## Development

```bash
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

---

## Credits

**roku-tui** is maintained by **[Karl Johnson](https://www.linkedin.com/in/hirekarl/)** and was built for the [Pursuit AI-Native program](https://www.pursuit.org/ai-native-program).
