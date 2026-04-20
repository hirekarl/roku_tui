from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Static

BUTTON_MAP: dict[str, str] = {
    "btn-power": "Power",
    "btn-back": "Back",
    "btn-home": "Home",
    "btn-up": "Up",
    "btn-down": "Down",
    "btn-left": "Left",
    "btn-right": "Right",
    "btn-select": "Select",
    "btn-play": "Play",
    "btn-rev": "Rev",
    "btn-fwd": "Fwd",
    "btn-vol-up": "VolumeUp",
    "btn-mute": "VolumeMute",
    "btn-vol-down": "VolumeDown",
}

HOTKEY_TO_BUTTON: dict[str, str] = {
    "up": "btn-up",
    "down": "btn-down",
    "left": "btn-left",
    "right": "btn-right",
    "enter": "btn-select",
    "space": "btn-play",
    "backspace": "btn-back",
}

REMOTE_HOTKEY_TO_BTN: dict[str, str] = {
    "h": "btn-home",
    "m": "btn-mute",
    ",": "btn-rev",
    ".": "btn-fwd",
    "=": "btn-vol-up",
    "-": "btn-vol-down",
}

_LEGEND = """\
[dim]───── Keyboard Shortcuts ──────[/dim]
 [bold]↑↓←→[/bold]  D-pad    [bold]Enter[/bold]   OK
 [bold]Space[/bold]  Play     [bold]⌫[/bold]       Back
 [bold]H[/bold]      Home     [bold]M[/bold]       Mute
 [bold],[/bold]      Rev      [bold].[/bold]       Fwd
 [bold]-[/bold]      Vol−     [bold]=[/bold]       Vol+\
"""


class RemotePanel(Widget):
    class ButtonActivated(Message):
        def __init__(self, ecp_key: str) -> None:
            super().__init__()
            self.ecp_key = ecp_key

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="remote-scroll"), Vertical(id="remote-content"):
            with Vertical(id="remote-body"):
                with Horizontal(classes="remote-row"):
                    yield Button("⏻  Power", id="btn-power", classes="btn-power")
                with Horizontal(classes="remote-row"):
                    yield Button("↩  Back", id="btn-back", classes="btn-nav")
                    yield Button("⌂  Home", id="btn-home", classes="btn-nav")
                with Vertical(classes="dpad"):
                    with Horizontal(classes="remote-row"):
                        yield Button("▲", id="btn-up", classes="btn-dpad")
                    with Horizontal(classes="remote-row"):
                        yield Button("◄", id="btn-left", classes="btn-dpad")
                        yield Button("OK", id="btn-select", classes="btn-ok")
                        yield Button("►", id="btn-right", classes="btn-dpad")
                    with Horizontal(classes="remote-row"):
                        yield Button("▼", id="btn-down", classes="btn-dpad")
                with Horizontal(classes="remote-row"):
                    yield Button("◀◀", id="btn-rev", classes="btn-media")
                    yield Button("▶  ⏸", id="btn-play", classes="btn-media")
                    yield Button("▶▶", id="btn-fwd", classes="btn-media")
                with Horizontal(classes="remote-row"):
                    yield Button("- Vol", id="btn-vol-down", classes="btn-volume")
                    yield Button("⊗ Mute", id="btn-mute", classes="btn-volume")
                    yield Button("+ Vol", id="btn-vol-up", classes="btn-volume")
            with Horizontal(id="remote-legend-row"):
                yield Static(_LEGEND, id="remote-legend", markup=True)

    def flash_button(self, btn_id: str) -> None:
        try:
            btn = self.query_one(f"#{btn_id}", Button)
        except Exception:
            return
        btn.add_class("btn-flash")
        self.set_timer(0.15, lambda: btn.remove_class("btn-flash"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        ecp_key = BUTTON_MAP.get(event.button.id or "")
        if ecp_key:
            self.post_message(self.ButtonActivated(ecp_key))
