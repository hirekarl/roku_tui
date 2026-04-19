import re
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

DPAD = """\
[dim]─────────────────────────────[/dim]
[bold]  Hotkeys[/bold] [dim](when not typing)[/dim]

        [bold #7aa2f7][ ▲ ][/bold #7aa2f7]
   [bold #7aa2f7][ ◄ ][/bold #7aa2f7] [bold #bb9af7][ ● ][/bold #bb9af7] [bold #7aa2f7][ ► ][/bold #7aa2f7]
        [bold #7aa2f7][ ▼ ][/bold #7aa2f7]

  [dim]Arrow keys  →  D-pad[/dim]
  [dim]Enter       →  Select[/dim]
  [dim]Space       →  Play / Pause[/dim]
  [dim]Backspace   →  Back[/dim]
[dim]─────────────────────────────[/dim]\
"""

ALIASES = """\
[bold]  Quick aliases[/bold]

  [bold #7aa2f7]u[/bold #7aa2f7]  up        [bold #7aa2f7]d[/bold #7aa2f7]  down
  [bold #7aa2f7]l[/bold #7aa2f7]  left      [bold #7aa2f7]r[/bold #7aa2f7]  right
  [bold #7aa2f7]s[/bold #7aa2f7]  select    [bold #7aa2f7]b[/bold #7aa2f7]  back
  [bold #7aa2f7]p[/bold #7aa2f7]  play      [bold #7aa2f7]m[/bold #7aa2f7]  mute

[bold]  Repeat syntax[/bold]

  [bold #73daca]up 3[/bold #73daca]         press 3×
  [bold #73daca]right 5[/bold #73daca]      press 5×
  [bold #73daca]volume up 4[/bold #73daca]  4 steps up\
"""

COMMANDS = """\
[bold]  Commands[/bold]

  [bold #7aa2f7]launch[/bold #7aa2f7] [dim]<name>[/dim]    fuzzy app launch
  [bold #7aa2f7]apps[/bold #7aa2f7]             list channels
  [bold #7aa2f7]active[/bold #7aa2f7]           now playing
  [bold #7aa2f7]info[/bold #7aa2f7]             device details
  [bold #7aa2f7]connect[/bold #7aa2f7] [dim]<ip>[/dim]    connect device
  [bold #7aa2f7]macro[/bold #7aa2f7] [dim]list|run|save[/dim]
  [bold #7aa2f7]history[/bold #7aa2f7] [dim][N][/dim]      command log
  [bold #7aa2f7]history search[/bold #7aa2f7] [dim]<t>[/dim]
  [bold #7aa2f7]stats[/bold #7aa2f7]            usage stats
  [bold #7aa2f7]devices[/bold #7aa2f7]          known devices\
"""

SHORTCUTS = """\
[bold]  Keyboard shortcuts[/bold]

  [bold #bb9af7]Tab[/bold #bb9af7]      autocomplete
  [bold #bb9af7]↑ ↓[/bold #bb9af7]      command history
  [bold #bb9af7]Ctrl+N[/bold #bb9af7]   toggle network panel
  [bold #bb9af7]Ctrl+L[/bold #bb9af7]   clear REPL
  [bold #bb9af7]Ctrl+Q[/bold #bb9af7]   quit
  [bold #bb9af7]F1[/bold #bb9af7]       this guide

[bold]  Tips[/bold]

  [dim]Tab completes commands and[/dim]
  [dim]app names as you type.[/dim]

  [dim]Unfocus the input (click[/dim]
  [dim]elsewhere) to use hotkeys.[/dim]\
"""

FOOTER_TEXT = "[dim]press [bold]Escape[/bold] or any key to close[/dim]"


class HelpScreen(ModalScreen):
    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "dismiss", show=False)]

    def compose(self) -> ComposeResult:
        yield Static(self._build_layout(), id="help-body", markup=True)

    def _build_layout(self) -> str:
        title = "[bold #7aa2f7] roku-tui[/bold #7aa2f7] [dim]· user guide[/dim]"
        divider = "[dim]" + "─" * 57 + "[/dim]"

        left_col = _pad_lines(DPAD, width=31)
        right_col = _pad_lines(ALIASES, width=27)
        top_row = _zip_columns(left_col, right_col)

        left_col2 = _pad_lines(COMMANDS, width=31)
        right_col2 = _pad_lines(SHORTCUTS, width=27)
        bottom_row = _zip_columns(left_col2, right_col2)

        sections = [
            "",
            f"  {title}",
            f"  {divider}",
            *[f"  {line}" for line in top_row],
            f"  {divider}",
            *[f"  {line}" for line in bottom_row],
            f"  {divider}",
            f"  {FOOTER_TEXT}",
            "",
        ]
        return "\n".join(sections)

    def on_key(self, event) -> None:
        if event.key != "escape":
            self.dismiss()


def _pad_lines(text: str, width: int) -> list[str]:
    """Split text into markup lines."""
    return text.split("\n")


def _zip_columns(left: list[str], right: list[str]) -> list[str]:
    """Merge two lists of markup lines side-by-side with a plain-text gutter."""
    max_len = max(len(left), len(right))
    left += [""] * (max_len - len(left))
    right += [""] * (max_len - len(right))
    # We can't measure Rich markup width accurately here, so use a fixed visual offset.
    # Left column content is kept at ~31 visible chars; pad with spaces on plain text.
    result = []
    for left_line, right_line in zip(left, right, strict=False):
        plain = re.sub(r"\[.*?\]", "", left_line)
        pad = max(0, 31 - len(plain))
        result.append(left_line + " " * pad + right_line)
    return result
