# ruff: noqa: E501
from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Static

_SECTIONS: list[tuple[str, str]] = [
    (
        "Getting Started",
        """\
[bold #7aa2f7]Getting Started[/bold #7aa2f7]

roku-tui is a terminal-based Roku remote control that gives you a
command console, a visual remote panel, and a live HTTP log of every
ECP request sent to the device.

[bold]Connecting[/bold]

On startup, roku-tui tries the most recently connected device first,
then falls back to SSDP network discovery. Once a device responds,
its name appears in the status bar at the top.

Connect manually at any time:
  [bold #73daca]connect 192.168.1.42[/bold #73daca]

Or pass an address on the command line to skip discovery entirely:
  [bold #73daca]roku-tui --ip 192.168.1.42[/bold #73daca]

Run with [bold]--mock[/bold] to simulate a device without network access.

[bold]The Console[/bold]

The input bar at the bottom accepts commands. Press Enter to run.
Use [bold]Tab[/bold] to autocomplete commands and app names.
Use [bold]↑ / ↓[/bold] to cycle through command history.

Chain multiple commands on one line with semicolons:
  [bold #73daca]home; up 3; select[/bold #73daca]

[bold]The Remote Tab[/bold]

Press [bold]Ctrl+T[/bold] to switch to the visual remote control panel.
Arrow keys still send ECP navigation commands from this tab.
Press [bold]Ctrl+T[/bold] again to return to the Console.

[bold]Getting Help[/bold]

  [bold #7aa2f7]help[/bold #7aa2f7]              show all commands
  [bold #7aa2f7]help <command>[/bold #7aa2f7]    detailed usage with examples
  [bold #7aa2f7]F1[/bold #7aa2f7]                quick reference card
  [bold #7aa2f7]F2[/bold #7aa2f7]                this guide\
""",
    ),
    (
        "Navigation",
        """\
[bold #7aa2f7]Navigation[/bold #7aa2f7]

[bold]D-Pad & Media Commands[/bold]

  [bold #7aa2f7]up  down  left  right[/bold #7aa2f7]   D-pad directions
  [bold #7aa2f7]select[/bold #7aa2f7]                   OK / confirm
  [bold #7aa2f7]back[/bold #7aa2f7]                     Back button
  [bold #7aa2f7]home[/bold #7aa2f7]                     Home screen
  [bold #7aa2f7]play  rev  fwd  replay[/bold #7aa2f7]   Media controls
  [bold #7aa2f7]mute  power  info  enter[/bold #7aa2f7]

[bold]Single-Letter Aliases[/bold]

  [bold #73daca]u[/bold #73daca] up      [bold #73daca]d[/bold #73daca] down    [bold #73daca]l[/bold #73daca] left    [bold #73daca]r[/bold #73daca] right
  [bold #73daca]s[/bold #73daca] select  [bold #73daca]b[/bold #73daca] back    [bold #73daca]p[/bold #73daca] play    [bold #73daca]m[/bold #73daca] mute

[bold]Repeat Count[/bold]

Append a number to repeat any key command:
  [bold #73daca]up 5[/bold #73daca]            send Up five times
  [bold #73daca]volume down 3[/bold #73daca]   lower volume three steps

Maximum repeat: 30.

[bold]Hotkeys (when console input is not active)[/bold]

  Arrow keys  →  D-pad
  Enter       →  Select
  Space       →  Play/Pause
  Backspace   →  Back

[bold]App Shortcuts[/bold]

  [bold #bb9af7]Ctrl+T[/bold #bb9af7]   Switch between Console and Remote tabs
  [bold #bb9af7]Ctrl+N[/bold #bb9af7]   Toggle the network inspector panel
  [bold #bb9af7]Ctrl+L[/bold #bb9af7]   Clear console history
  [bold #bb9af7]Ctrl+Q[/bold #bb9af7]   Quit
  [bold #bb9af7]Tab[/bold #bb9af7]      Autocomplete in the console
  [bold #bb9af7]↑ ↓[/bold #bb9af7]     Navigate command history\
""",
    ),
    (
        "Apps & Launching",
        """\
[bold #7aa2f7]Apps & Launching[/bold #7aa2f7]

[bold]Launch an App[/bold]

  [bold #73daca]launch netflix[/bold #73daca]
  [bold #73daca]launch tube[/bold #73daca]           ← partial names work (fuzzy match)

Apps are matched case-insensitively with fuzzy matching, so you
rarely need to type the full name.

[bold]List Installed Apps[/bold]

  [bold #73daca]apps[/bold #73daca]

The app list is cached locally after connecting and powers Tab
autocomplete for the launch command.

[bold]See What's Playing[/bold]

  [bold #73daca]active[/bold #73daca]

Shows the currently running foreground app and its ID.

[bold]Launch Deep Link Shortcuts[/bold]

If you have saved a shortcut with [bold]link save[/bold] or [bold]yt save[/bold], the same
[bold]launch[/bold] command works for them too:

  [bold #73daca]launch lofi[/bold #73daca]       ← YouTube shortcut
  [bold #73daca]launch bb[/bold #73daca]         ← Netflix deep link

See the [bold]Deep Links[/bold] and [bold]YouTube[/bold] sections for how to create shortcuts.\
""",
    ),
    (
        "YouTube",
        """\
[bold #7aa2f7]YouTube[/bold #7aa2f7]

roku-tui integrates with YouTube using InnerTube — no API key required.

[bold]Search[/bold]

  [bold #73daca]yt search lo-fi beats[/bold #73daca]

Results are displayed in a numbered table showing title, channel,
and video ID.

[bold]Launch[/bold]

  [bold #73daca]yt launch 1[/bold #73daca]                  launch first result from last search
  [bold #73daca]yt launch dQw4w9WgXcQ[/bold #73daca]        launch directly by video ID

The numeric index shorthand works only with the most recent search.

[bold]Save a Shortcut[/bold]

  [bold #73daca]yt save lofi jfKfPfyJRdk[/bold #73daca]
  [bold #73daca]launch lofi[/bold #73daca]

Saved YouTube shortcuts are stored alongside other deep links and
appear in [bold]link list[/bold]. They can be launched with [bold]launch <alias>[/bold]
in any future session.

[bold]Full Workflow Example[/bold]

  [bold #73daca]yt search chill study music[/bold #73daca]
  [bold #73daca]yt launch 2[/bold #73daca]
  [bold #73daca]yt save study jfKfPfyJRdk[/bold #73daca]
  [bold #73daca]launch study[/bold #73daca]          ← works in any future session\
""",
    ),
    (
        "Text Input",
        """\
[bold #7aa2f7]Text Input[/bold #7aa2f7]

[bold]One-Shot: type[/bold]

  [bold #73daca]type breaking bad[/bold #73daca]

Sends a string to the TV as a sequence of Lit_ ECP keypresses.
Each character is URL-encoded. Spaces and special characters work.

Use this to fill in search boxes, enter usernames, or type a URL
when a text input is active on the device.

[bold]Interactive: keyboard mode[/bold]

  [bold #73daca]kb[/bold #73daca]

Toggles live keyboard passthrough. While active:

  • Every printable key you press is sent instantly to the TV
  • Backspace → Backspace ECP keypress
  • Enter → Select ECP keypress
  • ESC → exit keyboard mode

The command input border turns [bold]accent-colored[/bold] while keyboard mode
is active as a visual reminder. Type [bold]kb[/bold] again or press ESC to exit.

Keyboard mode is ideal when you need to type multiple things in a
row, such as filling in a login form or running a search.\
""",
    ),
    (
        "Deep Links",
        """\
[bold #7aa2f7]Deep Links[/bold #7aa2f7]

Deep link shortcuts let you jump directly into specific content
on a streaming service, bypassing the service's home screen.

[bold]Save a Shortcut[/bold]

  [bold #73daca]link save <alias> <app> <content_id>[/bold #73daca]

  App can be a built-in name or a raw Roku app ID:
    [dim]youtube  netflix  hulu  disney  pluto  prime[/dim]

  [dim]Example:[/dim]  [bold #73daca]link save bb netflix tt0903747[/bold #73daca]
  [dim]Example:[/dim]  [bold #73daca]link save home pluto top[/bold #73daca]

[bold]Launch a Shortcut[/bold]

  [bold #73daca]launch bb[/bold #73daca]

The [bold]launch[/bold] command handles both app names and saved aliases.
Tab autocomplete suggests saved aliases.

[bold]List Shortcuts[/bold]

  [bold #73daca]link list[/bold #73daca]

Shows alias, app name, content ID, and launch count for all shortcuts.

[bold]Delete a Shortcut[/bold]

  [bold #73daca]link delete bb[/bold #73daca]

[bold]YouTube Shortcuts[/bold]

YouTube content saved with [bold]yt save[/bold] appears in [bold]link list[/bold] and
launches with [bold]launch <alias>[/bold] exactly like other deep links.\
""",
    ),
    (
        "Macros",
        """\
[bold #7aa2f7]Macros[/bold #7aa2f7]

Macros record a sequence of commands and replay them with a single
name. They are stored in the local database.

[bold]List Macros[/bold]

  [bold #73daca]macro list[/bold #73daca]

Built-in macros come pre-installed and are read-only.

[bold]Record a Macro[/bold]

  [bold #73daca]macro record[/bold #73daca]

Starts recording. Every successful command you run is captured until you
call [bold]macro stop[/bold]. Meta-commands (help, history, stats, etc.) are excluded.

  [bold #73daca]macro record[/bold #73daca]
  [bold #73daca]home[/bold #73daca]
  [bold #73daca]sleep 1[/bold #73daca]
  [bold #73daca]launch netflix[/bold #73daca]
  [bold #73daca]macro stop open-netflix Evening startup[/bold #73daca]

[bold]Run a Macro[/bold]

  [bold #73daca]macro run open-netflix[/bold #73daca]

Each step is echoed to the console as it runs.

[bold]Preview Steps[/bold]

  [bold #73daca]macro show open-netflix[/bold #73daca]

[bold]Abort Policy[/bold]

  [bold #73daca]macro set open-netflix abort on[/bold #73daca]
  [bold #73daca]macro set open-netflix abort off[/bold #73daca]

Controls whether the macro stops at the first failed step.
Default is [dim]continue on fail[/dim].

[bold]Delete[/bold]

  [bold #73daca]macro delete open-netflix[/bold #73daca]

[bold]Using sleep in Macros[/bold]

The [bold]sleep[/bold] command pauses for N seconds (max 30), useful for giving
a device time to respond between steps:
  [bold #73daca]home; sleep 1; launch netflix[/bold #73daca]\
""",
    ),
    (
        "Themes & Settings",
        """\
[bold #7aa2f7]Themes & Settings[/bold #7aa2f7]

[bold]Switch Theme[/bold]

  [bold #73daca]theme roku-night[/bold #73daca]    Default — Tokyo Night palette
  [bold #73daca]theme catppuccin[/bold #73daca]    Catppuccin Mocha
  [bold #73daca]theme nord[/bold #73daca]          Nord
  [bold #73daca]theme gruvbox[/bold #73daca]       Gruvbox Dark

Run [bold]theme[/bold] with no argument to see the current theme name.

[bold]Network Inspector[/bold]

  [bold #bb9af7]Ctrl+N[/bold #bb9af7]   Show / hide the network inspector panel

The inspector shows every ECP HTTP request in real time: method,
URL, status code, and response time. Useful for finding content IDs
for deep links or understanding what a remote button actually sends.

[bold]Usage Statistics[/bold]

  [bold #73daca]stats[/bold #73daca]

Shows your most-launched apps, most-used commands, and how many
days the app has been in use.

[bold]Device History[/bold]

  [bold #73daca]devices[/bold #73daca]

Lists all Roku devices roku-tui has connected to, with last-seen
timestamp and connection count. The most recently connected device
is tried first on the next startup.\
""",
    ),
]


