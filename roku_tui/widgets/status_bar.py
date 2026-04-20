from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    def compose(self) -> ComposeResult:
        yield Label("○", id="status-indicator")
        yield Label("  Not connected", id="status-device")

    def set_connected(self, name: str, mock: bool = False) -> None:
        self.query_one("#status-indicator", Label).update("●")
        suffix = " (mock)" if mock else ""
        self.query_one("#status-device", Label).update(f"  {name}{suffix}")
        self.set_class(mock, "mock-mode")
        self.set_class(not mock, "connected")

    def set_disconnected(self) -> None:
        self.query_one("#status-indicator", Label).update("○")
        self.query_one("#status-device", Label).update("  Not connected")
        self.remove_class("connected", "mock-mode")
