from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.theme import Theme
from textual.widgets import Footer, Header, Input

from .commands.db_commands import register_db_commands
from .commands.handlers import register_all
from .commands.registry import CommandRegistry
from .commands.suggester import RokuSuggester
from .db import Database
from .ecp.client import EcpClient
from .ecp.discovery import discover_rokus
from .ecp.mock import MockEcpClient
from .ecp.models import NetworkEvent
from .widgets.help_screen import HelpScreen
from .widgets.network_panel import NetworkPanel
from .widgets.repl_panel import ReplPanel
from .widgets.status_bar import StatusBar

TOKYO_NIGHT = Theme(
    name="roku-night",
    primary="#7aa2f7",
    secondary="#bb9af7",
    foreground="#c0caf5",
    background="#1a1b26",
    dark=True,
    variables={
        "surface": "#24283b",
        "panel": "#1f2335",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "error": "#f7768e",
        "accent": "#73daca",
        "comment": "#565f89",
        "bg-dark": "#16161e",
        "bg-highlight": "#292e42",
    },
)


def _get_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "roku_tui.db"


class RokuTuiApp(App):
    CSS_PATH = "../roku_tui.tcss"
    TITLE = "roku-tui"
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+n", "toggle_network", "Network"),
        Binding("ctrl+l", "clear_repl", "Clear"),
        Binding("f1", "show_guide", "Guide", key_display="F1"),
    ]

    _HOTKEYS: ClassVar[dict[str, str]] = {
        "up": "Up",
        "down": "Down",
        "left": "Left",
        "right": "Right",
        "enter": "Select",
        "space": "Play",
        "backspace": "Back",
    }

    class NetworkEventReceived(Message):
        def __init__(self, event: NetworkEvent):
            super().__init__()
            self.event = event

    def __init__(self, mock: bool = False, initial_ip: str | None = None):
        super().__init__()
        self.mock = mock
        self.initial_ip = initial_ip
        self.client: EcpClient | MockEcpClient | None = None
        self.registry = CommandRegistry()
        self.app_cache = []
        self._current_ip: str | None = None
        self.db = Database(_get_db_path())
        register_all(self.registry)
        self.suggester = RokuSuggester(self.registry)

    def compose(self) -> ComposeResult:
        yield Header()
        yield StatusBar(id="status-bar")
        with Horizontal(id="main-area"):
            yield ReplPanel(suggester=self.suggester, id="repl-panel")
            yield NetworkPanel(id="network-panel")
        yield Footer()

    async def on_mount(self) -> None:
        self.register_theme(TOKYO_NIGHT)
        self.theme = "roku-night"
        await asyncio.to_thread(self.db.initialize)
        register_db_commands(self.registry)
        if self.mock:
            self._init_mock()
        elif self.initial_ip:
            self._connect(self.initial_ip)
        else:
            self._start_discovery()

    @work(thread=True)
    def _start_discovery(self) -> None:
        repl = self.query_one("#repl-panel", ReplPanel)
        self.call_from_thread(
            repl.system_message,
            "[dim]Searching for Roku devices on your network...[/dim]",
        )
        urls = discover_rokus(timeout=3.0)
        if urls:
            url = urls[0]
            self.call_from_thread(
                repl.system_message,
                f"[dim]Found Roku at[/dim] [bold]{url}[/bold]",
            )
            self.call_from_thread(self._connect, url)
        else:
            self.call_from_thread(
                repl.system_message,
                "[yellow]No Roku found.[/yellow] "
                "Use [bold]connect <ip>[/bold] to connect manually.",
            )

    def _init_mock(self) -> None:
        self._current_ip = "mock-roku"
        self.client = MockEcpClient(on_network_event=self._on_network_event)
        self.query_one("#status-bar", StatusBar).set_connected(
            "My Roku TV (Mock)", mock=True
        )
        self.query_one("#repl-panel", ReplPanel).system_message(
            "[dim]Running in [bold]mock mode[/bold] — "
            "HTTP requests are simulated.[/dim]"
        )
        self._prefetch_info()

    def _connect(self, url: str) -> None:
        if "://" not in url:
            url = f"http://{url}:8060"
        base_url = url.rstrip("/")
        if not base_url.endswith(":8060"):
            base_url = base_url.split(":8060")[0] + ":8060"

        ip = base_url.split("://")[-1].split(":")[0]
        self._current_ip = ip

        if self.client and hasattr(self.client, "close"):
            self.run_worker(self.client.close())

        self.client = EcpClient(
            base_url=base_url, on_network_event=self._on_network_event
        )
        self._prefetch_info()

    @work
    async def _prefetch_info(self) -> None:
        if not self.client or not self._current_ip:
            return
        try:
            info = await self.client.query_device_info()
            if info:
                self.query_one("#status-bar", StatusBar).set_connected(
                    info.friendly_name
                )
                device_id = await asyncio.to_thread(
                    self.db.upsert_device, info, self._current_ip
                )

                # Warm the suggester immediately from cached DB apps (no network wait)
                cached_apps = await asyncio.to_thread(
                    self.db.get_device_apps, device_id
                )
                if cached_apps:
                    freq = await asyncio.to_thread(self.db.app_launch_frequencies)
                    self.suggester.update_launch_frequencies(freq)
                    self.suggester.update_app_names(
                        [a["app_name"] for a in cached_apps]
                    )

            # Fetch live app list and write through to DB
            apps = await self.client.query_apps()
            self.app_cache = apps
            if info:
                await asyncio.to_thread(self.db.sync_device_apps, apps, device_id)

            freq = await asyncio.to_thread(self.db.app_launch_frequencies)
            self.suggester.update_launch_frequencies(freq)
            self.suggester.update_app_names([a.name for a in apps])
        except Exception:
            pass

    def _on_network_event(self, event: NetworkEvent) -> None:
        self.post_message(self.NetworkEventReceived(event))

    def on_roku_tui_app_network_event_received(self, msg: NetworkEventReceived) -> None:
        self.query_one("#network-panel", NetworkPanel).add_event(msg.event)
        device_id = self._current_device_id()
        with contextlib.suppress(Exception):
            self.db.log_network_request(msg.event, device_id)

    async def on_repl_panel_command_submitted(
        self, msg: ReplPanel.CommandSubmitted
    ) -> None:
        await self._dispatch(msg.line)

    async def _dispatch(self, line: str) -> None:
        repl = self.query_one("#repl-panel", ReplPanel)
        success = False

        no_client_allowed = {
            "connect", "help", "?", "h", "clear", "cls",
            "macro", "history", "stats", "devices",
        }
        if self.client is None and line.split()[0] not in no_client_allowed:
            repl.error(
                "[yellow]Not connected.[/yellow] "
                "Use [bold]connect <ip>[/bold] or run with [bold]--mock[/bold]."
            )
            self.db.log_command(line, success=False, device_id=None)
            return

        result = self.registry.parse(line)
        if result is None:
            cmd_name = line.split()[0]
            repl.error(
                f"[red]Unknown command:[/red] [bold]{cmd_name}[/bold] — "
                f"try [bold]help[/bold]"
            )
            self.db.log_command(
                line, success=False, device_id=self._current_device_id()
            )
            return

        cmd, args = result
        try:
            output = await cmd.handler(self.client, args, context=self)
            if output:
                repl.output(output)
            success = True
        except Exception as e:
            repl.error(f"[red]Error:[/red] {e}")
        finally:
            self.db.log_command(
                line, success=success, device_id=self._current_device_id()
            )

    def _current_device_id(self) -> int | None:
        if not self._current_ip:
            return None
        try:
            return self.db.get_device_id(self._current_ip)
        except Exception:
            return None

    async def on_key(self, event) -> None:
        if isinstance(self.focused, Input):
            return
        ecp_key = self._HOTKEYS.get(event.key)
        if ecp_key and self.client:
            event.prevent_default()
            await self.client.keypress(ecp_key)

    def action_show_guide(self) -> None:
        self.push_screen(HelpScreen())

    def action_toggle_network(self) -> None:
        panel = self.query_one("#network-panel", NetworkPanel)
        repl = self.query_one("#repl-panel", ReplPanel)
        if "hidden" in panel.classes:
            panel.remove_class("hidden")
            repl.remove_class("full-width")
        else:
            panel.add_class("hidden")
            repl.add_class("full-width")

    def action_clear_repl(self) -> None:
        self.query_one("#repl-panel", ReplPanel).clear_history()

    async def connect(self, ip: str) -> None:
        self._connect(ip)

    async def on_unmount(self) -> None:
        if self.client and hasattr(self.client, "close"):
            await self.client.close()
        self.db.close()