class GuideScreen(ModalScreen[None]):
    """Full user manual as a navigable multi-section TUI document."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "dismiss", show=False),
        Binding("q", "dismiss", show=False),
        Binding("f1", "dismiss", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="guide-body"):
            yield Static(
                "[bold #7aa2f7]roku-tui[/bold #7aa2f7] [dim]User Guide[/dim]",
                id="guide-title",
                markup=True,
            )
            with Horizontal(id="guide-main"):
                with Vertical(id="guide-sidebar"):
                    yield Static(
                        "[dim] Contents[/dim]",
                        id="guide-sidebar-title",
                        markup=True,
                    )
                    yield ListView(
                        *[
                            ListItem(Label(f" {name}"), id=f"sec-{i}")
                            for i, (name, _) in enumerate(_SECTIONS)
                        ],
                        id="guide-nav",
                    )
                with VerticalScroll(id="guide-scroll"):
                    yield Static("", id="guide-content", markup=True)
            with Horizontal(id="guide-foot"):
                yield Static(
                    "[dim][bold]↑↓[/bold] navigate sections"
                    " · [bold]Tab[/bold] switch panel"
                    " · [bold]Q / ESC / F1[/bold] close[/dim]",
                    id="guide-foot-text",
                    markup=True,
                )
                yield Button("✕ Close", id="guide-close", classes="modal-close")

    def on_mount(self) -> None:
        self.query_one("#guide-nav", ListView).focus()
        self._show_section(0)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None or event.item.id is None:
            return
        try:
            idx = int(event.item.id.split("-")[1])
        except (ValueError, IndexError):
            return
        self._show_section(idx)

    def _show_section(self, idx: int) -> None:
        self.query_one("#guide-content", Static).update(_SECTIONS[idx][1])
        self.query_one("#guide-scroll", VerticalScroll).scroll_home(animate=False)
