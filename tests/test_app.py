from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import TabbedContent

from roku_tui.app import RokuTuiApp
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
