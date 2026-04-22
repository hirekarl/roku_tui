from __future__ import annotations

import random

TIPS: list[str] = [
    "Chain commands with semicolons: [bold]home; up 3; select[/bold]",
    "Press [bold]Tab[/bold] to autocomplete commands and app names.",
    "Repeat any command N times: [bold]up 3[/bold]  or  [bold]volume up 5[/bold]",
    "YouTube: [bold]yt search jazz[/bold] → [bold]yt launch 1[/bold] to play",
    "[bold]kb[/bold] toggles live keyboard passthrough — ESC to exit.",
    "Send text to the TV in one shot: [bold]type my search query[/bold]",
    "Deep link: [bold]link save alias app id[/bold] → [bold]launch alias[/bold]",
    "[bold]Ctrl+T[/bold] switches between the Console and the Remote tab.",
    "[bold]macro record[/bold] → run commands → [bold]macro stop <name>[/bold]",
    "Open the full user manual with [bold]F1[/bold] or [bold]guide[/bold].",
    "Navigate command history with [bold]↑[/bold] and [bold]↓[/bold] in the console.",
    "Themes: [bold]nord[/bold]  [bold]catppuccin[/bold]  [bold]gruvbox[/bold]",
    "[bold]help <command>[/bold] shows detailed docs — try [bold]help yt[/bold]",
    "Search command history: [bold]history search netflix[/bold]",
    "[bold]sleep <seconds>[/bold] adds delays between macro steps.",
]


def random_tip() -> str:
    """Return a random startup tip."""
    return random.choice(TIPS)


