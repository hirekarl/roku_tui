from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    device_name: reactive[str] = reactive("Not connected")
    connected: reactive[bool] = reactive(False)
    mock_mode: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Label("", id="status-device")
        yield Label("○", id="status-indicator")

    def watch_device_name(self, name: str) -> None:
        self.query_one("#status-device", Label).update(name)

    def watch_connected(self, val: bool) -> None:
        self._refresh_indicator()

    def watch_mock_mode(self, val: bool) -> None:
        self._refresh_indicator()

    def _refresh_indicator(self) -> None:
        if self.mock_mode:
            text = "● mock"
        elif self.connected:
            text = "●"
        else:
            text = "○"
        self.query_one("#status-indicator", Label).update(text)

    def set_connected(self, name: str, mock: bool = False) -> None:
        self.mock_mode = mock
        self.device_name = name
        self.connected = True

    def set_disconnected(self) -> None:
        self.connected = False
        self.mock_mode = False
        self.device_name = "Not connected"
