from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

BUTTON_MAP: dict[str, str] = {
    "btn-power":    "Power",
    "btn-back":     "Back",
    "btn-home":     "Home",
    "btn-up":       "Up",
    "btn-down":     "Down",
    "btn-left":     "Left",
    "btn-right":    "Right",
    "btn-select":   "Select",
    "btn-play":     "Play",
    "btn-rev":      "Rev",
    "btn-fwd":      "Fwd",
    "btn-vol-up":   "VolumeUp",
    "btn-mute":     "VolumeMute",
    "btn-vol-down": "VolumeDown",
}

HOTKEY_TO_BUTTON: dict[str, str] = {
    "up":        "btn-up",
    "down":      "btn-down",
    "left":      "btn-left",
    "right":     "btn-right",
    "enter":     "btn-select",
    "space":     "btn-play",
    "backspace": "btn-back",
}


class RemotePanel(Widget):
    class ButtonActivated(Message):
        def __init__(self, ecp_key: str) -> None:
            super().__init__()
            self.ecp_key = ecp_key

    def compose(self) -> ComposeResult:
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
                yield Button("+ Vol", id="btn-vol-up", classes="btn-volume")
                yield Button("⊗ Mute", id="btn-mute", classes="btn-volume")
                yield Button("- Vol", id="btn-vol-down", classes="btn-volume")

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
