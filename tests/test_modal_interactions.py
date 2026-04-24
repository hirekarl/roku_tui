"""Tests for modal screen button events and tour screen navigation."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Button, Label

from roku_tui.ecp.models import NetworkEvent
from roku_tui.widgets.network_panel import NetworkPanel

# ── NetworkPanel.EventSelected ────────────────────────────────────────────────


def test_event_selected_init() -> None:
    event = NetworkEvent("GET", "http://x:8060/q", {}, 200)
    msg = NetworkPanel.EventSelected(event)
    assert msg.event is event


# ── on_button_pressed via direct call ─────────────────────────────────────────


async def test_help_screen_on_button_pressed() -> None:
    from roku_tui.widgets.help_screen import HelpScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(HelpScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, HelpScreen)
        btn = screen.query_one("#help-close", Button)
        screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)


async def test_about_screen_on_button_pressed() -> None:
    from roku_tui.widgets.about_screen import AboutScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(AboutScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, AboutScreen)
        btn = screen.query_one("#help-close", Button)
        screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()
        assert not isinstance(app.screen, AboutScreen)


async def test_network_inspector_on_button_pressed() -> None:
    from roku_tui.widgets.network_inspector import NetworkInspector

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            ev = NetworkEvent("GET", "http://x:8060/q", {}, 200)
            self.push_screen(NetworkInspector(ev))

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NetworkInspector)
        btn = screen.query_one("#inspector-close", Button)
        screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()
        assert not isinstance(app.screen, NetworkInspector)


# ── GuideScreen events ────────────────────────────────────────────────────────


async def test_guide_screen_button_dismisses() -> None:
    from roku_tui.widgets.guide_screen import GuideScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(GuideScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, GuideScreen)
        # on_button_pressed with any button calls dismiss
        btn = screen.query_one(Button)
        screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()
        assert not isinstance(app.screen, GuideScreen)


async def test_guide_screen_list_highlighted_none_item() -> None:
    from textual.widgets import ListView

    from roku_tui.widgets.guide_screen import GuideScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(GuideScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, GuideScreen)
        lv = screen.query_one("#guide-nav", ListView)
        # Simulate highlight with None item - should return early without error
        event = ListView.Highlighted(lv, None)
        screen.on_list_view_highlighted(event)


async def test_guide_screen_list_highlighted_bad_id() -> None:
    from textual.widgets import ListItem, ListView

    from roku_tui.widgets.guide_screen import GuideScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(GuideScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, GuideScreen)
        lv = screen.query_one("#guide-nav", ListView)
        # Create ListItem with a bad ID format (not parseable as int)
        bad_item = ListItem(id="section-bad")
        event = ListView.Highlighted(lv, bad_item)
        screen.on_list_view_highlighted(event)  # Should not raise


# ── TourScreen navigation ─────────────────────────────────────────────────────


async def test_tour_screen_next_and_prev() -> None:
    from roku_tui.widgets.tour_screen import TourScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(TourScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, TourScreen)

        # Step forward
        initial_step = screen.step_index
        screen.action_next_step()
        await pilot.pause()
        assert screen.step_index == initial_step + 1

        # Step backward
        screen.action_prev_step()
        await pilot.pause()
        assert screen.step_index == initial_step


async def test_tour_screen_prev_at_first_step_does_nothing() -> None:
    from roku_tui.widgets.tour_screen import TourScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(TourScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, TourScreen)
        assert screen.step_index == 0
        screen.action_prev_step()
        await pilot.pause()
        assert screen.step_index == 0  # Should not go below 0


async def test_tour_screen_last_step_dismiss() -> None:
    from roku_tui.widgets.tour_screen import _STEPS, TourScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(TourScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, TourScreen)
        # Jump to last step
        screen.step_index = len(_STEPS) - 1
        screen._update_step()
        await pilot.pause()
        # Next from last step should dismiss
        screen.action_next_step()
        await pilot.pause()
        assert not isinstance(app.screen, TourScreen)


async def test_tour_screen_button_next() -> None:
    from roku_tui.widgets.tour_screen import TourScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(TourScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, TourScreen)
        initial = screen.step_index
        btn = screen.query_one("#tour-next", Button)
        screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()
        assert screen.step_index == initial + 1


async def test_tour_screen_button_prev() -> None:
    from roku_tui.widgets.tour_screen import TourScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(TourScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, TourScreen)
        # Move to step 1 first
        screen.step_index = 1
        screen._update_step()
        await pilot.pause()
        btn = screen.query_one("#tour-prev", Button)
        screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()
        assert screen.step_index == 0


async def test_tour_screen_button_close() -> None:
    from roku_tui.widgets.tour_screen import TourScreen

    class _App(App):
        def compose(self) -> ComposeResult:
            yield Label("base")

        def on_mount(self) -> None:
            self.push_screen(TourScreen())

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, TourScreen)
        btn = screen.query_one("#tour-skip", Button)
        screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()
        assert not isinstance(app.screen, TourScreen)
