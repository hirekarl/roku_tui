from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, RichLog

from ..ecp.models import NetworkEvent

METHOD_STYLES: dict[str, str] = {
    "GET": "bold green",
    "POST": "bold blue",
}
STATUS_STYLES: dict[int, str] = {2: "green", 3: "yellow", 4: "red", 5: "red"}


class NetworkPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Label(" HTTP Inspector", id="network-title")
        yield RichLog(id="network-log", auto_scroll=True, markup=True, highlight=False, wrap=True)

    def add_event(self, event: NetworkEvent) -> None:
        log = self.query_one("#network-log", RichLog)
        log.write(self._format_event(event))

    def _format_event(self, event: NetworkEvent) -> Text:
        method_style = METHOD_STYLES.get(event.method, "bold white")
        status_bucket = (event.status_code // 100) if event.status_code else 0
        status_style = STATUS_STYLES.get(status_bucket, "white")

        path = event.url
        if "://" in path:
            path = path.split(":8060", 1)[-1] or path

        # Right side: Status + Time
        right = Text()
        if event.status_code is not None:
            right.append(f"{event.status_code}", style=f"bold {status_style}")
            if event.response_time_ms is not None:
                right.append(f" {event.response_time_ms:.0f}ms", style="dim")
        elif event.error:
            right.append("ERR", style="bold red")

        # Left side: Method + Path
        # Fixed width is 44. Scrollbar is 1. Effective width is 43.
        # We'll allow 42 to be safe.
        max_width = 42
        right_len = len(right)
        left_width = max_width - right_len - 1 # -1 for spacer
        
        method_part = f"{event.method:4} "
        path_part = path
        
        left = Text()
        left.append(method_part, style=method_style)
        
        available_for_path = left_width - len(method_part)
        if len(path_part) > available_for_path:
            path_part = "…" + path_part[-(available_for_path-1):]
        
        left.append(path_part, style="white")
        
        # Assemble with dynamic padding
        padding = max_width - (len(left) + len(right))
        return left + (" " * padding) + right
