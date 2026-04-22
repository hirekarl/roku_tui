# roku-tui

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Textual](https://img.shields.io/badge/UI-Textual-green.svg)](https://textual.textualize.io/)
[![uv](https://img.shields.io/badge/Managed%20by-uv-purple.svg)](https://github.com/astral-sh/uv)

**Your Roku remote, inside your terminal. Type to control your TV — no phone, no plastic, no excuses.**

---

## The Problem With Every Roku Remote

You're at your computer. A show is playing on the TV. You need to pause it.

So you reach for your phone, unlock it, open the Roku app, wait for it to connect, and hit pause. Or you get up to find the physical remote. Or — be honest — you just let the show keep playing.

None of this makes sense. You have a keyboard right in front of you.

**roku-tui** is a Roku remote that lives inside your terminal. You type what you want, and it happens. No unlocking, no waiting, no getting up.

---

## What It Looks Like

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

Think of it like a search bar that controls your TV. You type what you want — `pause`, `launch Netflix`, `volume up 3` — and it happens instantly. Tab-completion means you rarely need to type more than a few characters.

> 💡 **First time here?** Press **F2** inside the app (or type `tour`) to start the **Guided Tour**. It's the fastest way to learn how to control your TV from your terminal.

---

## Five Things It Does That No Physical Remote Can

**1. Scripts for your TV (Macros)**

A physical remote can't remember sequences. In **roku-tui**, you record one, name it, and run it with a single command. Type `macro run morning` and it executes: home → wait 2 seconds → launch your news app → select. One command, zero menu-diving.

**2. Find anything, instantly**

No more scrolling through a grid of 100 apps. Type `launch net` and it finds Netflix. Save a shortcut to a specific playlist: `link save lofi youtube dCmq...`. From then on, `launch lofi` takes you directly there — not just to the app, but to that exact content.

**3. Search YouTube from your terminal**

Type `yt search lo-fi beats` and get results back in the console. Type `yt launch 1` to play the first one. No YouTube app loading screen, no autoplay algorithm, no ads to click through.

**4. Your remote remembers you**

Your Roku doesn't know you. **roku-tui** does. Every app you've launched and every command you've run is stored locally. `stats` shows your most-used apps. Tab-completion learns your favorites. The more you use it, the faster it gets.

**5. See how it works**

The right panel shows every HTTP request your Roku responds to, in real time — what gets sent, what comes back, how fast. Most apps hide their complexity. This one shows you the internet working, live, while you use it.

---

## Quick Start

**Option 1: Download a binary** (no setup required)

Grab the latest release for your platform from the [Releases page](https://github.com/hirekarl/roku_tui/releases). Download, run, done.

**Option 2: Run from source**

Ensure you have [uv](https://github.com/astral-sh/uv) installed, then:

```bash
git clone https://github.com/hirekarl/roku_tui.git
cd roku_tui

# No Roku? Use mock mode — all HTTP calls are simulated
uv run roku-tui --mock

# Auto-discover Roku on your local network
uv run roku-tui

# Or connect directly by IP
uv run roku-tui --ip 192.168.1.42
```

> **Can't find your Roku automatically?**
> On your Roku, go to **Settings → Network → About**. The IP address is listed there (it looks like `192.168.1.42`). Enter it with `--ip` and you're connected. If that menu is hard to reach, the same address is usually visible in your router's admin page under connected devices — typically at `192.168.1.1` or `192.168.0.1` in a browser.

---

## For the Developers

The prompt for this project was: **"Take a UI you use daily and improve it."**

The "obvious" move is to build a modern web app with gradients and animations. But for the Roku, the "modern" path is actually the source of the friction. Physical remotes and mobile apps are **Dumb Remotes** — stateless, forgetful, with zero bandwidth.

**roku-tui** is an argument for the **Programmable Remote**. Moving the interface into a terminal doesn't just add speed — it adds a **brain**: a local SQLite database, a command registry, a macro engine, and a real-time network inspector. Things a piece of plastic will never have.

### The Unfair TUI Advantages

- **Context-switch killer.** Reaching for a phone breaks flow. If you're already at your computer, your remote is a `Cmd+Tab` away.
- **Works over SSH.** A TUI sends text — nothing more. Control your TV from a remote machine with zero GUI dependencies.
- **Shell-native automation.** Wrap commands in a shell script, call them from cron, compose with home automation. A phone app can't do that.
- **God view.** The network panel exposes the Roku ECP protocol in real time. Turn your remote into an educational tool for how HTTP actually works.

### Who Is This For?

- **Terminal natives.** You use tmux, Neovim, or a tiling WM. Reaching for your phone to pause a video is genuinely annoying.
- **Home server / HTPC users.** SSH in and control the TV without a graphical environment or VNC session.
- **Automation people.** Cron job to mute at 11pm. Script that launches a show and dims your Hue lights.
- **Learners.** The network panel shows every ECP request live — method, path, status code, latency. It's the rare app that teaches you how it works while you use it.

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
| `launch <name \| alias>` | Fuzzy-match launch an app or a saved shortcut |
| `apps` | List installed channels |
| `active` | Show currently playing app |
| `link save <alias> <app> <id>` | Save a content shortcut (e.g., `link save lofi youtube dCmq...`) |
| `link list` | List all saved shortcuts |
| `yt search <query>` | Search YouTube directly from the console |
| `yt launch <id \| index>` | Launch a YouTube video by ID or search result index |
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
| `tour` | Start the interactive guided tour |
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
| `F1` | User Manual (Guide) |
| `F2` | Interactive Guided Tour |

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
uv run mypy .

# Tests
uv run pytest
```

The local database is stored in your OS user data directory (`~/.local/share/roku-tui/roku_tui.db` on Linux/macOS, `%LOCALAPPDATA%\roku-tui\roku_tui.db` on Windows).

**Stack:** Python 3.12 · Textual · httpx · SQLAlchemy Core · SQLite · uv

---

## Credits

**roku-tui** is maintained by **[Karl Johnson](https://www.linkedin.com/in/hirekarl/)** and was built for the [Pursuit AI-Native program](https://www.pursuit.org/ai-native-program).
