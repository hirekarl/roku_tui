from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Static

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

# Reverse mapping for console/hotkey feedback
CMD_TO_BTN: dict[str, str] = {
    "power": "btn-power",
    "back": "btn-back",
    "home": "btn-home",
    "up": "btn-up",
    "down": "btn-down",
    "left": "btn-left",
    "right": "btn-right",
    "select": "btn-select",
    "play": "btn-play",
    "rev": "btn-rev",
    "fwd": "btn-fwd",
    "volume up": "btn-vol-up",
    "volume down": "btn-vol-down",
    "volume mute": "btn-vol-mute",
    "vol up": "btn-vol-up",
    "vol down": "btn-vol-down",
    "vol mute": "btn-vol-mute",
    "mute": "btn-vol-mute",
}

# Normalize ECP keys to button IDs
ECP_TO_BTN: dict[str, str] = {v: k for k, v in BUTTON_MAP.items()}

# Mapping from command names to ECP keys for visual feedback
CMD_TO_ECP: dict[str, str] = {
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "select": "Select",
    "back": "Back",
    "home": "Home",
    "rev": "Rev",
    "fwd": "Fwd",
    "play": "Play",
    "volume": "VolumeMute", # Default to mute if no args, though handler is complex
    "mute": "VolumeMute",
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
    """A visual Roku remote with grid-based layout and visual feedback."""

    class ButtonActivated(Message):
        """Sent when a remote button is pressed."""

        def __init__(self, ecp_key: str) -> None:
            super().__init__()
            self.ecp_key = ecp_key

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="remote-scroll"):
            with Vertical(id="remote-content"):
                with Vertical(id="remote-wrapper"):
                    with Horizontal(id="remote-grid-container"):
                        with Static(id="remote-body"):
                            # Row 1: Back, Home, Power
                            yield Button("↩", id="btn-back", classes="btn-nav", tooltip="Back")
                            yield Button("⌂", id="btn-home", classes="btn-nav", tooltip="Home")
                            yield Button("⏻", id="btn-power", classes="btn-power", tooltip="Power")

                            # Row 2: Empty, Up, Empty
                            yield Static(classes="remote-empty")
                            yield Button("▲", id="btn-up", classes="btn-dpad")
                            yield Static(classes="remote-empty")

                            # Row 3: Left, OK, Right
                            yield Button("◄", id="btn-left", classes="btn-dpad")
                            yield Button("OK", id="btn-select", classes="btn-ok")
                            yield Button("►", id="btn-right", classes="btn-dpad")

                            # Row 4: Empty, Down, Empty
                            yield Static(classes="remote-empty")
                            yield Button("▼", id="btn-down", classes="btn-dpad")
                            yield Static(classes="remote-empty")

                            # Row 5: Vol-, Mute, Vol+
                            yield Button("−", id="btn-vol-down", classes="btn-volume", tooltip="Volume Down")
                            yield Button("⊗", id="btn-mute", classes="btn-volume", tooltip="Mute")
                            yield Button("+", id="btn-vol-up", classes="btn-volume", tooltip="Volume Up")

                            # Row 6: Rev, Play, Fwd
                            yield Button("◀◀", id="btn-rev", classes="btn-media", tooltip="Reverse")
                            yield Button("▶⏸", id="btn-play", classes="btn-media", tooltip="Play/Pause")
                            yield Button("▶▶", id="btn-fwd", classes="btn-media", tooltip="Forward")

                    yield Label(
                        "\n\n\n[bold]No Roku Connected[/bold]\n\n"
                        "Search for devices with [cyan]C[/cyan]\n"
                        "or use the [cyan]connect <ip>[/cyan] command.",
                        id="remote-empty-state",
                        markup=True
                    )

                with Static(id="remote-legend-row"):
                    yield Static(_LEGEND, id="remote-legend", markup=True)

    def on_mount(self) -> None:
        """Initial state is disconnected until explicitly set."""
        self.add_class("disconnected")

    def set_connected(self, connected: bool) -> None:
        """Toggle the visual connected/disconnected state."""
        if connected:
            self.remove_class("disconnected")
        else:
            self.add_class("disconnected")

    def flash_button(self, btn_id: str) -> None:
        """Trigger a brief visual 'pulse' on a button."""
        try:
            btn = self.query_one(f"#{btn_id}", Button)
        except Exception:
            return
        btn.add_class("btn-flash")
        self.set_timer(0.15, lambda: btn.remove_class("btn-flash"))

    def flash_by_key(self, ecp_key: str) -> None:
        """Flash a button given its ECP key (e.g. 'Home')."""
        btn_id = ECP_TO_BTN.get(ecp_key)
        if btn_id:
            self.flash_button(btn_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        ecp_key = BUTTON_MAP.get(event.button.id or "")
        if ecp_key:
            self.post_message(self.ButtonActivated(ecp_key))
