from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from .. import __version__
from ..mascot import RAT_MARKUP_CREDITED

_TITLE = f"[bold #7aa2f7]roku-tui[/bold #7aa2f7] [dim]v{__version__} · about the project[/dim]"

_CONTENT = f"""
[bold #73daca]The Gist[/bold #73daca]

[italic]Precision remote control for people who hate imprecision.[/italic]

roku-tui turns your terminal into a full-featured Roku remote —
deep links, macros, network inspection, YouTube without an API key.
The things your stock remote pretends it can't do.

[bold #73daca]The Author[/bold #73daca]

[bold]Karl Johnson[/bold]
Senior Software Engineer · Terminal Enthusiast

[bold #bb9af7]Connect & Contribute[/bold #bb9af7]

 [bold #7aa2f7]GitHub[/bold #7aa2f7]    https://github.com/hirekarl/roku_tui
 [bold #7aa2f7]LinkedIn[/bold #7aa2f7]  https://www.linkedin.com/in/hirekarl

[dim]── Ratsmith ──────────────────────────────[/dim]

{RAT_MARKUP_CREDITED}
"""


class AboutScreen(ModalScreen[None]):
    """A modal 'About' screen with project information."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "dismiss", show=False),
        Binding("f3", "dismiss", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-body", classes="about-body"):
            yield Static(_TITLE, id="help-title", markup=True)
            with Vertical(id="help-cols"):
                yield Static(_CONTENT, id="about-content", markup=True)
            with Horizontal(id="help-foot"):
                yield Static(
                    "[dim]ESC or F3 to close[/dim]", id="help-foot-text", markup=True
                )
                yield Button("✕ Close", id="help-close", classes="modal-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
