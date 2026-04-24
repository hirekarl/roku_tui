"""Tests for RokuActions mixin methods."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Label

from roku_tui.actions import RokuActions
from roku_tui.commands.handlers import register_all
from roku_tui.commands.registry import CommandRegistry
from roku_tui.commands.suggester import RokuSuggester
from roku_tui.ecp.models import NetworkEvent
from roku_tui.widgets.console_panel import ConsolePanel
from roku_tui.widgets.network_panel import NetworkPanel


def _make_registry() -> CommandRegistry:
    registry = CommandRegistry()
    register_all(registry)
    return registry


class _BaseActionsApp(RokuActions, App):
    def compose(self) -> ComposeResult:
        yield Label("base")


class _NetworkPanelApp(RokuActions, App):
    def compose(self) -> ComposeResult:
        yield NetworkPanel(id="network-panel")


class _ConsolePanelApp(RokuActions, App):
    def compose(self) -> ComposeResult:
        registry = _make_registry()
        suggester = RokuSuggester(registry)
        yield ConsolePanel(suggester=suggester, registry=registry, id="console-panel")


# ── action_show_manual pop path (line 73) ─────────────────────────────────────


async def test_action_show_manual_pop_when_guide_visible() -> None:
    from roku_tui.widgets.guide_screen import GuideScreen

    app = _BaseActionsApp()
    async with app.run_test() as pilot:
        app.push_screen(GuideScreen())
        await pilot.pause()
        assert isinstance(app.screen, GuideScreen)
        app.action_show_manual()
        await pilot.pause()
        assert not isinstance(app.screen, GuideScreen)


# ── action_show_about pop path (line 88) ──────────────────────────────────────


async def test_action_show_about_pop_when_about_visible() -> None:
    from roku_tui.widgets.about_screen import AboutScreen

    app = _BaseActionsApp()
    async with app.run_test() as pilot:
        app.push_screen(AboutScreen())
        await pilot.pause()
        assert isinstance(app.screen, AboutScreen)
        app.action_show_about()
        await pilot.pause()
        assert not isinstance(app.screen, AboutScreen)


# ── on_network_panel_event_selected (lines 64-66) ─────────────────────────────


async def test_on_network_panel_event_selected() -> None:
    from roku_tui.widgets.network_inspector import NetworkInspector

    app = _BaseActionsApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        ev = NetworkEvent("GET", "http://x:8060/q", {}, 200)
        msg = NetworkPanel.EventSelected(ev)
        app.on_network_panel_event_selected(msg)
        await pilot.pause()
        assert isinstance(app.screen, NetworkInspector)


# ── on_discovery_screen_device_selected (line 58) ─────────────────────────────


async def test_on_discovery_screen_device_selected() -> None:
    from roku_tui.widgets.discovery_screen import DiscoveryScreen

    connected: list[str] = []

    class _App(RokuActions, App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def _connect(self, ip: str) -> None:
            connected.append(ip)

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        msg = DiscoveryScreen.DeviceSelected("192.168.1.50")
        app.on_discovery_screen_device_selected(msg)
        await pilot.pause()
        assert "192.168.1.50" in connected


# ── action_focus_network_filter (lines 41-45) ─────────────────────────────────


async def test_action_focus_network_filter_visible() -> None:
    """Calls focus on the filter input when panel is not hidden (lines 41-45)."""
    app = _NetworkPanelApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(NetworkPanel)
        assert "hidden" not in panel.classes
        app.action_focus_network_filter()
        await pilot.pause()


async def test_action_focus_network_filter_hidden() -> None:
    """Does nothing when panel has 'hidden' class (lines 41-44, short-circuit)."""
    app = _NetworkPanelApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(NetworkPanel)
        panel.add_class("hidden")
        await pilot.pause()
        app.action_focus_network_filter()
        await pilot.pause()


# ── action_clear_console (lines 117-119) ──────────────────────────────────────


async def test_action_clear_console() -> None:
    """Calls clear_history on the ConsolePanel (lines 117-119)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.action_clear_console()
        await pilot.pause()


# ── _on_network_event (line 123) ──────────────────────────────────────────────


async def test_on_network_event_posts_message() -> None:
    """_on_network_event posts a NetworkEventReceived message (line 123)."""
    received: list[RokuActions.NetworkEventReceived] = []

    class _App(RokuActions, App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_roku_actions_network_event_received(
            self, msg: RokuActions.NetworkEventReceived
        ) -> None:
            received.append(msg)

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        ev = NetworkEvent("GET", "http://x:8060/q", {}, 200)
        app._on_network_event(ev)
        await pilot.pause()
        assert len(received) == 1
        assert received[0].event is ev
