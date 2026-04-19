from __future__ import annotations

from rich.console import Group
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
        yield RichLog(id="network-log", auto_scroll=True, markup=False, highlight=False)

    def add_event(self, event: NetworkEvent) -> None:
        log = self.query_one("#network-log", RichLog)
        log.write(self._format_event(event))

    def _format_event(self, event: NetworkEvent) -> Group:
        method_style = METHOD_STYLES.get(event.method, "bold white")
        status_bucket = (event.status_code // 100) if event.status_code else 0
        status_style = STATUS_STYLES.get(status_bucket, "white")

        path = event.url
        for prefix in ("http://mock-roku:8060", "http://"):
            if prefix in path:
                path = path.split(":8060", 1)[-1] or path
                break

        header = Text()
        header.append(f" {event.method} ", style=method_style + " on #1f2335")
        header.append(f" {path}", style="white")

        status_line = Text()
        if event.status_code is not None:
            status_line.append(f"  {event.status_code} ", style=f"bold {status_style}")
            if event.response_time_ms is not None:
                status_line.append(f"· {event.response_time_ms:.0f}ms", style="dim")
        elif event.error:
            status_line.append(f"  ERROR: {event.error}", style="bold red")

        parts = [header, status_line]

        if event.body and event.status_code is not None:
            preview = event.body[:120].replace("\n", " ").strip()
            if len(event.body) > 120:
                preview += "…"
            body_line = Text()
            body_line.append(f"  {preview}", style="dim")
            parts.append(body_line)

        parts.append(Text("─" * 36, style="dim #414868"))
        return Group(*parts)
