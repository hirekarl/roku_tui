from __future__ import annotations

from collections import deque
from typing import Any, ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Input, Label

from ..ecp.models import NetworkEvent

METHOD_STYLES: dict[str, str] = {
    "GET": "bold green",
    "POST": "bold blue",
}
STATUS_STYLES: dict[int, str] = {2: "green", 3: "yellow", 4: "red", 5: "red"}


class NetworkPanel(Widget):
    """A panel that displays real-time HTTP traffic with filtering and inspection."""

    class EventSelected(Message):
        """Sent when a network event is selected for inspection."""

        def __init__(self, event: NetworkEvent):
            super().__init__()
            self.event = event

    # Max number of events to keep in the rolling log
    MAX_EVENTS: ClassVar[int] = 100

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._events: deque[NetworkEvent] = deque(maxlen=self.MAX_EVENTS)
        self._filter: str = ""

    def compose(self) -> ComposeResult:
        yield Label(" HTTP Inspector", id="network-title")
        yield Input(placeholder="Filter (Press /)", id="network-filter")
        yield DataTable(
            id="network-log",
            cursor_type="row",
            zebra_stripes=False,
        )

    def on_mount(self) -> None:
        table = self.query_one("#network-log", DataTable)
        table.add_column("Event")

    def add_event(self, event: NetworkEvent) -> None:
        """Add a new network event to the panel."""
        self._events.append(event)
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Re-populate the data table based on current events and filter."""
        table = self.query_one("#network-log", DataTable)
        current_scroll = table.scroll_y

        # We need to track if we were at the bottom before clearing
        # DataTable doesn't have a perfect 'is_at_bottom', so we check if scroll_y
        # is near the maximum scrollable distance.
        is_at_bottom = (
            table.scroll_y >= table.max_scroll_y - 1 if table.max_scroll_y > 0 else True
        )

        table.clear()

        # Filter and add rows
        for i, event in enumerate(self._events):
            if self._matches_filter(event):
                # We use the original index in the deque as the row key
                # so we can retrieve the event later.
                table.add_row(self._format_event(event), key=str(i))

        # Auto-scroll to bottom if we were already there
        if is_at_bottom:
            table.scroll_to(y=table.max_scroll_y)
        else:
            table.scroll_y = current_scroll

    def _matches_filter(self, event: NetworkEvent) -> bool:
        if not self._filter:
            return True
        f = self._filter.lower()
        return (
            f in event.url.lower()
            or f in event.method.lower()
            or (event.status_code is not None and f in str(event.status_code))
            or (event.error is not None and f in event.error.lower())
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "network-filter":
            self._filter = event.value
            self._refresh_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection by emitting a custom EventSelected message."""
        if event.row_key.value is not None:
            idx = int(event.row_key.value)
            if 0 <= idx < len(self._events):
                self.post_message(self.EventSelected(self._events[idx]))

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
        max_width = 40  # Slightly narrower for DataTable padding
        right_len = len(right)
        left_width = max_width - right_len - 1

        method_part = f"{event.method:4} "
        path_part = path

        left = Text()
        left.append(method_part, style=method_style)

        available_for_path = left_width - len(method_part)
        if len(path_part) > available_for_path:
            path_part = "…" + path_part[-(available_for_path - 1) :]

        left.append(path_part, style="white")

        padding = max_width - (len(left) + len(right))
        return left + (" " * padding) + right
