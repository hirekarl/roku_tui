from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import Label

from roku_tui.app import RokuTuiApp
from roku_tui.widgets.discovery_screen import DiscoveryScreen
from roku_tui.widgets.remote_panel import RemotePanel


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> RokuTuiApp:
    monkeypatch.setattr("roku_tui.app._get_db_path", lambda: tmp_path / "test.db")
    app = RokuTuiApp()  # Not mock, to trigger discovery
    app.db.initialize()
    return app


async def test_discovery_modal_appears_on_startup(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, DiscoveryScreen)


async def test_remote_panel_shows_empty_state_when_disconnected(
    app: RokuTuiApp,
) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        # Dismiss discovery
        await pilot.press("escape")
        await pilot.pause()

        remote = app.query_one("#remote-panel", RemotePanel)
        assert "disconnected" in remote.classes

        empty_state = remote.query_one("#remote-empty-state", Label)
        assert empty_state.display is True


async def test_global_connect_hotkey_opens_discovery(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        # 1. Dismiss initial discovery
        await pilot.pause()
        assert isinstance(app.screen, DiscoveryScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, DiscoveryScreen)

        # 2. Trigger discovery action directly
        app.action_show_discovery()
        await pilot.pause()
        assert isinstance(app.screen, DiscoveryScreen)


async def test_mock_mode_bypasses_discovery() -> None:
    # Use a fresh app in mock mode
    app = RokuTuiApp(mock=True)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert not isinstance(app.screen, DiscoveryScreen)
        assert app.client is not None

        remote = app.query_one("#remote-panel", RemotePanel)
        assert "disconnected" not in remote.classes
