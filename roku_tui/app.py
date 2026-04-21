from __future__ import annotations

import asyncio
import contextlib
import difflib
import urllib.parse
from pathlib import Path
from typing import Any, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Key
from textual.message import Message
from textual.theme import Theme
from textual.widgets import Button, Footer, Header, Input, TabbedContent, TabPane

from .commands.db_commands import register_db_commands
from .commands.handlers import register_all
from .commands.registry import Command, CommandRegistry
from .commands.suggester import RokuSuggester
from .db import Database
from .ecp.client import EcpClient
from .ecp.discovery import discover_rokus, probe_roku
from .ecp.mock import MockEcpClient
from .ecp.models import AppInfo, NetworkEvent
from .widgets.console_panel import ConsolePanel
from .widgets.guide_screen import GuideScreen
from .widgets.help_screen import HelpScreen
from .widgets.network_inspector import NetworkInspector
from .widgets.network_panel import NetworkPanel
from .widgets.remote_panel import (
    CMD_TO_ECP,
    HOTKEY_TO_BUTTON,
    REMOTE_HOTKEY_TO_BTN,
    RemotePanel,
)
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
        "muted-border": "#414868",
    },
)

_THEMES: dict[str, Theme] = {
    "roku-night": TOKYO_NIGHT,
    "catppuccin": Theme(
        name="catppuccin",
        primary="#89b4fa",
        secondary="#cba6f7",
        foreground="#cdd6f4",
        background="#1e1e2e",
        dark=True,
        variables={
            "surface": "#313244",
            "panel": "#181825",
            "success": "#a6e3a1",
            "warning": "#fab387",
            "error": "#f38ba8",
            "accent": "#94e2d5",
            "comment": "#6c7086",
            "bg-dark": "#11111b",
            "bg-highlight": "#45475a",
            "muted-border": "#585b70",
        },
    ),
    "nord": Theme(
        name="nord",
        primary="#88c0d0",
        secondary="#b48ead",
        foreground="#d8dee9",
        background="#2e3440",
        dark=True,
        variables={
            "surface": "#434c5e",
            "panel": "#3b4252",
            "success": "#a3be8c",
            "warning": "#ebcb8b",
            "error": "#bf616a",
            "accent": "#8fbcbb",
            "comment": "#4c566a",
            "bg-dark": "#242933",
            "bg-highlight": "#3b4252",
            "muted-border": "#434c5e",
        },
    ),
    "gruvbox": Theme(
        name="gruvbox",
        primary="#83a598",
        secondary="#d3869b",
        foreground="#ebdbb2",
        background="#282828",
        dark=True,
        variables={
            "surface": "#3c3836",
            "panel": "#1d2021",
            "success": "#b8bb26",
            "warning": "#fabd2f",
            "error": "#fb4934",
            "accent": "#8ec07c",
            "comment": "#928374",
            "bg-dark": "#1d2021",
            "bg-highlight": "#504945",
            "muted-border": "#665c54",
        },
    ),
}


def _get_db_path() -> Path:
    """Return the absolute path to the SQLite database file."""
    return Path(__file__).resolve().parent.parent / "roku_tui.db"


