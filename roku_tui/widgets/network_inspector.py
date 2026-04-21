from __future__ import annotations

import json
import xml.dom.minidom
from typing import Any, ClassVar

from rich.syntax import Syntax
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, RichLog, Static

from ..ecp.models import NetworkEvent

...
class NetworkInspector(ModalScreen[None]):
    """A modal screen for inspecting the details of a NetworkEvent."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]

    def __init__(self, event: NetworkEvent, **kwargs: Any):
        super().__init__(**kwargs)
        self.event = event

    def compose(self) -> ComposeResult:
        with Vertical(id="inspector-body"):
            yield Label(
                f" Inspect: {self.event.method} {self.event.url}", id="inspector-title"
            )

            with Vertical(id="inspector-header"):
                status_color = "green" if (self.event.status_code or 0) < 400 else "red"
                yield Label(Text.assemble(
                    ("Status: ", "dim"),
                    (f"{self.event.status_code or '???'}", f"bold {status_color}"),
                    ("  Time: ", "dim"),
                    (f"{self.event.response_time_ms or 0:.1f}ms", "bold")
                ))

            with ScrollableContainer(id="inspector-content"):
                yield Label("Request Headers", classes="inspector-section-title")
                yield Static(
                    self._format_headers(self.event.request_headers),
                    classes="inspector-text",
                )

                yield Label("Response Headers", classes="inspector-section-title")
                yield Static(
                    self._format_headers(self.event.response_headers),
                    classes="inspector-text",
                )

                with Vertical(id="inspector-payload-container"):
                    yield Label("Response Body", classes="inspector-section-title")
                    yield RichLog(id="inspector-payload", highlight=True, wrap=True)

            with Vertical(id="inspector-foot"):
                yield Button(
                    "Close (Esc)",
                    variant="error",
                    classes="modal-close",
                    id="inspector-close",
                )

    def on_mount(self) -> None:
        """Pretty-print the body once the log is mounted."""
        log = self.query_one("#inspector-payload", RichLog)
        if self.event.error:
            log.write(Text(f"Error: {self.event.error}", style="bold red"))
        elif not self.event.body:
            log.write(Text("No response body.", style="dim italic"))
        else:
            log.write(self._format_body(self.event.body))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "inspector-close":
            self.dismiss()

    def _format_headers(self, headers: dict[str, str]) -> Text:
        if not headers:
            return Text("None", style="dim italic")

        txt = Text()
        for k, v in headers.items():
            txt.append(f"{k}: ", style="bold cyan")
            txt.append(f"{v}\n", style="white")
        return txt

    def _format_body(self, body: str) -> Syntax | Text:
        """Attempt to pretty-print JSON or XML, otherwise return as-is."""
        # Try JSON
        try:
            parsed = json.loads(body)
            pretty = json.dumps(parsed, indent=2)
            return Syntax(pretty, "json", theme="monokai", background_color="default")
        except (json.JSONDecodeError, TypeError):
            pass

        # Try XML
        try:
            if body.strip().startswith("<"):
                dom = xml.dom.minidom.parseString(body)
                pretty = dom.toprettyxml(indent="  ")
                # Strip extra newlines toprettyxml adds
                pretty = "\n".join(
                    [line for line in pretty.split("\n") if line.strip()]
                )
                return Syntax(
                    pretty, "xml", theme="monokai", background_color="default"
                )
        except Exception:
            pass

        return Text(body)
