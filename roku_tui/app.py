from __future__ import annotations

import asyncio
import contextlib
import difflib
import sys
import urllib.parse
from pathlib import Path

import platformdirs
from rich.panel import Panel
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.events import Key
from textual.widgets import Footer, Header, Input, TabbedContent, TabPane

from .actions import RokuActions
from .commands.db_commands import register_db_commands
from .commands.handlers import register_all
from .commands.registry import CommandRegistry
from .commands.suggester import RokuSuggester
from .commands.tui_commands import register_tui_commands
from .constants import BINDINGS, HOTKEYS, RECORDING_SKIP, REMOTE_HOTKEYS
from .db import Database
from .ecp.client import EcpClient
from .ecp.discovery import discover_rokus, probe_roku
from .ecp.mock import MockEcpClient
from .ecp.models import AppInfo
from .themes import THEMES, TOKYO_NIGHT
from .widgets.console_panel import ConsolePanel
from .widgets.network_panel import NetworkPanel
from .widgets.remote_panel import CMD_TO_ECP, RemotePanel
from .widgets.status_bar import StatusBar


def _get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    except Exception:
        base_path = Path(__file__).resolve().parent.parent

    return base_path / relative_path


def _get_db_path() -> Path:
    """Return the absolute path to the SQLite database file in user data directory."""
    data_dir = Path(platformdirs.user_data_dir("roku-tui"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "roku_tui.db"


class RokuTuiApp(RokuActions, App[None]):
    """The main Textual application class for roku-tui."""

    CSS_PATH = _get_resource_path("roku_tui.tcss")
    TITLE = "roku-tui"
    BINDINGS = BINDINGS

    def __init__(self, mock: bool = False, initial_ip: str | None = None):
        """Initialize the application."""
        super().__init__()
        self.mock = mock
        self.initial_ip = initial_ip
        self._kb_mode: bool = False
        self._recording: list[str] | None = None
        self.client: EcpClient | MockEcpClient | None = None
        self.registry: CommandRegistry = CommandRegistry()
        self.app_cache: list[AppInfo] = []
        self._current_ip: str | None = None
        self.db = Database(_get_db_path())
        register_all(self.registry)
        self.suggester = RokuSuggester(self.registry)
        self._register_tui_commands()

    def get_css_variables(self) -> dict[str, str]:
        """Inject Tokyo Night variables into the global CSS scope."""
        variables = super().get_css_variables()
        for key, value in TOKYO_NIGHT.variables.items():
            variables.setdefault(key, value)
        return variables

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        yield StatusBar(id="status-bar")
        with Horizontal(id="main-area"):
            with TabbedContent(id="main-tabs", initial="tab-console"):
                with TabPane("Console", id="tab-console"):
                    yield ConsolePanel(
                        suggester=self.suggester,
                        registry=self.registry,
                        id="console-panel",
                    )
                with TabPane("Remote", id="tab-remote"):
                    yield RemotePanel(id="remote-panel")
            yield NetworkPanel(id="network-panel")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize themes, database, and start device discovery."""
        for t in THEMES.values():
            self.register_theme(t)
        self.theme = "roku-night"
        await asyncio.to_thread(self.db.initialize)
        register_db_commands(self.registry)
        if self.mock:
            self._init_mock()
        elif self.initial_ip:
            self._connect(self.initial_ip)
        else:
            self.action_show_discovery()

    @work(thread=True)
    def _start_discovery(self) -> None:
        """Try last-known devices first, then fall back to SSDP discovery."""
        console = self.query_one("#console-panel", ConsolePanel)
        known_ips = self.db.known_device_ips()
        if known_ips:
            self.call_from_thread(
                console.system_message, "[dim]Trying last-known devices...[/dim]"
            )
            for ip in known_ips:
                if probe_roku(ip):
                    self.call_from_thread(self._connect, f"http://{ip}:8060")
                    return

        self.call_from_thread(console.system_message, "[dim]Searching network...[/dim]")
        urls = discover_rokus(timeout=3.0)
        if urls:
            self.call_from_thread(self._connect, urls[0])
        else:
            self.call_from_thread(
                console.system_message, "[yellow]No Roku found.[/yellow]"
            )

    def _init_mock(self) -> None:
        """Initialize mock mode with a simulated ECP client."""
        self._current_ip = "mock-roku"
        self.client = MockEcpClient(on_network_event=self._on_network_event)
        self.query_one("#status-bar", StatusBar).set_connected(
            "My Roku TV (Mock)", mock=True
        )
        self.query_one("#console-panel", ConsolePanel).system_message(
            "[dim]Running in [bold]mock mode[/bold][/dim]"
        )
        self.query_one("#remote-panel", RemotePanel).set_connected(True)
        self._prefetch_info()

    def _connect(self, url: str) -> None:
        """Connect to a Roku device at the specified URL."""
        if "://" not in url:
            url = f"http://{url}:8060"
        base_url = url.rstrip("/")
        if not base_url.endswith(":8060"):
            base_url = base_url.split(":8060")[0] + ":8060"

        self._current_ip = base_url.split("://")[-1].split(":")[0]
        if self.client and hasattr(self.client, "close"):
            self.run_worker(self.client.close())

        self.client = EcpClient(
            base_url=base_url, on_network_event=self._on_network_event
        )
        self.query_one("#remote-panel", RemotePanel).set_connected(True)
        self._prefetch_info()

    @work
    async def _prefetch_info(self) -> None:
        """Prefetch device info and app list to warm the suggester cache."""
        client = self.client
        if not client or not self._current_ip:
            return
        device_id = None
        try:
            info = await client.query_device_info()
            if info:
                self.query_one("#status-bar", StatusBar).set_connected(
                    info.friendly_name
                )
                self.query_one("#console-panel", ConsolePanel).system_message(
                    f"[dim]Connected to[/dim] [bold]{info.friendly_name}[/bold]"
                )
                device_id = await asyncio.to_thread(
                    self.db.upsert_device, info, self._current_ip
                )
                cached = await asyncio.to_thread(self.db.get_device_apps, device_id)
                if cached:
                    freq = await asyncio.to_thread(self.db.app_launch_frequencies)
                    self.suggester.update_launch_frequencies(freq)
                    self.suggester.update_app_names([a["app_name"] for a in cached])

            apps = await client.query_apps()
            self.app_cache = apps
            if info and device_id:
                await asyncio.to_thread(self.db.sync_device_apps, apps, device_id)
            self.suggester.update_app_names([a.name for a in apps])
        except Exception:
            with contextlib.suppress(Exception):
                self.query_one("#console-panel", ConsolePanel).system_message(
                    "[red]Connection failed.[/red]"
                )

    def on_roku_tui_app_network_event_received(
        self, msg: RokuActions.NetworkEventReceived
    ) -> None:
        """Handle network event messages by updating the UI and database."""
        with contextlib.suppress(Exception):
            self.query_one("#network-panel", NetworkPanel).add_event(msg.event)

        device_id = self._current_device_id()
        with contextlib.suppress(Exception):
            self.db.log_network_request(msg.event, device_id)

    async def on_console_panel_command_submitted(
        self, msg: ConsolePanel.CommandSubmitted
    ) -> None:
        """Handle command submission from the console panel."""
        for part in [p.strip() for p in msg.line.split(";") if p.strip()]:
            await self.dispatch(part)

    async def on_remote_panel_button_activated(
        self, msg: RemotePanel.ButtonActivated
    ) -> None:
        """Handle virtual button presses from the Remote panel."""
        if self.client:
            await self.client.keypress(msg.ecp_key)
            self.db.log_command(
                f"remote:{msg.ecp_key}",
                success=True,
                device_id=self._current_device_id(),
            )

    async def _dispatch(self, line: str) -> bool:
        """Parse and route a command string to its appropriate handler."""
        console = self.query_one("#console-panel", ConsolePanel)
        if self.client is None and line.split()[0] not in RECORDING_SKIP:
            msg = Panel(
                "[bold yellow]Not connected.[/bold yellow]\n\n"
                "• Press [cyan]C[/cyan] to search",
                title="[red]Error[/red]",
                border_style="yellow",
                expand=False,
                padding=(1, 2),
            )
            console.output(msg)
            return False

        result = self.registry.parse(line)
        if result is None:
            cmd_name = line.split()[0]
            suggestions = difflib.get_close_matches(
                cmd_name, list(self.registry.all_names()), n=1, cutoff=0.6
            )
            hint = (
                f" — did you mean [bold]{suggestions[0]}[/bold]?"
                if suggestions
                else " — try [bold]help[/bold]"
            )
            console.error(f"[red]Unknown command:[/red] [bold]{cmd_name}[/bold]{hint}")
            return False

        cmd, args = result
        try:
            output = await cmd.handler(self.client, args, context=self)
            if output:
                console.output(output)
            if CMD_TO_ECP.get(cmd.name):
                ecp_key = CMD_TO_ECP[cmd.name]
                if cmd.name == "volume" and args:
                    if args[0] == "up":
                        ecp_key = "VolumeUp"
                    elif args[0] == "down":
                        ecp_key = "VolumeDown"
                self.query_one("#remote-panel", RemotePanel).flash_by_key(ecp_key)
            return True
        except Exception as e:
            console.error(f"[red]Error:[/red] {e}")
            return False
        finally:
            dev_id = self._current_device_id()
            self.db.log_command(line, success=True, device_id=dev_id)
            if self._recording is not None and line.split()[0] not in RECORDING_SKIP:
                self._recording.append(line)

    def _current_device_id(self) -> int | None:
        """Return the database ID of the currently connected device."""
        try:
            return self.db.get_device_id(self._current_ip) if self._current_ip else None
        except Exception:
            return None

    def toggle_keyboard_mode(self) -> None:
        """Toggle keyboard passthrough mode on or off."""
        if self._kb_mode:
            self._kb_mode = False
            self.query_one("#console-panel", ConsolePanel).exit_keyboard_mode()
        else:
            self._kb_mode = True
            self.set_focus(None)
            self.query_one("#console-panel", ConsolePanel).enter_keyboard_mode()

    async def on_key(self, event: Key) -> None:
        """Route keys to the TV in keyboard mode; otherwise handle hotkeys."""
        remote = self.query_one("#remote-panel", RemotePanel)
        if self._kb_mode:
            if event.key == "escape":
                self.toggle_keyboard_mode()
            elif event.key in ("enter", "return") and self.client:
                remote.flash_by_key("Select")
                await self.client.keypress("Select")
            elif event.key == "backspace" and self.client:
                remote.flash_by_key("Back")
                await self.client.keypress("Backspace")
            elif event.character and event.character.isprintable() and self.client:
                quoted = urllib.parse.quote(event.character, safe="")
                await self.client.keypress(f"Lit_{quoted}")
            return

        if isinstance(self.focused, Input) or len(self.screen_stack) > 1:
            return

        ecp_key = HOTKEYS.get(event.key)
        if ecp_key and self.client:
            event.prevent_default()
            remote.flash_by_key(ecp_key)
            await self.client.keypress(ecp_key)
        elif (
            self.client
            and self.query_one("#main-tabs", TabbedContent).active == "tab-remote"
        ):
            remote_ecp = REMOTE_HOTKEYS.get(event.character or "")
            if remote_ecp:
                event.prevent_default()
                remote.flash_by_key(remote_ecp)
                await self.client.keypress(remote_ecp)

    def _register_tui_commands(self) -> None:
        register_tui_commands(self.registry, self)

    def start_recording(self) -> None:
        self._recording = []

    def stop_recording(self) -> list[str] | None:
        lines, self._recording = self._recording, None
        return lines

    def emit_message(self, text: str) -> None:
        self.query_one("#console-panel", ConsolePanel).system_message(text)

    async def dispatch(self, line: str) -> bool:
        return await self._dispatch(line)

    async def connect(self, ip: str) -> None:
        self._connect(ip)

    async def on_unmount(self) -> None:
        if self.client:
            await self.client.close()
        self.db.close()
