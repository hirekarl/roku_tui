from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

_TITLE = (
    "[bold #7aa2f7] roku-tui[/bold #7aa2f7]  [dim]user guide[/dim]"
)

_LEFT = """\
[bold]Hotkeys[/bold] [dim](when not typing)[/dim]

         [bold #7aa2f7]▲[/bold #7aa2f7]
   [bold #7aa2f7]◄[/bold #7aa2f7]   [bold #bb9af7]●[/bold #bb9af7]   [bold #7aa2f7]►[/bold #7aa2f7]
         [bold #7aa2f7]▼[/bold #7aa2f7]

 [dim]arrows    → D-pad[/dim]
 [dim]Enter     → Select[/dim]
 [dim]Space     → Play/Pause[/dim]
 [dim]Backspace → Back[/dim]

[bold]Aliases[/bold]

 [bold #7aa2f7]u[/bold #7aa2f7] up      [bold #7aa2f7]d[/bold #7aa2f7] down
 [bold #7aa2f7]l[/bold #7aa2f7] left    [bold #7aa2f7]r[/bold #7aa2f7] right
 [bold #7aa2f7]s[/bold #7aa2f7] select  [bold #7aa2f7]b[/bold #7aa2f7] back
 [bold #7aa2f7]p[/bold #7aa2f7] play    [bold #7aa2f7]m[/bold #7aa2f7] mute

[bold]Repeat[/bold]

 [bold #73daca]up 3[/bold #73daca]          press 3×
 [bold #73daca]volume up 4[/bold #73daca]   4 steps up\
"""

_RIGHT = """\
[bold]Commands[/bold]

 [bold #7aa2f7]launch[/bold #7aa2f7] [dim]<name>[/dim]   fuzzy launch
 [bold #7aa2f7]apps[/bold #7aa2f7]            list channels
 [bold #7aa2f7]active[/bold #7aa2f7]          now playing
 [bold #7aa2f7]info[/bold #7aa2f7]            device info
 [bold #7aa2f7]connect[/bold #7aa2f7] [dim]<ip>[/dim]   connect Roku
 [bold #7aa2f7]macro[/bold #7aa2f7] [dim]list|run|save[/dim]
 [bold #7aa2f7]history[/bold #7aa2f7] [dim][N][/dim]     command log
 [bold #7aa2f7]stats[/bold #7aa2f7]           usage stats
 [bold #7aa2f7]sleep[/bold #7aa2f7] [dim]<s>[/dim]      pause Ns

[bold]Shortcuts[/bold]

 [bold #bb9af7]Tab[/bold #bb9af7]      autocomplete
 [bold #bb9af7]↑ ↓[/bold #bb9af7]      history
 [bold #bb9af7]Ctrl+T[/bold #bb9af7]   REPL / Remote mode
 [bold #bb9af7]Ctrl+N[/bold #bb9af7]   toggle network
 [bold #bb9af7]Ctrl+L[/bold #bb9af7]   clear REPL
 [bold #bb9af7]Ctrl+Q[/bold #bb9af7]   quit
 [bold #bb9af7]F1[/bold #bb9af7]       this guide\
"""

_FOOTER = "[dim]Escape or any key to close[/dim]"


class HelpScreen(ModalScreen):
    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "dismiss", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-body"):
            yield Static(_TITLE, id="help-title", markup=True)
            with Horizontal(id="help-cols"):
                yield Static(_LEFT, classes="help-col", markup=True)
                yield Static(_RIGHT, classes="help-col", markup=True)
            yield Static(_FOOTER, id="help-foot", markup=True)

    def on_key(self, event) -> None:
        if event.key != "escape":
            self.dismiss()
