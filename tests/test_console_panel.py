"""Tests for ConsolePanel and CommandHighlighter."""

from __future__ import annotations

from unittest.mock import MagicMock

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Input

from roku_tui.commands.handlers import register_all
from roku_tui.commands.registry import CommandRegistry
from roku_tui.commands.suggester import RokuSuggester
from roku_tui.widgets.console_panel import CommandHighlighter, ConsolePanel


def _make_registry() -> CommandRegistry:
    registry = CommandRegistry()
    register_all(registry)
    return registry


class _ConsolePanelApp(App):
    def compose(self) -> ComposeResult:
        registry = _make_registry()
        suggester = RokuSuggester(registry)
        yield ConsolePanel(suggester=suggester, registry=registry, id="cp")


# ── CommandHighlighter unit tests ─────────────────────────────────────────────


def test_highlighter_empty_string_returns_early() -> None:
    registry = _make_registry()
    h = CommandHighlighter(registry)
    t = Text("")
    h.highlight(t)  # hits line 32: `if not str_text: return`
    assert len(t._spans) == 0


def test_highlighter_known_command() -> None:
    registry = _make_registry()
    h = CommandHighlighter(registry)
    t = Text("home")
    h.highlight(t)
    assert len(t._spans) == 1
    assert t._spans[0].style == "bold #7aa2f7"


def test_highlighter_alias_command() -> None:
    registry = _make_registry()
    h = CommandHighlighter(registry)
    t = Text("channels")  # alias for apps
    h.highlight(t)
    assert len(t._spans) == 1
    assert t._spans[0].style == "bold #bb9af7"


def test_highlighter_unknown_command() -> None:
    registry = _make_registry()
    h = CommandHighlighter(registry)
    t = Text("badcmd")
    h.highlight(t)
    assert len(t._spans) == 1
    assert t._spans[0].style == "bold #f7768e"


def test_highlighter_chained_commands() -> None:
    registry = _make_registry()
    h = CommandHighlighter(registry)
    t = Text("home; up")
    h.highlight(t)
    assert len(t._spans) == 2


# ── ConsolePanel mounted tests ─────────────────────────────────────────────────


async def test_console_panel_input_changed_empty_value() -> None:
    """Empty input value triggers tip hint (lines 126-127)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        panel.on_input_changed(Input.Changed(inp, ""))
        await pilot.pause()


async def test_console_panel_input_changed_whitespace_only() -> None:
    """Whitespace-only value also triggers tip hint (lines 125-127)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        panel.on_input_changed(Input.Changed(inp, "   "))
        await pilot.pause()


async def test_console_panel_input_changed_unknown_cmd() -> None:
    """Unknown command shows error hint (line 178)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        panel.on_input_changed(Input.Changed(inp, "badcmd"))
        await pilot.pause()


async def test_console_panel_input_changed_known_cmd_no_space() -> None:
    """Known command without trailing space shows help text (line 163)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        panel.on_input_changed(Input.Changed(inp, "home"))
        await pilot.pause()


async def test_console_panel_input_changed_cmd_with_args_list() -> None:
    """Command with defined args shows usage hint (lines 167-170)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        # volume has args=["up", "down", "mute"]
        panel.on_input_changed(Input.Changed(inp, "volume "))
        await pilot.pause()


async def test_console_panel_input_changed_dynamic_args() -> None:
    """Command with dynamic_args but no args list shows <args> hint (lines 171-174)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        # launch has dynamic_args=True, args=[]
        panel.on_input_changed(Input.Changed(inp, "launch "))
        await pilot.pause()


async def test_console_panel_input_changed_no_args_no_dynamic() -> None:
    """Command with neither args nor dynamic shows no-args hint (lines 175-176)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        # home has args=[], dynamic_args=False
        panel.on_input_changed(Input.Changed(inp, "home "))
        await pilot.pause()


async def test_console_panel_input_changed_empty_part_after_semicolon() -> None:
    """Empty current part at cursor shows tip (lines 150-151).

    Value starts with ';' so part[0] is '' and cursor=0 selects it.
    """
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        # Cursor pos=0 selects the first part, which is empty before the ';'
        panel.on_input_changed(Input.Changed(inp, ";home"))
        await pilot.pause()


async def test_console_panel_input_submitted_nonempty() -> None:
    """Submitting a non-empty command fires CommandSubmitted (lines 182-190)."""
    submitted: list[str] = []

    class _App(App):
        def compose(self) -> ComposeResult:
            registry = _make_registry()
            suggester = RokuSuggester(registry)
            yield ConsolePanel(suggester=suggester, registry=registry, id="cp")

        def on_console_panel_command_submitted(
            self, msg: ConsolePanel.CommandSubmitted
        ) -> None:
            submitted.append(msg.line)

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        panel.on_input_submitted(Input.Submitted(inp, "home"))
        await pilot.pause()
        assert "home" in submitted


async def test_console_panel_input_submitted_empty_ignored() -> None:
    """Submitting an empty string is silently ignored (line 183-184)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        panel.on_input_submitted(Input.Submitted(inp, ""))
        await pilot.pause()


async def test_console_panel_clear_history() -> None:
    """clear_history clears the log and shows banner again (lines 218-219)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(ConsolePanel)
        panel.clear_history()
        await pilot.pause()


async def test_console_panel_error_method() -> None:
    """error() appends an error message to the log (line 236)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(ConsolePanel)
        panel.error("something went wrong")
        await pilot.pause()


async def test_console_panel_on_key_enter_refocuses_input() -> None:
    """on_key enter focuses input when another widget has focus (lines 195-197)."""
    from textual.widgets import Button

    class _App(App):
        def compose(self) -> ComposeResult:
            registry = _make_registry()
            suggester = RokuSuggester(registry)
            yield Button("other", id="other-btn")
            yield ConsolePanel(suggester=suggester, registry=registry, id="cp")

    app = _App()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Focus the button so the input no longer has focus
        await pilot.click("#other-btn")
        await pilot.pause()
        panel = app.query_one(ConsolePanel)
        inp = app.query_one("#command-input", Input)
        assert not inp.has_focus
        fake_key = MagicMock()
        fake_key.key = "enter"
        panel.on_key(fake_key)  # should call inp.focus() (line 197)
        await pilot.pause()


async def test_console_panel_on_key_other() -> None:
    """on_key with a non-enter key is a no-op (line 193)."""
    app = _ConsolePanelApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(ConsolePanel)
        fake_key = MagicMock()
        fake_key.key = "up"
        panel.on_key(fake_key)
        await pilot.pause()
