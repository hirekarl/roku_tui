from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, RichLog

from ..commands.tips import random_tip

if TYPE_CHECKING:
    from ..commands.suggester import RokuSuggester


class ConsolePanel(Widget):
    """The command console panel for manual interaction and output."""

    class CommandSubmitted(Message):
        """Sent when the user submits a command string."""

        def __init__(self, line: str) -> None:
            super().__init__()
            self.line = line

    def __init__(self, suggester: RokuSuggester, **kwargs: Any) -> None:
        """Initialize the ConsolePanel.

        Args:
            suggester: The command and app name suggester.
            **kwargs: Additional widget arguments.
        """
        super().__init__(**kwargs)
        self.suggester = suggester

    def compose(self) -> ComposeResult:
        """Compose the console layout."""
        with Vertical(id="console-panel"):
            yield RichLog(id="history-scroll", auto_scroll=True, markup=True, wrap=True)
            yield Input(
                placeholder="Type a command...  (Tab to complete, ↑↓ for history)",
                id="command-input",
                suggester=self.suggester,
            )

    def on_mount(self) -> None:
        """Focus the input and show the banner on mount."""
        self.query_one(Input).focus()
        self._show_banner()
        self._append(f"[dim]Tip:[/dim] {random_tip()}", "cmd-system")

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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission from the input widget."""
        line = event.value.strip()
        if not line:
            return

        event.input.value = ""
        self._append(f"> {line}", "cmd-echo")
        self.post_message(self.CommandSubmitted(line))

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

    def _append(self, content: Any, css_class: str = "") -> None:
        """Append content to the history scroll log.

        Args:
            content: The content to append.
            css_class: The CSS class to apply (simulated).
        """
        log = self.query_one("#history-scroll", RichLog)
        log.write(content)
