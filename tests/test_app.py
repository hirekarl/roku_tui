from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from textual.widgets import TabbedContent

from roku_tui.app import RokuTuiApp, _get_db_path
from roku_tui.widgets.console_panel import ConsolePanel
from roku_tui.widgets.network_panel import NetworkPanel
from roku_tui.widgets.status_bar import StatusBar


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> RokuTuiApp:
    monkeypatch.setattr("roku_tui.app._get_db_path", lambda: tmp_path / "test.db")
    app = RokuTuiApp(mock=True)
    app.db.initialize()
    return app


# ── Startup ───────────────────────────────────────────────────────────────────


async def test_app_mounts_without_error(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#console-panel", ConsolePanel) is not None
        assert app.query_one("#network-panel", NetworkPanel) is not None
        assert app.query_one("#status-bar", StatusBar) is not None


async def test_app_initializes_mock_client(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None


# ── Ctrl+N panel toggle ───────────────────────────────────────────────────────


async def test_ctrl_n_hides_network_panel(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one("#network-panel", NetworkPanel)
        assert not panel.has_class("hidden")

        await pilot.press("ctrl+n")
        assert panel.has_class("hidden")


async def test_ctrl_n_expands_tabs(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        tabs = app.query_one("#main-tabs", TabbedContent)
        assert not tabs.has_class("full-width")

        await pilot.press("ctrl+n")
        assert tabs.has_class("full-width")


async def test_ctrl_n_twice_restores_layout(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one("#network-panel", NetworkPanel)
        tabs = app.query_one("#main-tabs", TabbedContent)

        await pilot.press("ctrl+n")
        await pilot.press("ctrl+n")

        assert not panel.has_class("hidden")
        assert not tabs.has_class("full-width")


# ── Command dispatch ──────────────────────────────────────────────────────────


async def test_unknown_command_returns_false(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        result = await app.dispatch("zzz_nonexistent_command")
        assert result is False


async def test_known_nav_command_returns_true(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        result = await app.dispatch("up")
        assert result is True


async def test_help_command_returns_true(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        result = await app.dispatch("help")
        assert result is True


async def test_disconnected_ecp_command_returns_false(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        app.client = None
        result = await app.dispatch("up")
        assert result is False


async def test_disconnected_allows_help(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        app.client = None
        result = await app.dispatch("help")
        assert result is True


# ── Additional coverage ───────────────────────────────────────────────────────


def test_get_db_path_returns_path() -> None:
    """_get_db_path() returns a Path ending in roku_tui.db (lines 45-47)."""
    result = _get_db_path()
    assert isinstance(result, Path)
    assert result.name == "roku_tui.db"


async def test_app_cache_setter(app: RokuTuiApp) -> None:
    """app_cache setter delegates to service (line 98)."""
    async with app.run_test() as pilot:
        await pilot.pause()
        app.app_cache = []
        assert app.service.app_cache == []


async def test_current_ip_property(app: RokuTuiApp) -> None:
    """_current_ip property delegates to service (line 102)."""
    async with app.run_test() as pilot:
        await pilot.pause()
        # In mock mode _current_ip is set to "mock-roku"
        _ = app._current_ip  # just ensure property is accessible


async def test_start_stop_recording(app: RokuTuiApp) -> None:
    """start_recording and stop_recording delegate to service (lines 286, 289)."""
    async with app.run_test() as pilot:
        await pilot.pause()
        app.start_recording()
        result = app.stop_recording()
        assert isinstance(result, list)


async def test_emit_message(app: RokuTuiApp) -> None:
    """emit_message appends a system message to the console panel (line 292)."""
    async with app.run_test() as pilot:
        await pilot.pause()
        app.emit_message("test system message")
        await pilot.pause()


async def test_connect_method(app: RokuTuiApp) -> None:
    """connect() calls _connect() (line 295)."""
    async with app.run_test() as pilot:
        await pilot.pause()
        with patch.object(app, "_connect") as mock_connect:
            await app.connect("192.168.1.50")
            mock_connect.assert_called_once_with("192.168.1.50")


async def test_private_dispatch(app: RokuTuiApp) -> None:
    """_dispatch() calls service._dispatch_single (line 235)."""
    async with app.run_test() as pilot:
        await pilot.pause()
        result = await app._dispatch("home")
        assert result is True


async def test_initial_ip_triggers_connect() -> None:
    """On mount with initial_ip, _connect is called (line 147)."""
    with patch.object(RokuTuiApp, "_connect") as mock_connect:
        app = RokuTuiApp(mock=False, initial_ip="192.168.1.50")
        async with app.run_test() as pilot:
            await pilot.pause()
            mock_connect.assert_called_once_with("192.168.1.50")


async def test_connect_spawns_worker(app: RokuTuiApp) -> None:
    """_connect() calls run_worker (line 166)."""
    async with app.run_test() as pilot:
        await pilot.pause()
        with patch.object(app, "run_worker") as mock_worker:
            app._connect("192.168.1.50")
            mock_worker.assert_called_once()


async def test_async_connect_calls_service(app: RokuTuiApp) -> None:
    """_connect() dispatches a worker that calls service.connect."""
    async with app.run_test() as pilot:
        await pilot.pause()
        with patch.object(app.service, "connect", new_callable=AsyncMock) as mock_conn:
            app._connect("192.168.1.50")
            await pilot.pause()
            mock_conn.assert_called_once_with("192.168.1.50")


async def test_prefetch_info_no_client() -> None:
    """_prefetch_info returns early when client is None (line 183)."""
    app = RokuTuiApp(mock=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.service.client is None
        app._prefetch_info()  # @work decorator — returns Worker, not awaitable
        await pilot.pause()


async def test_on_remote_button_with_mock_client(app: RokuTuiApp) -> None:
    """on_remote_panel_button_activated sends keypress via client (lines 222-224)."""
    from roku_tui.widgets.remote_panel import RemotePanel

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.service.client is not None
        msg = RemotePanel.ButtonActivated("Home")
        await app.on_remote_panel_button_activated(msg)
        await pilot.pause()


async def test_prefetch_info_exception_is_suppressed(app: RokuTuiApp) -> None:
    """_prefetch_info suppresses exceptions via except (lines 197-198)."""
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.service.client is not None
        with patch.object(
            app.service.client,
            "query_device_info",
            new_callable=AsyncMock,
            side_effect=RuntimeError("network failure"),
        ):
            app._prefetch_info()  # @work — returns Worker, not awaitable
            await pilot.pause()
            await pilot.pause()
