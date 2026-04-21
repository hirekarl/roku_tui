from __future__ import annotations

import asyncio
from typing import Any, ClassVar

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, LoadingIndicator, OptionList
from textual.widgets.option_list import Option

from ..ecp.client import EcpClient
from ..ecp.discovery import discover_rokus, probe_roku

...


class DiscoveryScreen(ModalScreen[str | None]):
    """A modal screen for discovering and selecting Roku devices on the network."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("escape", "dismiss(None)", "Cancel"),
    ]

    class DeviceSelected(Message):
        """Sent when a device is selected from the list or manually entered."""

        def __init__(self, ip: str):
            super().__init__()
            self.ip = ip

    class DiscoveryFound(Message):
        """Internal message when a device is found."""

        def __init__(self, ip: str, name: str):
            super().__init__()
            self.ip = ip
            self.name = name

    class DiscoveryFinished(Message):
        """Internal message when SSDP discovery completes."""

        pass

    def __init__(self, known_ips: list[str], **kwargs: Any):
        super().__init__(**kwargs)
        self.known_ips = known_ips
        self._found_ips: set[str] = set()

    def compose(self) -> ComposeResult:
        with Vertical(id="discovery-body"):
            yield Label("Connect to Roku", id="discovery-title")
            yield LoadingIndicator(id="discovery-loading")
            yield OptionList(id="discovery-list")

            with Vertical(id="discovery-manual-container"):
                yield Label("Enter IP Address:", classes="discovery-label")
                yield Input(placeholder="e.g. 192.168.1.50", id="discovery-ip-input")

            with Vertical(id="discovery-foot"):
                yield Button("Cancel", variant="error", id="discovery-cancel")

    def on_mount(self) -> None:
        """Start discovery workers on mount."""
        self.query_one("#discovery-list", OptionList).add_option(
            Option("Enter IP Manually...", id="manual")
        )
        self.discover_known_devices()
        self.discover_ssdp_devices()

    def on_discovery_screen_discovery_found(self, msg: DiscoveryFound) -> None:
        """Handle found device by adding to the list."""
        if msg.ip in self._found_ips:
            return
        self._found_ips.add(msg.ip)
        lst = self.query_one("#discovery-list", OptionList)
        # Add to the end of the list
        lst.add_option(Option(f"{msg.name} ({msg.ip})", id=msg.ip))

    def on_discovery_screen_discovery_finished(self, msg: DiscoveryFinished) -> None:
        """SSDP discovery is complete."""
        self.query_one("#discovery-loading").display = False

    @work(thread=True)
    def discover_known_devices(self) -> None:
        """Probe known IPs from history."""
        for ip in self.known_ips:
            if probe_roku(ip):
                name = self._get_device_name_sync(ip)
                self.post_message(self.DiscoveryFound(ip, name))

    @work(thread=True)
    def discover_ssdp_devices(self) -> None:
        """Perform SSDP discovery."""
        urls = discover_rokus(timeout=3.0)
        for url in urls:
            ip = url.split("//")[-1].split(":")[0]
            name = self._get_device_name_sync(ip)
            self.post_message(self.DiscoveryFound(ip, name))
        self.post_message(self.DiscoveryFinished())

    def _get_device_name_sync(self, ip: str) -> str:
        """Helper to get device name using a temporary event loop if needed."""

        async def _async_get() -> str:
            try:
                client = EcpClient(f"http://{ip}:8060")
                info = await client.query_device_info()
                await client.close()
                return info.friendly_name if info else "Roku Device"
            except Exception:
                return "Roku Device"

        return str(asyncio.run(_async_get()))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle device selection."""
        if event.option_id == "manual":
            self.query_one("#discovery-list").display = False
            container = self.query_one("#discovery-manual-container")
            container.add_class("visible")
            self.query_one("#discovery-ip-input").focus()
        else:
            self.post_message(self.DeviceSelected(str(event.option_id)))
            self.dismiss(str(event.option_id))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle manual IP entry."""
        ip = event.value.strip()
        if ip:
            self.post_message(self.DeviceSelected(ip))
            self.dismiss(ip)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "discovery-cancel":
            self.dismiss(None)