class RokuTuiApp(App[None]):
    """The main Textual application class for roku-tui."""

    CSS_PATH = "../roku_tui.tcss"
    TITLE = "roku-tui"
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+t", "toggle_tab", "Console/Remote"),
        Binding("ctrl+n", "toggle_network", "Network"),
        Binding("ctrl+l", "clear_console", "Clear"),
        Binding("f1", "show_guide", "Quick ref", key_display="F1"),
        Binding("f2", "show_manual", "Guide", key_display="F2"),
        Binding("/", "focus_network_filter", "Filter", show=False),
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

    _RECORDING_SKIP: ClassVar[frozenset[str]] = frozenset(
        {
            "macro",
            "history",
            "stats",
            "devices",
            "help",
            "clear",
            "cls",
            "guide",
            "theme",
        }
    )

    _REMOTE_HOTKEYS: ClassVar[dict[str, str]] = {
        "h": "Home",
        "m": "VolumeMute",
        ",": "Rev",
        ".": "Fwd",
        "=": "VolumeUp",
        "-": "VolumeDown",
    }

    class NetworkEventReceived(Message):
        """Internal message sent when an ECP network event occurs."""

        def __init__(self, event: NetworkEvent):
            super().__init__()
            self.event = event

    def __init__(self, mock: bool = False, initial_ip: str | None = None):
        """Initialize the application.

        Args:
            mock: If True, run in mock mode with simulated HTTP calls.
            initial_ip: Optional IP address to connect to on startup.
        """
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
        for t in _THEMES.values():
            self.register_theme(t)
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
        """Try last-known devices first, then fall back to SSDP discovery."""
        console = self.query_one("#console-panel", ConsolePanel)

        known_ips = self.db.known_device_ips()
        if known_ips:
            self.call_from_thread(
                console.system_message,
                "[dim]Trying last-known Roku devices...[/dim]",
            )
            for ip in known_ips:
                if probe_roku(ip):
                    self.call_from_thread(self._connect, f"http://{ip}:8060")
                    return

        self.call_from_thread(
            console.system_message,
            "[dim]Searching for Roku devices on your network...[/dim]",
        )
        urls = discover_rokus(timeout=3.0)
        if urls:
            url = urls[0]
            self.call_from_thread(
                console.system_message,
                f"[dim]Found Roku at[/dim] [bold]{url}[/bold]",
            )
            self.call_from_thread(self._connect, url)
        else:
            self.call_from_thread(
                console.system_message,
                "[yellow]No Roku found.[/yellow] "
                "Use [bold]connect <ip>[/bold] to connect manually.",
            )

    def _init_mock(self) -> None:
        """Initialize mock mode with a simulated ECP client."""
        self._current_ip = "mock-roku"
        self.client = MockEcpClient(on_network_event=self._on_network_event)
        self.query_one("#status-bar", StatusBar).set_connected(
            "My Roku TV (Mock)", mock=True
        )
        self.query_one("#console-panel", ConsolePanel).system_message(
            "[dim]Running in [bold]mock mode[/bold] — "
            "HTTP requests are simulated.[/dim]"
        )
        self._prefetch_info()

    def _connect(self, url: str) -> None:
        """Connect to a Roku device at the specified URL.

        Args:
            url: The IP address or base URL of the Roku device.
        """
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
        """Prefetch device info and app list to warm the suggester cache."""
        client = self.client
        if not client or not self._current_ip:
            return
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

                db = self.db
                cached = await asyncio.to_thread(db.get_device_apps, device_id)
                if cached:
                    freq = await asyncio.to_thread(db.app_launch_frequencies)
                    self.suggester.update_launch_frequencies(freq)
                    names = [a["app_name"] for a in cached]
                    self.suggester.update_app_names(names)

            apps = await client.query_apps()
            self.app_cache = apps
            if info and device_id:
                await asyncio.to_thread(self.db.sync_device_apps, apps, device_id)

            freq = await asyncio.to_thread(self.db.app_launch_frequencies)
            self.suggester.update_launch_frequencies(freq)
            self.suggester.update_app_names([a.name for a in apps])
        except Exception:
            with contextlib.suppress(Exception):
                self.query_one("#console-panel", ConsolePanel).system_message(
                    "[red]Connection failed.[/red] Check the IP and try again."
                )

    def _on_network_event(self, event: NetworkEvent) -> None:
        """Internal callback passed to the ECP client to route network traffic."""
        self.post_message(self.NetworkEventReceived(event))

    def on_roku_tui_app_network_event_received(self, msg: NetworkEventReceived) -> None:
        """Handle network event messages by updating the UI and database."""
        with contextlib.suppress(Exception):
            self.query_one("#network-panel", NetworkPanel).add_event(msg.event)

        device_id = self._current_device_id()
        with contextlib.suppress(Exception):
            self.db.log_network_request(msg.event, device_id)

    def on_network_panel_event_selected(self, msg: NetworkPanel.EventSelected) -> None:
        """Show the inspection modal when a network event is selected."""
        self.push_screen(NetworkInspector(msg.event))

    def action_focus_network_filter(self) -> None:
        """Focus the network filter input if the panel is visible."""
        panel = self.query_one("#network-panel", NetworkPanel)
        if not panel.has_class("hidden"):
            panel.query_one("#network-filter", Input).focus()

    async def on_console_panel_command_submitted(
        self, msg: ConsolePanel.CommandSubmitted
    ) -> None:
        """Handle command submission from the console panel."""
        parts = [p.strip() for p in msg.line.split(";") if p.strip()]
        for part in parts:
            await self._dispatch(part)

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
        success = False

        no_client = {
            "connect",
            "help",
            "?",
            "h",
            "clear",
            "cls",
            "macro",
            "history",
            "stats",
            "devices",
            "sleep",
            "link",
            "yt",
            "kb",
            "keyboard",
            "guide",
        }
        if self.client is None and line.split()[0] not in no_client:
            console.error(
                "[yellow]Not connected.[/yellow] "
                "Use [bold]connect <ip>[/bold] or run with [bold]--mock[/bold]."
            )
            self.db.log_command(line, success=False, device_id=None)
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
            dev_id = self._current_device_id()
            self.db.log_command(line, success=False, device_id=dev_id)
            return False

        cmd, args = result
        try:
            output = await cmd.handler(self.client, args, context=self)
            if output:
                console.output(output)
            success = True

            # Visual feedback on the remote
            if success:
                ecp_key = CMD_TO_ECP.get(cmd.name)
                if ecp_key:
                    # Special case for volume directions
                    if cmd.name == "volume" and args:
                        if args[0] == "up":
                            ecp_key = "VolumeUp"
                        elif args[0] == "down":
                            ecp_key = "VolumeDown"
                        elif args[0] == "mute":
                            ecp_key = "VolumeMute"

                    self.query_one("#remote-panel", RemotePanel).flash_by_key(ecp_key)
        except Exception as e:
            console.error(f"[red]Error:[/red] {e}")
        finally:
            dev_id = self._current_device_id()
            self.db.log_command(line, success=success, device_id=dev_id)
            if success and self._recording is not None:
                first = line.split()[0] if line.split() else ""
                if first not in self._RECORDING_SKIP:
                    self._recording.append(line)
        return success

    def _current_device_id(self) -> int | None:
        """Return the database ID of the currently connected device."""
        if not self._current_ip:
            return None
        try:
            return self.db.get_device_id(self._current_ip)
        except Exception:
            return None

    def toggle_keyboard_mode(self) -> None:
        """Toggle keyboard passthrough mode on or off."""
        if self._kb_mode:
            self._exit_keyboard_mode()
        else:
            self._enter_keyboard_mode()

    def _enter_keyboard_mode(self) -> None:
        self._kb_mode = True
        self.set_focus(None)
        self.query_one("#console-panel", ConsolePanel).enter_keyboard_mode()

    def _exit_keyboard_mode(self) -> None:
        self._kb_mode = False
        self.query_one("#console-panel", ConsolePanel).exit_keyboard_mode()

    async def on_key(self, event: Key) -> None:
        """Route keys to the TV in keyboard mode; otherwise handle hotkeys."""
        remote = self.query_one("#remote-panel", RemotePanel)
        if self._kb_mode:
            char = event.character
            key = event.key
            if key == "escape":
                event.stop()
                self._exit_keyboard_mode()
            elif key in ("enter", "return"):
                event.stop()
                if self.client:
                    remote.flash_by_key("Select")
                    await self.client.keypress("Select")
            elif key == "backspace":
                event.stop()
                if self.client:
                    remote.flash_by_key("Back")
                    await self.client.keypress("Backspace")
            elif char and char.isprintable():
                event.stop()
                if self.client:
                    await self.client.keypress(
                        f"Lit_{urllib.parse.quote(char, safe='')}"
                    )
            return

        if isinstance(self.focused, Input):
            return
        if len(self.screen_stack) > 1:
            return

        ecp_key = self._HOTKEYS.get(event.key)
        if ecp_key and self.client:
            event.prevent_default()
            remote.flash_by_key(ecp_key)
            await self.client.keypress(ecp_key)
            return

        if not self.client:
            return
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active != "tab-remote":
            return
        char = event.character
        if char:
            remote_ecp = self._REMOTE_HOTKEYS.get(char)
            if remote_ecp:
                event.prevent_default()
                remote.flash_by_key(remote_ecp)
                await self.client.keypress(remote_ecp)

    def action_show_guide(self) -> None:
        """Toggle the F1 quick reference card."""
        if isinstance(self.screen, HelpScreen):
            self.pop_screen()
        else:
            self.push_screen(HelpScreen())

    def action_show_manual(self) -> None:
        """Toggle the F2 full user guide."""
        if isinstance(self.screen, GuideScreen):
            self.pop_screen()
        else:
            self.push_screen(GuideScreen())

    def action_toggle_tab(self) -> None:
        """Toggle between Console and Remote tabs (Ctrl+T)."""
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-console":
            tabs.active = "tab-remote"
            self.query_one("#btn-up", Button).focus()
        else:
            tabs.active = "tab-console"
            self.query_one("#command-input", Input).focus()

    def action_toggle_network(self) -> None:
        """Show or hide the network inspector panel (Ctrl+N)."""
        panel = self.query_one("#network-panel", NetworkPanel)
        tabs = self.query_one("#main-tabs", TabbedContent)
        if "hidden" in panel.classes:
            panel.remove_class("hidden")
            tabs.remove_class("full-width")
        else:
            panel.add_class("hidden")
            tabs.add_class("full-width")

    def action_clear_console(self) -> None:
        """Clear the console history scrollback."""
        self.query_one("#console-panel", ConsolePanel).clear_history()

    def _register_tui_commands(self) -> None:
        """Register built-in TUI-specific commands like 'clear' and 'theme'."""

        async def _handle_clear(client: Any, args: list[str], context: Any) -> str:
            self.query_one("#console-panel", ConsolePanel).clear_history()
            return ""

        self.registry.register(
            Command(
                name="clear",
                aliases=["cls"],
                args=[],
                handler=_handle_clear,
                help_text="Clear the console history",
            )
        )

        async def _handle_guide(client: Any, args: list[str], context: Any) -> str:
            self.push_screen(GuideScreen())
            return ""

        self.registry.register(
            Command(
                name="guide",
                aliases=[],
                args=[],
                handler=_handle_guide,
                help_text="Open the full user manual",
            )
        )

        async def _handle_theme(client: Any, args: list[str], context: Any) -> str:
            if not args:
                options = "  ".join(
                    f"[bold]{n}[/bold]" if n == self.theme else f"[dim]{n}[/dim]"
                    for n in _THEMES
                )
                return f"Theme: [bold]{self.theme}[/bold]   {options}"
            name = args[0].lower()
            if name not in _THEMES:
                avail = ", ".join(_THEMES.keys())
                return f"[yellow]Unknown theme:[/yellow] {name}. Options: {avail}"
            self.theme = name
            return f"[green]✓[/green] Theme → [bold]{name}[/bold]"

        self.registry.register(
            Command(
                name="theme",
                aliases=[],
                args=["name"],
                handler=_handle_theme,
                help_text="Switch color theme",
            )
        )

    def start_recording(self) -> None:
        """Begin capturing successful commands into a macro recording buffer."""
        self._recording = []

    def stop_recording(self) -> list[str] | None:
        """Stop recording and return captured commands, or None if not recording."""
        lines = self._recording
        self._recording = None
        return lines

    def emit_message(self, text: str) -> None:
        """Display a system message in the console (external API)."""
        self.query_one("#console-panel", ConsolePanel).system_message(text)

    async def dispatch(self, line: str) -> bool:
        """Dispatch a command string (external API)."""
        return await self._dispatch(line)

    async def connect(self, ip: str) -> None:
        """Manually initiate a connection (external API)."""
        self._connect(ip)

    async def on_unmount(self) -> None:
        """Dispose of resources on application exit."""
        if self.client and hasattr(self.client, "close"):
            await self.client.close()
        self.db.close()
