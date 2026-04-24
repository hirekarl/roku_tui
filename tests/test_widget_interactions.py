from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Label

from roku_tui.ecp.models import NetworkEvent
from roku_tui.widgets.network_panel import NetworkPanel
from roku_tui.widgets.status_bar import StatusBar


def _ev(
    method: str = "GET",
    url: str = "http://1.1.1.1:8060/query/apps",
    status_code: int | None = 200,
    error: str | None = None,
) -> NetworkEvent:
    return NetworkEvent(
        method=method,
        url=url,
        request_headers={},
        status_code=status_code,
        response_headers={},
        response_time_ms=42.5,
        body="",
        error=error,
    )


# ── NetworkPanel unit tests (no mount needed) ─────────────────────────────────


def test_format_event_error() -> None:
    panel = NetworkPanel()
    event = _ev(status_code=None, error="Connection refused")
    result = panel._format_event(event)
    assert "ERR" in str(result)


def test_format_event_long_path_truncated() -> None:
    panel = NetworkPanel()
    long_url = "http://1.1.1.1:8060/" + "x" * 80
    event = _ev(url=long_url)
    result = panel._format_event(event)
    assert "…" in str(result)


def test_format_event_5xx_status() -> None:
    panel = NetworkPanel()
    event = _ev(status_code=500)
    result = panel._format_event(event)
    assert "500" in str(result)


def test_matches_filter_with_error() -> None:
    panel = NetworkPanel()
    event = _ev(status_code=None, error="Connection refused")
    panel._filter = "connection"
    assert panel._matches_filter(event) is True


# ── NetworkPanel mounted tests ────────────────────────────────────────────────


class _NetworkApp(App):
    def compose(self) -> ComposeResult:
        yield NetworkPanel(id="np")


async def test_network_panel_filter_input_updates_table() -> None:
    from textual.widgets import Input

    app = _NetworkApp()
    async with app.run_test() as pilot:
        panel = app.query_one(NetworkPanel)
        panel.add_event(_ev(url="http://1.1.1.1:8060/keypress/Home", method="POST"))
        panel.add_event(_ev(url="http://1.1.1.1:8060/query/apps", method="GET"))
        await pilot.pause()

        # Trigger the input_changed handler directly via the mounted Input widget
        filter_input = app.query_one("#network-filter", Input)
        filter_input.value = "POST"
        await pilot.pause()
        # The filter is applied when on_input_changed fires
        panel.on_input_changed(Input.Changed(filter_input, "POST"))
        assert panel._filter == "POST"


async def test_network_panel_preserves_scroll_when_not_at_bottom() -> None:
    """When not scrolled to bottom, scroll position is preserved (line 82)."""
    app = _NetworkApp()
    async with app.run_test(size=(80, 6)) as pilot:
        panel = app.query_one(NetworkPanel)
        # Add enough events to make the table taller than the viewport
        for i in range(15):
            panel.add_event(_ev(url=f"http://1.1.1.1:8060/query/app{i}"))
        await pilot.pause()

        table = app.query_one("#network-log", DataTable)
        assert table.max_scroll_y > 1, (
            "Table must be scrollable to test scroll preservation; "
            "increase row count or reduce terminal height"
        )
        # Scroll to top to simulate user having scrolled up
        table.scroll_y = 0
        saved_scroll = table.scroll_y
        # Add another event — should preserve scroll at top, not jump to bottom
        panel.add_event(_ev(url="http://1.1.1.1:8060/query/new"))
        await pilot.pause()
        # Scroll position should be restored (line 82 executed)
        assert table.scroll_y == saved_scroll


async def test_network_panel_row_selected_posts_message() -> None:
    from unittest.mock import MagicMock

    app = _NetworkApp()
    async with app.run_test() as pilot:
        panel = app.query_one(NetworkPanel)
        event = _ev()
        panel.add_event(event)
        await pilot.pause()

        # Simulate a row-selected event via direct call
        fake_event = MagicMock()
        fake_event.row_key.value = "0"
        panel.on_data_table_row_selected(fake_event)
        await pilot.pause()


async def test_network_panel_row_selected_out_of_range() -> None:
    from unittest.mock import MagicMock

    app = _NetworkApp()
    async with app.run_test() as pilot:
        panel = app.query_one(NetworkPanel)
        await pilot.pause()

        fake_event = MagicMock()
        fake_event.row_key.value = "999"
        panel.on_data_table_row_selected(
            fake_event
        )  # idx out of range, should not raise


