from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static

from ..commands.suggester import RokuSuggester


class ReplPanel(Widget):
    class CommandSubmitted(Message):
        def __init__(self, line: str):
            super().__init__()
            self.line = line

    def __init__(self, suggester: RokuSuggester, **kwargs):
        super().__init__(**kwargs)
        self._suggester = suggester
        self._history: list[str] = []
        self._history_idx: int = -1

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="history-scroll")
        yield Input(
            placeholder="Type a command...  (Tab to complete, ↑↓ for history)",
            suggester=self._suggester,
            id="command-input",
        )

    def on_mount(self) -> None:
        self._show_banner()
        self.query_one("#command-input", Input).focus()

    def _show_banner(self) -> None:
        self._append(
            "[bold #7aa2f7]roku-tui[/bold #7aa2f7]  "
            "[dim]Roku Remote · REPL Edition[/dim]",
            css_class="banner",
        )
        self._append(
            "[dim]Type [bold]help[/bold] for commands · "
            "[bold]Tab[/bold] to complete · "
            "[bold]↑↓[/bold] for history · "
            "[bold]Ctrl+N[/bold] toggles network panel[/dim]",
            css_class="banner",
        )
        self._append("", css_class="spacer")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        line = event.value.strip()
        if not line:
            return
        self._history.append(line)
        self._history_idx = -1
        event.input.clear()
        self._append(f"[bold #7aa2f7]>[/bold #7aa2f7] {line}", css_class="cmd-echo")
        self.post_message(self.CommandSubmitted(line))

    def on_key(self, event) -> None:
        inp = self.query_one("#command-input", Input)
        if event.key == "up":
            if not self._history:
                return
            if self._history_idx == -1:
                self._history_idx = len(self._history) - 1
            else:
                self._history_idx = max(0, self._history_idx - 1)
            inp.value = self._history[self._history_idx]
            inp.cursor_position = len(inp.value)
            event.prevent_default()
        elif event.key == "down":
            if self._history_idx == -1:
                return
            if self._history_idx < len(self._history) - 1:
                self._history_idx += 1
                inp.value = self._history[self._history_idx]
            else:
                self._history_idx = -1
                inp.value = ""
            inp.cursor_position = len(inp.value)
            event.prevent_default()

    def output(self, content) -> None:
        self._append(content, css_class="cmd-output")

    def error(self, markup: str) -> None:
        self._append(markup, css_class="cmd-error")

    def system_message(self, markup: str) -> None:
        self._append(markup, css_class="cmd-system")

    def clear_history(self) -> None:
        scroll = self.query_one("#history-scroll", VerticalScroll)
        scroll.remove_children()
        self._show_banner()

    def _append(self, content, css_class: str = "") -> None:
        scroll = self.query_one("#history-scroll", VerticalScroll)
        if isinstance(content, str):
            widget = Static(content, classes=f"history-entry {css_class}", markup=True)
        else:
            # Rich renderable (Table, etc.)
            widget = Static(content, classes=f"history-entry {css_class}", markup=False)
        scroll.mount(widget)
        scroll.scroll_end(animate=False)
