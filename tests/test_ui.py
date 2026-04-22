from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import TabbedContent

from roku_tui.app import RokuTuiApp
from roku_tui.widgets.console_panel import ConsolePanel
from roku_tui.widgets.guide_screen import GuideScreen
from roku_tui.widgets.help_screen import HelpScreen
from roku_tui.widgets.about_screen import AboutScreen
from roku_tui.widgets.tour_screen import TourScreen


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> RokuTuiApp:
    monkeypatch.setattr("roku_tui.app._get_db_path", lambda: tmp_path / "test.db")
    app = RokuTuiApp(mock=True)
    app.db.initialize()
    return app


# ── Modal lifecycle ────────────────────────────────────────────────────────────


async def test_f1_opens_guide_screen(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f1")
        await pilot.pause()
        assert isinstance(app.screen, GuideScreen)


async def test_f1_closes_guide_screen(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f1")
        await pilot.pause()
        await pilot.press("f1")
        await pilot.pause()
        assert not isinstance(app.screen, GuideScreen)


async def test_escape_closes_guide_screen(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f1")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, GuideScreen)


async def test_f2_opens_tour_screen(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f2")
        await pilot.pause()
        assert isinstance(app.screen, TourScreen)


async def test_screen_stack_depth_on_startup(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        assert len(app.screen_stack) == 1


async def test_screen_stack_depth_with_guide_modal(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f1")
        await pilot.pause()
        assert len(app.screen_stack) == 2


async def test_screen_stack_depth_with_tour_modal(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f2")
        await pilot.pause()
        assert len(app.screen_stack) == 2


async def test_only_one_modal_pushed_per_key(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f1")
        await pilot.pause()
        await pilot.press("f1")  # closes
        await pilot.pause()
        await pilot.press("f1")  # reopens — should be exactly one modal
        await pilot.pause()
        assert len(app.screen_stack) == 2
        assert isinstance(app.screen, GuideScreen)


# ── Modals do not leak ECP keypresses ─────────────────────────────────────────


async def test_arrow_keys_not_sent_to_tv_in_guide_modal(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await pilot.press("f1")
        await pilot.pause()
        assert isinstance(app.screen, GuideScreen)
        await pilot.press("up")
        await pilot.press("down")
        await pilot.press("left")
        await pilot.press("right")
        await pilot.pause()
        assert keypresses == []


# ── Tab switching ─────────────────────────────────────────────────────────────


async def test_console_tab_is_active_on_startup(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        tabs = app.query_one("#main-tabs", TabbedContent)
        assert tabs.active == "tab-console"


async def test_ctrl_t_switches_to_remote_tab(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("ctrl+t")
        await pilot.pause()
        tabs = app.query_one("#main-tabs", TabbedContent)
        assert tabs.active == "tab-remote"


async def test_ctrl_t_toggles_back_to_console(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("ctrl+t")
        await pilot.pause()
        await pilot.press("ctrl+t")
        await pilot.pause()
        tabs = app.query_one("#main-tabs", TabbedContent)
        assert tabs.active == "tab-console"


# ── Universal hotkeys ─────────────────────────────────────────────────────────


async def test_up_arrow_sends_ecp_on_remote_tab(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await pilot.press("ctrl+t")
        await pilot.pause()
        await pilot.press("up")
        await pilot.pause()
        assert "Up" in keypresses


async def test_space_sends_play_on_remote_tab(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await pilot.press("ctrl+t")
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert "Play" in keypresses


async def test_backspace_sends_back_on_remote_tab(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await pilot.press("ctrl+t")
        await pilot.pause()
        await pilot.press("backspace")
        await pilot.pause()
        assert "Back" in keypresses


# ── Remote-only hotkeys ───────────────────────────────────────────────────────


async def test_h_sends_home_on_remote_tab(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await pilot.press("ctrl+t")
        await pilot.pause()
        await pilot.press("h")
        await pilot.pause()
        assert "Home" in keypresses


async def test_m_sends_mute_on_remote_tab(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await pilot.press("ctrl+t")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()
        assert "VolumeMute" in keypresses


async def test_remote_hotkeys_blocked_when_modal_open_over_remote_tab(
    app: RokuTuiApp,
) -> None:
    """Open a modal while on the Remote tab; hotkeys must not reach the TV."""
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await pilot.press("ctrl+t")  # switch to Remote
        await pilot.pause()
        await pilot.press("f1")  # open guide modal
        await pilot.pause()
        assert isinstance(app.screen, GuideScreen)
        await pilot.press("h")  # would be Home on Remote tab without modal
        await pilot.press("up")  # would be Up
        await pilot.pause()
        assert keypresses == []


# ── Keyboard mode ─────────────────────────────────────────────────────────────


async def test_kb_command_enters_keyboard_mode(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        assert not app._kb_mode
        await app.dispatch("kb")
        await pilot.pause()
        assert app._kb_mode


async def test_escape_exits_keyboard_mode(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.dispatch("kb")
        await pilot.pause()
        assert app._kb_mode
        await pilot.press("escape")
        await pilot.pause()
        assert not app._kb_mode


async def test_printable_key_in_kb_mode_sends_lit_keypress(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await app.dispatch("kb")
        await pilot.pause()
        assert app._kb_mode
        await pilot.press("a")
        await pilot.pause()
        assert any(k.startswith("Lit_") for k in keypresses)


async def test_enter_in_kb_mode_sends_select(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await app.dispatch("kb")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert "Select" in keypresses


async def test_backspace_in_kb_mode_sends_backspace(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await app.dispatch("kb")
        await pilot.pause()
        await pilot.press("backspace")
        await pilot.pause()
        assert "Backspace" in keypresses


async def test_arrow_key_in_kb_mode_does_not_send_ecp_nav(app: RokuTuiApp) -> None:
    """In keyboard mode, up is a literal keypress (Lit_...) not an ECP Up."""
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        await app.dispatch("kb")
        await pilot.pause()
        await pilot.press("up")
        await pilot.pause()
        assert "Up" not in keypresses


# ── Console command chaining ───────────────────────────────────────────────────


async def test_semicolon_chain_dispatches_all_commands(app: RokuTuiApp) -> None:
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        app.post_message(ConsolePanel.CommandSubmitted("up; down; left"))
        await pilot.pause()
        assert keypresses == ["Up", "Down", "Left"]


async def test_semicolon_chain_stops_on_unknown_command(app: RokuTuiApp) -> None:
    """An unknown command mid-chain still allows valid commands after it to run."""
    keypresses: list[str] = []

    async def track(key: str) -> None:
        keypresses.append(key)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.client is not None
        app.client.keypress = track  # type: ignore[method-assign]
        app.post_message(ConsolePanel.CommandSubmitted("up; zzz_bad; down"))
        await pilot.pause()
        # up and down both run; bad command in the middle just errors
        assert "Up" in keypresses
        assert "Down" in keypresses


# ── About screen lifecycle ─────────────────────────────────────────────────────


async def test_f3_opens_about_screen(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f3")
        await pilot.pause()
        assert isinstance(app.screen, AboutScreen)


async def test_f3_closes_about_screen(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f3")
        await pilot.pause()
        await pilot.press("f3")
        await pilot.pause()
        assert not isinstance(app.screen, AboutScreen)


async def test_about_command_opens_screen(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.dispatch("about")
        await pilot.pause()
        assert isinstance(app.screen, AboutScreen)
