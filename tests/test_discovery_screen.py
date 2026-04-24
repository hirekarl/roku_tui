"""Tests for DiscoveryScreen."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Label, OptionList
from textual.widgets.option_list import Option

from roku_tui.widgets.discovery_screen import DiscoveryScreen

# ── Message unit tests ────────────────────────────────────────────────────────


def test_discovery_found_init() -> None:
    """DiscoveryFound message stores ip and name (lines 33-34)."""
    msg = DiscoveryScreen.DiscoveryFound("192.168.1.1", "My Roku")
    assert msg.ip == "192.168.1.1"
    assert msg.name == "My Roku"


# ── DiscoveryScreen mounted tests ─────────────────────────────────────────────


class _DiscApp(App):
    def compose(self) -> ComposeResult:
        yield Label("base")

    def on_mount(self) -> None:
        self.push_screen(DiscoveryScreen(known_ips=[]))


async def test_discovery_screen_mounts() -> None:
    app = _DiscApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, DiscoveryScreen)


async def test_discovery_screen_dedup_found(monkeypatch: object) -> None:
    """Duplicate DiscoveryFound messages are ignored (line 79)."""
    app = _DiscApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DiscoveryScreen)
        screen._found_ips.add("192.168.1.1")
        # Second call with same IP should return early
        msg = DiscoveryScreen.DiscoveryFound("192.168.1.1", "Roku")
        screen.on_discovery_screen_discovery_found(msg)
        await pilot.pause()


async def test_discovery_screen_found_adds_option() -> None:
    """New DiscoveryFound message adds an item to the list (line 80-83)."""
    app = _DiscApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DiscoveryScreen)
        lst = screen.query_one("#discovery-list", OptionList)
        initial_count = lst.option_count
        msg = DiscoveryScreen.DiscoveryFound("10.0.0.1", "Bedroom Roku")
        screen.on_discovery_screen_discovery_found(msg)
        await pilot.pause()
        assert lst.option_count == initial_count + 1


async def test_discovery_screen_finished_hides_spinner() -> None:
    """DiscoveryFinished hides the loading indicator (line 87)."""
    app = _DiscApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DiscoveryScreen)
        msg = DiscoveryScreen.DiscoveryFinished()
        screen.on_discovery_screen_discovery_finished(msg)
        await pilot.pause()
        loading = screen.query_one("#discovery-loading")
        assert not loading.display


async def test_discovery_screen_option_manual_shows_input() -> None:
    """Selecting 'manual' hides list and shows manual container (lines 123-127)."""
    app = _DiscApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DiscoveryScreen)
        lst = screen.query_one("#discovery-list", OptionList)
        manual_option = lst.get_option("manual")
        event = OptionList.OptionSelected(lst, manual_option, 0)
        screen.on_option_list_option_selected(event)
        await pilot.pause()
        assert not lst.display


async def test_discovery_screen_option_device_selected() -> None:
    """Selecting a device option dismisses with the IP (lines 128-130)."""
    dismissed: list[str | None] = []

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(DiscoveryScreen(known_ips=[]), callback=dismissed.append)

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DiscoveryScreen)
        # Manually add a device to the list
        lst = screen.query_one("#discovery-list", OptionList)
        lst.add_option(Option("Roku (10.0.0.2)", id="10.0.0.2"))
        await pilot.pause()
        device_option = lst.get_option("10.0.0.2")
        event = OptionList.OptionSelected(lst, device_option, lst.option_count - 1)
        screen.on_option_list_option_selected(event)
        await pilot.pause()
        assert "10.0.0.2" in dismissed


async def test_discovery_screen_input_submitted() -> None:
    """Submitting an IP in the manual input dismisses with that IP (lines 134-137)."""
    dismissed: list[str | None] = []

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(DiscoveryScreen(known_ips=[]), callback=dismissed.append)

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DiscoveryScreen)
        inp = screen.query_one("#discovery-ip-input", Input)
        screen.on_input_submitted(Input.Submitted(inp, "192.168.5.10"))
        await pilot.pause()
        assert "192.168.5.10" in dismissed


async def test_discovery_screen_input_submitted_empty_ignored() -> None:
    """Submitting empty string does nothing (line 135 guard)."""
    app = _DiscApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DiscoveryScreen)
        inp = screen.query_one("#discovery-ip-input", Input)
        screen.on_input_submitted(Input.Submitted(inp, ""))
        await pilot.pause()
        assert isinstance(app.screen, DiscoveryScreen)


async def test_discovery_screen_cancel_button() -> None:
    """Cancel button dismisses the screen (lines 140-141)."""
    dismissed: list[str | None] = []

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(DiscoveryScreen(known_ips=[]), callback=dismissed.append)

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DiscoveryScreen)
        btn = screen.query_one("#discovery-cancel", Button)
        screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()
        assert not isinstance(app.screen, DiscoveryScreen)
        assert None in dismissed


# ── Thread worker paths ───────────────────────────────────────────────────────


def test_get_device_name_sync_exception_path() -> None:
    """_get_device_name_sync returns 'Roku Device' on any exception (lines 116-117).

    Must be sync because _get_device_name_sync calls asyncio.run() internally,
    which cannot be called from a running event loop.
    """
    screen = DiscoveryScreen(known_ips=[])
    with patch("roku_tui.widgets.discovery_screen.EcpClient") as MockClient:
        MockClient.return_value.query_device_info = AsyncMock(
            side_effect=RuntimeError("network error")
        )
        MockClient.return_value.close = AsyncMock()
        result = screen._get_device_name_sync("192.168.1.1")
    assert result == "Roku Device"


async def test_discover_ssdp_posts_found_message() -> None:
    """discover_ssdp_devices parses URLs and posts DiscoveryFound (lines 102-104)."""

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(DiscoveryScreen(known_ips=[]))

    app = _App()
    with (
        patch(
            "roku_tui.widgets.discovery_screen.discover_rokus",
            return_value=["http://10.0.0.5:8060"],
        ),
        patch.object(
            DiscoveryScreen, "_get_device_name_sync", return_value="Test Roku"
        ),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(
                0.2
            )  # give thread worker time to post message and have it processed
            screen = app.screen
            assert isinstance(screen, DiscoveryScreen)
            assert "10.0.0.5" in screen._found_ips