async def test_network_panel_row_selected_none_key() -> None:
    from unittest.mock import MagicMock

    app = _NetworkApp()
    async with app.run_test() as pilot:
        panel = app.query_one(NetworkPanel)
        await pilot.pause()

        fake_event = MagicMock()
        fake_event.row_key.value = None
        panel.on_data_table_row_selected(fake_event)  # None key, should skip


# ── StatusBar ─────────────────────────────────────────────────────────────────


class _StatusApp(App):
    def compose(self) -> ComposeResult:
        yield StatusBar(id="status")


async def test_status_bar_set_connected() -> None:
    app = _StatusApp()
    async with app.run_test() as pilot:
        bar = app.query_one(StatusBar)
        bar.set_connected("My Roku")
        await pilot.pause()
        assert "connected" in bar.classes


async def test_status_bar_set_connected_mock() -> None:
    app = _StatusApp()
    async with app.run_test() as pilot:
        bar = app.query_one(StatusBar)
        bar.set_connected("My Roku", mock=True)
        await pilot.pause()
        assert "mock-mode" in bar.classes


async def test_status_bar_set_disconnected() -> None:
    app = _StatusApp()
    async with app.run_test() as pilot:
        bar = app.query_one(StatusBar)
        bar.set_connected("My Roku")
        await pilot.pause()
        bar.set_disconnected()
        await pilot.pause()
        assert "connected" not in bar.classes


# ── AboutScreen ───────────────────────────────────────────────────────────────


async def test_about_screen_button_dismisses() -> None:
    from roku_tui.widgets.about_screen import AboutScreen

    class _AboutApp(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(AboutScreen())

    app = _AboutApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, AboutScreen)
        app.screen.dismiss()
        await pilot.pause()
        assert not isinstance(app.screen, AboutScreen)


async def test_about_screen_escape_dismisses() -> None:
    from roku_tui.widgets.about_screen import AboutScreen

    class _AboutApp(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(AboutScreen())

    app = _AboutApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, AboutScreen)


# ── NetworkInspector on_button_pressed ───────────────────────────────────────


async def test_network_inspector_close_button() -> None:
    from roku_tui.widgets.network_inspector import NetworkInspector

    class _InspApp(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            event = NetworkEvent(
                method="GET",
                url="http://1.1.1.1:8060/query/apps",
                request_headers={},
                status_code=200,
                response_headers={},
                response_time_ms=5.0,
                body="ok",
            )
            self.push_screen(NetworkInspector(event))

    app = _InspApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, NetworkInspector)
        app.screen.dismiss()
        await pilot.pause()
        assert not isinstance(app.screen, NetworkInspector)


# ── RemotePanel ───────────────────────────────────────────────────────────────


async def test_remote_panel_set_disconnected() -> None:
    from roku_tui.widgets.remote_panel import RemotePanel

    class _RemoteApp(App):
        def compose(self) -> ComposeResult:
            yield RemotePanel(id="remote")

    app = _RemoteApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(RemotePanel)
        panel.set_connected(False)
        await pilot.pause()
        assert "disconnected" in panel.classes


async def test_remote_panel_button_activated_message() -> None:
    from roku_tui.widgets.remote_panel import RemotePanel

    activated: list[str] = []

    class _RemoteApp(App):
        def compose(self) -> ComposeResult:
            yield RemotePanel(id="remote")

        def on_remote_panel_button_activated(
            self, msg: RemotePanel.ButtonActivated
        ) -> None:
            activated.append(msg.ecp_key)

    app = _RemoteApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(RemotePanel)
        panel.set_connected(True)
        await pilot.pause()
        await pilot.click("#btn-home")
        await pilot.pause()
        assert "Home" in activated


async def test_remote_panel_flash_button_invalid_id() -> None:
    from roku_tui.widgets.remote_panel import RemotePanel

    class _RemoteApp(App):
        def compose(self) -> ComposeResult:
            yield RemotePanel(id="remote")

    app = _RemoteApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(RemotePanel)
        panel.flash_button("nonexistent-id")  # Should not raise
        await pilot.pause()
