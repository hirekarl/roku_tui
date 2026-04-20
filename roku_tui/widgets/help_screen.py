from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

_TITLE = "[bold #7aa2f7]roku-tui[/bold #7aa2f7] [dim]quick reference[/dim]"

_LEFT = """\
[bold]Common Patterns[/bold]

 [bold #73daca]yt search jazz; yt launch 1[/bold #73daca]
 [dim]→ search and launch YouTube[/dim]

 [bold #73daca]up 5; select[/bold #73daca]
 [dim]→ navigate and confirm[/dim]

 [bold #73daca]launch netflix[/bold #73daca]
 [dim]→ fuzzy-match by name[/dim]

 [bold #73daca]type my search[/bold #73daca]
 [dim]→ send text to the TV[/dim]

 [bold #73daca]kb[/bold #73daca]
 [dim]→ live keyboard mode · ESC to exit[/dim]

 [bold #73daca]macro record[/bold #73daca] [dim]/ [bold]macro stop name[/bold][/dim]
 [dim]→ record then save a macro[/dim]

 [bold #73daca]link save alias netflix id[/bold #73daca]
 [dim]→ create a deep link shortcut[/dim]

[bold]Learn More[/bold]

 [bold #7aa2f7]help <command>[/bold #7aa2f7]   detailed docs + examples
 [bold #7aa2f7]guide[/bold #7aa2f7] [dim]/ F2[/dim]       full user manual\
"""

_RIGHT = """\
[bold]Shortcuts[/bold]

 [bold #bb9af7]Ctrl+T[/bold #bb9af7]     Console / Remote tab
 [bold #bb9af7]Ctrl+N[/bold #bb9af7]     network inspector
 [bold #bb9af7]Ctrl+L[/bold #bb9af7]     clear console
 [bold #bb9af7]Ctrl+Q[/bold #bb9af7]     quit
 [bold #bb9af7]Tab[/bold #bb9af7]        autocomplete
 [bold #bb9af7]↑ ↓[/bold #bb9af7]        command history

[bold]Key Aliases[/bold]

 [bold #73daca]u d l r[/bold #73daca]   up/down/left/right
 [bold #73daca]s b p m[/bold #73daca]   select/back/play/mute

[bold]Repeat & Chain[/bold]

 [bold #73daca]up 3[/bold #73daca]           press 3 times
 [bold #73daca]volume up 4[/bold #73daca]    4 volume steps
 [bold #73daca]a; b; c[/bold #73daca]        chain commands\
"""


class HelpScreen(ModalScreen[None]):
    """A modal quick-reference card."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "dismiss", show=False),
        Binding("f1", "dismiss", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-body"):
            yield Static(_TITLE, id="help-title", markup=True)
            with VerticalScroll(id="help-cols"), Horizontal():
                yield Static(_LEFT, classes="help-col", markup=True)
                yield Static(_RIGHT, classes="help-col", markup=True)
            with Horizontal(id="help-foot"):
                yield Static(
                    "[dim]ESC or F1 to close[/dim]", id="help-foot-text", markup=True
                )
                yield Button("✕ Close", id="help-close", classes="modal-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