LONG_HELP: dict[str, str] = {
    "yt": """\
[bold #7aa2f7]yt[/bold #7aa2f7] [dim]/ youtube[/dim] — YouTube integration

  [bold]yt search[/bold] [dim]<query>[/dim]
    Search YouTube and display a numbered results table.

    [dim]Example:[/dim]  yt search late night jazz
    [dim]Example:[/dim]  yt search breaking bad trailer

  [bold]yt launch[/bold] [dim]<index | video_id>[/dim]
    Launch from last search by result number, or directly by YouTube video ID.

    [dim]Example:[/dim]  yt launch 1
    [dim]Example:[/dim]  yt launch dQw4w9WgXcQ

  [bold]yt save[/bold] [dim]<alias> <video_id>[/dim]
    Save a video as a named shortcut. Launch any time with [bold]launch <alias>[/bold].

    [dim]Example:[/dim]  yt lofi jfKfPfyJRdk
    [dim]Then:[/dim]     launch lofi
""",
    "youtube": "See [bold]help yt[/bold].",
    "apps": """\
[bold #7aa2f7]apps[/bold #7aa2f7] [dim]/ channels[/dim] — list installed apps

  Displays a table of all apps installed on the connected Roku device,
  including their App ID, Name, and Version.

  Use these names or IDs with the [bold]launch[/bold] command.
""",
    "channels": "See [bold]help apps[/bold].",
    "active": """\
[bold #7aa2f7]active[/bold #7aa2f7] [dim]/ now[/dim] — show currently active app

  Identifies the app that is currently in the foreground on the Roku.
  Displays the app name and its App ID.
""",
    "now": "See [bold]help active[/bold].",
    "macro": """\
[bold #7aa2f7]macro[/bold #7aa2f7] — record and replay command sequences

  [bold]macro list[/bold]
    Show all macros. Built-in macros are read-only.

  [bold]macro record[/bold]
    Start recording. Every successful command you run is captured until
    you call [bold]macro stop[/bold]. Meta-commands (help, history, etc.) are excluded.

  [bold]macro stop[/bold] [dim]<name> [description][/dim]
    Stop recording and save the captured commands as a named macro.

    [dim]Example:[/dim]  macro record
                home
                sleep 1
                launch netflix
                macro stop open-netflix Evening startup

  [bold]macro run[/bold] [dim]<name>[/dim]
    Run a macro by name. Each step is echoed to the console as it executes.

    [dim]Example:[/dim]  macro run open-netflix

  [bold]macro show[/bold] [dim]<name>[/dim]
    Preview the command sequence a macro will run.

  [bold]macro delete[/bold] [dim]<name>[/dim]
    Delete a user-defined macro. Built-in macros cannot be deleted.

  [bold]macro set[/bold] [dim]<name> abort on|off[/dim]
    Control whether the macro stops on the first failed step.
    Default is [dim]continue on fail[/dim].
""",
    "link": """\
[bold #7aa2f7]link[/bold #7aa2f7] [dim]/ shortcut[/dim] — manage deep link shortcuts

  [bold]link list[/bold]
    Show all saved shortcuts.

  [bold]link save[/bold] [dim]<alias> <app> <content_id>[/dim]
    Save a deep link shortcut. App can be a built-in name or a raw Roku app ID.

    Built-in app names:  youtube  netflix  hulu  disney  pluto  prime

    [dim]Example:[/dim]  link save bb netflix tt0903747
    [dim]Example:[/dim]  link save home-feed pluto top

    Launch any saved shortcut with [bold]launch <alias>[/bold].

  [bold]link delete[/bold] [dim]<alias>[/dim]
    Remove a saved shortcut.

    [dim]Example:[/dim]  link delete bb
""",
    "shortcut": "See [bold]help link[/bold].",
    "launch": """\
[bold #7aa2f7]launch[/bold #7aa2f7] — open an app or deep link shortcut

  [bold]launch[/bold] [dim]<app name>[/dim]
    Fuzzy-match and launch an installed app by name. Partial names work.

    [dim]Example:[/dim]  launch netflix
    [dim]Example:[/dim]  launch tube     ← matches YouTube

  [bold]launch[/bold] [dim]<alias>[/dim]
    Launch a shortcut created with [bold]link save[/bold] or [bold]yt save[/bold].

    [dim]Example:[/dim]  launch lofi

  Use [bold]apps[/bold] to list all installed apps on the device.
  Use [bold]active[/bold] to see what is currently running.
""",
    "kb": """\
[bold #7aa2f7]kb[/bold #7aa2f7] [dim]/ keyboard[/dim] — live keyboard passthrough mode

  Toggles keyboard passthrough. While active, every keystroke is sent
  directly to the TV as a Lit_ ECP keypress.

    Printable keys  →  sent to TV
    Backspace       →  Backspace ECP keypress
    Enter           →  Select ECP keypress
    ESC             →  exit keyboard mode

  The command input border turns accent-colored while keyboard mode
  is active as a visual reminder.

  Use [bold]type <text>[/bold] to send a full string at once without entering
  keyboard mode.
""",
    "keyboard": "See [bold]help kb[/bold].",
    "type": """\
[bold #7aa2f7]type[/bold #7aa2f7] — send text to the TV as keypresses

  [bold]type[/bold] [dim]<text>[/dim]
    Sends each character as a URL-encoded Lit_ ECP keypress in sequence.
    Spaces and special characters are handled automatically.

    [dim]Example:[/dim]  type breaking bad
    [dim]Example:[/dim]  type hello@world.com

  For interactive typing one key at a time, use [bold]kb[/bold] to toggle
  keyboard passthrough mode instead.
""",
    "connect": """\
[bold #7aa2f7]connect[/bold #7aa2f7] — connect to a Roku device

  [bold]connect[/bold] [dim]<ip>[/dim]
    Connect to a Roku at the given IP address. Closes the current connection first.

    [dim]Example:[/dim]  connect 192.168.1.42

  On startup, roku-tui tries the most recently connected device first,
  then falls back to SSDP network discovery.

  Use [bold]devices[/bold] to see all previously connected devices.
  Use [bold]--ip <address>[/bold] on the command line to skip discovery entirely.
""",
    "volume": """\
[bold #7aa2f7]volume[/bold #7aa2f7] [dim]/ vol[/dim] — control TV volume

  [bold]volume up[/bold] [dim][N][/dim]     Raise volume N steps (default 1)
  [bold]volume down[/bold] [dim][N][/dim]   Lower volume N steps
  [bold]volume mute[/bold]        Toggle mute

  [dim]Example:[/dim]  volume up 3
  [dim]Example:[/dim]  vol mute
""",
    "vol": "See [bold]help volume[/bold].",
    "theme": """\
[bold #7aa2f7]theme[/bold #7aa2f7] — switch the color palette

  [bold]theme[/bold] [dim]<name>[/dim]
    Switch to the named theme immediately.

  Available themes:
    [bold]roku-night[/bold]   Default — Tokyo Night palette
    [bold]catppuccin[/bold]   Catppuccin Mocha
    [bold]nord[/bold]         Nord
    [bold]gruvbox[/bold]      Gruvbox Dark

  Run [bold]theme[/bold] with no argument to see the current theme.
""",
    "history": """\
[bold #7aa2f7]history[/bold #7aa2f7] [dim]/ hist[/dim] — command history

  [bold]history[/bold] [dim][N][/dim]
    Show the last N commands (default 20).

    [dim]Example:[/dim]  history 50

  [bold]history search[/bold] [dim]<term>[/dim]
    Search command history by content.

    [dim]Example:[/dim]  history search netflix

  In the console, use [bold]↑[/bold] and [bold]↓[/bold] to navigate history as you type.
""",
    "hist": "See [bold]help history[/bold].",
    "sleep": """\
[bold #7aa2f7]sleep[/bold #7aa2f7] — pause execution

  [bold]sleep[/bold] [dim]<seconds>[/dim]
    Pause for the given number of seconds. Maximum is 30.
    Most useful inside macros to add delays between steps.

    [dim]Example:[/dim]  sleep 2
    [dim]Macro use:[/dim]  home; sleep 1; launch netflix
""",
    "devices": """\
[bold #7aa2f7]devices[/bold #7aa2f7] [dim]/ devs[/dim] — known device history

  Lists all Roku devices roku-tui has previously connected to,
  with IP address, friendly name, model, last-seen timestamp,
  and total connection count.

  On startup, the most recently connected device is tried first
  before falling back to SSDP discovery.
""",
    "devs": "See [bold]help devices[/bold].",
    "stats": """\
[bold #7aa2f7]stats[/bold #7aa2f7] — usage statistics

  Shows your most-launched apps, most-used commands, and the number
  of days the app has been active.
""",
    "info": """\
[bold #7aa2f7]info[/bold #7aa2f7] [dim]/ device[/dim] — device information

  Displays hardware and software details about the connected Roku:
  friendly name, model, serial number, software version, and MAC addresses.
""",
    "device": "See [bold]help info[/bold].",
    "guide": """\
[bold #7aa2f7]guide[/bold #7aa2f7] — open the full user manual

  Opens the multi-section user guide as a TUI document.
  Navigate sections with [bold]↑ / ↓[/bold], scroll content with arrow keys or mouse.
  Press [bold]Q[/bold] or [bold]ESC[/bold] to close.

  Also available via [bold]F1[/bold].
""",
    "help": """\
[bold #7aa2f7]help[/bold #7aa2f7] [dim]/ ?[/dim] — show command help

  [bold]help[/bold]
    Lists all available commands grouped by category.

  [bold]help[/bold] [dim]<command>[/dim]
    Shows detailed documentation and examples for a specific command.

    [dim]Example:[/dim]  help yt
    [dim]Example:[/dim]  help macro
""",
    "tour": """\
[bold #7aa2f7]tour[/bold #7aa2f7] — start the interactive guided tour

  Starts a multi-step interactive walkthrough of the roku-tui interface.
  It highlights key features like the Console, Remote, and Network panels.

  Also available via [bold]F2[/bold].
""",
    "about": """\
[bold #7aa2f7]about[/bold #7aa2f7] — show project information

  Displays a modal with information about roku-tui, including the version,
  author, and a nice ASCII rat mascot.

  Also available via [bold]F3[/bold].
""",
    "clear": """\
[bold #7aa2f7]clear[/bold #7aa2f7] [dim]/ cls[/dim] — clear console history

  Wipes all output from the console panel. Does not affect command history.

  Also available via [bold]Ctrl+L[/bold].
""",
    "version": """\
[bold #7aa2f7]version[/bold #7aa2f7] [dim]/ v[/dim] — show current version

  Displays the current version of roku-tui.
""",
    "ratsay": """\
[bold #7aa2f7]ratsay[/bold #7aa2f7] — print a message with the mascot

  [bold]ratsay[/bold] [dim]<message>[/dim]
    Prints the rat mascot with a speech bubble containing your message.
    Works just like cowsay. If no message is provided, the rat will
    have something random to say.

    [dim]Example:[/dim]  ratsay Hello from Roku!
    [dim]Example:[/dim]  ratsay

  This command is particularly useful in headless mode ([bold]-c[/bold])
  to add some character to your automation scripts.
""",
}
