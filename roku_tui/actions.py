from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from textual.message import Message
from textual.widgets import Button, Input, TabbedContent

if TYPE_CHECKING:
    from .db import Database
    from .ecp.models import NetworkEvent
    from .widgets.discovery_screen import DiscoveryScreen
    from .widgets.network_panel import NetworkPanel


class RokuAppProtocol(Protocol):
    """Protocol defining the interface required by RokuActions."""

    db: Database

    def push_screen(self, screen: Any) -> Any: ...
    def pop_screen(self) -> Any: ...
    def query_one(self, selector: str, expect_type: Any) -> Any: ...
    def post_message(self, message: Message) -> Any: ...
    def _connect(self, url: str) -> None: ...
    @property
    def screen(self) -> Any: ...


class RokuActions:
    """Mixin class for RokuTuiApp actions and event handlers."""

    class NetworkEventReceived(Message):
        """Internal message sent when an ECP network event occurs."""

        def __init__(self, event: NetworkEvent):
            super().__init__()
            self.event = event

    def action_focus_network_filter(self: RokuAppProtocol) -> None:
        """Focus the network filter input if the panel is visible."""
        from .widgets.network_panel import NetworkPanel

        panel = self.query_one("#network-panel", NetworkPanel)
        if not panel.has_class("hidden"):
            panel.query_one("#network-filter", Input).focus()

    def action_show_discovery(self: RokuAppProtocol) -> None:
        """Show the interactive Roku discovery screen."""
        from .widgets.discovery_screen import DiscoveryScreen

        known_ips = self.db.known_device_ips()
        self.push_screen(DiscoveryScreen(known_ips=known_ips))

    def on_discovery_screen_device_selected(
        self: RokuAppProtocol, msg: DiscoveryScreen.DeviceSelected
    ) -> None:
        """Handle device selection from the discovery screen."""
        self._connect(msg.ip)

    def on_network_panel_event_selected(
        self: RokuAppProtocol, msg: NetworkPanel.EventSelected
    ) -> None:
        """Show the inspection modal when a network event is selected."""
        from .widgets.network_inspector import NetworkInspector

        self.push_screen(NetworkInspector(msg.event))

    def action_show_guide(self: RokuAppProtocol) -> None:
        """Toggle the F1 quick reference card."""
        from .widgets.help_screen import HelpScreen

        if isinstance(self.screen, HelpScreen):
            self.pop_screen()
        else:
            self.push_screen(HelpScreen())

    def action_show_manual(self: RokuAppProtocol) -> None:
        """Toggle the F2 full user guide."""
        from .widgets.guide_screen import GuideScreen

        if isinstance(self.screen, GuideScreen):
            self.pop_screen()
        else:
            self.push_screen(GuideScreen())

    def action_show_tour(self: RokuAppProtocol) -> None:
        """Show the interactive guided tour."""
        from .widgets.tour_screen import TourScreen

        self.push_screen(TourScreen())

    def action_toggle_tab(self: RokuAppProtocol) -> None:
        """Toggle between Console and Remote tabs (Ctrl+T)."""
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-console":
            tabs.active = "tab-remote"
            self.query_one("#btn-up", Button).focus()
        else:
            tabs.active = "tab-console"
            self.query_one("#command-input", Input).focus()

    def action_toggle_network(self: RokuAppProtocol) -> None:
        """Show or hide the network inspector panel (Ctrl+N)."""
        from .widgets.network_panel import NetworkPanel

        panel = self.query_one("#network-panel", NetworkPanel)
        tabs = self.query_one("#main-tabs", TabbedContent)
        if "hidden" in panel.classes:
            panel.remove_class("hidden")
            tabs.remove_class("full-width")
        else:
            panel.add_class("hidden")
            tabs.add_class("full-width")

    def action_clear_console(self: RokuAppProtocol) -> None:
        """Clear the console history scrollback."""
        from .widgets.console_panel import ConsolePanel

        self.query_one("#console-panel", ConsolePanel).clear_history()

    def _on_network_event(self: RokuAppProtocol, event: NetworkEvent) -> None:
        """Internal callback passed to the ECP client to route network traffic."""
        self.post_message(self.NetworkEventReceived(event))
