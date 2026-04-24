from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Button, Label

from roku_tui.widgets.help_screen import HelpScreen


class _HelpApp(App):
    def compose(self) -> ComposeResult:
        yield Label("base")

    def on_mount(self) -> None:
        self.push_screen(HelpScreen())


async def test_help_screen_mounts() -> None:
    app = _HelpApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, HelpScreen)


async def test_help_screen_has_close_button() -> None:
    app = _HelpApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        btn = app.screen.query_one("#help-close", Button)
        assert btn is not None


async def test_help_screen_close_button_dismisses() -> None:
    app = _HelpApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, HelpScreen)
        screen = app.screen
        assert isinstance(screen, HelpScreen)
        screen.dismiss()
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)


async def test_help_screen_escape_dismisses() -> None:
    app = _HelpApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)


async def test_help_screen_f1_dismisses() -> None:
    app = _HelpApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("f1")
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)
