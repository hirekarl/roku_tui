from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from rich.highlighter import RegexHighlighter
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label, RichLog

from ..commands.tips import random_tip

if TYPE_CHECKING:
    from ..commands.registry import CommandRegistry
    from ..commands.suggester import RokuSuggester


class CommandHighlighter(RegexHighlighter):
    """A highlighter for Roku console commands."""

    def __init__(self, registry: CommandRegistry):
        super().__init__()
        self.registry = registry

    def highlight(self, text: Text) -> None:
        """Apply highlighting to the command input."""
        str_text = text.plain
        if not str_text:
            return

        parts = str_text.split(maxsplit=1)
        if not parts:
            return

        cmd_name = parts[0]
        cmd = self.registry.lookup(cmd_name)

        if cmd:
            # Check if it's a primary name or an alias
            if cmd_name == cmd.name:
                style = "bold #7aa2f7"  # Primary blue
            else:
                style = "bold #bb9af7"  # Secondary purple
            
            # Apply style to the first word (the command/alias)
            text.stylize(style, 0, len(cmd_name))
        else:
            # Unknown command - highlight in red
            text.stylize("bold #f7768e", 0, len(cmd_name))


class ConsolePanel(Widget):
    """The command console panel for manual interaction and output."""

    class CommandSubmitted(Message):
        """Sent when the user submits a command string."""

        def __init__(self, line: str) -> None:
            super().__init__()
            self.line = line

    def __init__(self, suggester: RokuSuggester, registry: CommandRegistry, **kwargs: Any) -> None:
        """Initialize the ConsolePanel.

        Args:
            suggester: The command and app name suggester.
            registry: The command registry for hints and highlighting.
            **kwargs: Additional widget arguments.
        """
        super().__init__(**kwargs)
        self.suggester = suggester
        self.registry = registry
        self.highlighter = CommandHighlighter(registry)

    def compose(self) -> ComposeResult:
        """Compose the console layout."""
        with Vertical(id="console-panel"):
            yield RichLog(id="history-scroll", auto_scroll=True, markup=True, wrap=True)
            yield Label("", id="command-hint")
            yield Input(
                placeholder="Type a command...  (Tab to complete, ↑↓ for history)",
                id="command-input",
                suggester=self.suggester,
                highlighter=self.highlighter,
            )

    def on_mount(self) -> None:
        """Focus the input and show the banner on mount."""
        self.query_one(Input).focus()
        self._show_banner()
        self._set_hint(f"[dim]Tip:[/dim] {random_tip()}")

    def _show_banner(self) -> None:
        """Display the welcome banner in the console."""
        title = "[bold #7aa2f7]roku-tui[/bold #7aa2f7]"
        sub = "[dim]Roku Remote · Console[/dim]"
        banner = (
            f"{title}  {sub}\n\n"
            "Press [bold]F1[/bold] for the guide · "
            "[bold]Tab[/bold] to complete · "
            "[bold]↑ ↓[/bold] for history · "
            "[bold]u d l r s[/bold] quick keys"
        )
        self._append(banner, "banner")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update inline hints as the user types."""
        val = event.value.strip()
        if not val:
            self._set_hint(f"[dim]Tip:[/dim] {random_tip()}")
            return

        parts = val.split()
        cmd_name = parts[0].lower()
        cmd = self.registry.lookup(cmd_name)

        if cmd:
            # If they just typed the command name, show help text
            if len(parts) == 1 and not event.value.endswith(" "):
                self._set_hint(cmd.help_text)
            else:
                # Show expected arguments
                if cmd.args:
                    args_str = " | ".join(cmd.args)
                    self._set_hint(f"[bold]Usage:[/bold] {cmd.name} [cyan][{args_str}][/cyan]")
                elif cmd.dynamic_args:
                    self._set_hint(f"[bold]Usage:[/bold] {cmd.name} [cyan]<args>[/cyan]")
                else:
                    self._set_hint("[dim](No arguments expected)[/dim]")
        else:
            self._set_hint(f"[red]Unknown command:[/red] {cmd_name}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission from the input widget."""
        line = event.value.strip()
        if not line:
            return

        event.input.value = ""
        self._append(f"> {line}", "cmd-echo")
        self.post_message(self.CommandSubmitted(line))
        # Reset hint to a new random tip after submission
        self._set_hint(f"[dim]Tip:[/dim] {random_tip()}")

    def on_key(self, event: Any) -> None:
        """Handle key events in the console panel."""
        if event.key == "enter":
            inp = self.query_one(Input)
            if not inp.has_focus:
                inp.focus()

    def enter_keyboard_mode(self) -> None:
        """Switch the input into keyboard passthrough mode."""
        inp = self.query_one(Input)
        inp.add_class("keyboard-mode")
        self._append(
            "[bold]⌨  KEYBOARD MODE[/bold]  "
            "[dim]Every key is sent to the TV · ESC to exit[/dim]",
            "cmd-system",
        )

    def exit_keyboard_mode(self) -> None:
        """Restore normal console input mode."""
        inp = self.query_one(Input)
        inp.remove_class("keyboard-mode")
        self._append("[dim]Keyboard mode off.[/dim]", "cmd-system")
        inp.focus()

    def clear_history(self) -> None:
        """Clear the command output history."""
        self.query_one("#history-scroll", RichLog).clear()
        self._show_banner()

    def output(self, content: Any) -> None:
        """Display command output in the console history.

        Args:
            content: The content to display (str, Text, or Table).
        """
        if isinstance(content, (str, Text, Table)):
            self._append(content, "cmd-output")

    def error(self, text: str) -> None:
        """Display an error message in the console.

        Args:
            text: The error text to display.
        """
        self._append(text, "cmd-error")

    def system_message(self, text: str) -> None:
        """Display a system message in the console.

        Args:
            text: The system message text to display.
        """
        self._append(text, "cmd-system")

    def _set_hint(self, content: str) -> None:
        """Set the content of the command hint label."""
        hint = self.query_one("#command-hint", Label)
        hint.update(content)

    def _append(self, content: Any, css_class: str = "") -> None:
        """Append content to the history scroll log.

        Args:
            content: The content to append.
            css_class: The CSS class to apply (simulated).
        """
        log = self.query_one("#history-scroll", RichLog)
        log.write(content)
