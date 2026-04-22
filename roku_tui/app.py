from __future__ import annotations

import asyncio
import contextlib
import sys
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Any

import platformdirs
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.events import Key
from textual.widgets import Footer, Header, Input, TabbedContent, TabPane

from .actions import RokuActions
from .commands.suggester import RokuSuggester
from .constants import BINDINGS, HOTKEYS, REMOTE_HOTKEYS
from .service import RokuService
from .themes import THEMES, TOKYO_NIGHT
from .widgets.console_panel import ConsolePanel
from .widgets.network_panel import NetworkPanel
from .widgets.remote_panel import RemotePanel
from .widgets.status_bar import StatusBar

if TYPE_CHECKING:
    from .ecp.models import NetworkEvent


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
        self.service = RokuService(mock=mock, output_callback=self._on_service_output)
        self.initial_ip = initial_ip
        self._kb_mode: bool = False
        self.suggester = RokuSuggester(self.service.registry)

    @property
    def client(self) -> Any:
        return self.service.client

    @client.setter
    def client(self, value: Any) -> None:
        self.service.client = value

    @property
    def registry(self) -> Any:
        return self.service.registry

    @property
    def db(self) -> Any:
        return self.service.db

    @property
    def app_cache(self) -> Any:
        return self.service.app_cache

    @app_cache.setter
    def app_cache(self, value: Any) -> None:
        self.service.app_cache = value

    @property
    def _current_ip(self) -> str | None:
        return self.service._current_ip

    def _on_service_output(self, content: Any) -> None:
        """Handle output from the RokuService."""
        with contextlib.suppress(Exception):
            self.query_one("#console-panel", ConsolePanel).output(content)

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
        """Initialize themes and start connection."""
        for t in THEMES.values():
            self.register_theme(t)
        self.theme = "roku-night"

        # Override service's default event handler to route to UI
        if self.service.client:
            client: Any = self.service.client
            client.on_network_event = self._on_network_event

        if self.service.mock:
            self._init_ui_mock()
        elif self.initial_ip:
            self._connect(self.initial_ip)
        else:
            # action_show_discovery is from RokuActions mixin
            app: Any = self
            app.action_show_discovery()

    def _init_ui_mock(self) -> None:
        """Update UI for mock mode."""
        self.query_one("#status-bar", StatusBar).set_connected(
            "My Roku TV (Mock)", mock=True
        )
        self.query_one("#console-panel", ConsolePanel).system_message(
            "[dim]Running in [bold]mock mode[/bold][/dim]"
        )
        self.query_one("#remote-panel", RemotePanel).set_connected(True)
        self._prefetch_info()

    def _connect(self, url: str) -> None:
        """Connect to a Roku device via the service."""
        self.run_worker(self._async_connect(url))

    async def _async_connect(self, url: str) -> None:
        await self.service.connect(url)
        # Update client's callback to our UI-aware one
        if self.service.client:
            client: Any = self.service.client
            client.on_network_event = self._on_network_event

        self.query_one("#remote-panel", RemotePanel).set_connected(True)
        self._prefetch_info()

    @work
    async def _prefetch_info(self) -> None:
        """Update UI with device info and apps."""
        client = self.service.client
        if not client:
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

            freq = await asyncio.to_thread(self.db.app_launch_frequencies)
            self.suggester.update_launch_frequencies(freq)
            self.suggester.update_app_names([a.name for a in self.service.app_cache])
        except Exception:
            pass

    def _on_network_event(self, event: NetworkEvent) -> None:
        """Route network events to UI and service logic."""
        self.post_message(self.NetworkEventReceived(event))
        self.service._on_network_event(event)

    def on_roku_actions_network_event_received(
        self, msg: RokuActions.NetworkEventReceived
    ) -> None:
        """Handle network event messages in UI."""
        with contextlib.suppress(Exception):
            self.query_one("#network-panel", NetworkPanel).add_event(msg.event)

    async def on_console_panel_command_submitted(
        self, msg: ConsolePanel.CommandSubmitted
    ) -> None:
        """Handle command submission from the console panel."""
        await self.service.dispatch(msg.line, context=self)

    async def on_remote_panel_button_activated(
        self, msg: RemotePanel.ButtonActivated
    ) -> None:
        """Handle virtual button presses from the Remote panel."""
        if self.service.client:
            await self.service.client.keypress(msg.ecp_key)
            self.db.log_command(
                f"remote:{msg.ecp_key}",
                success=True,
                device_id=self._current_device_id(),
            )

    async def dispatch(self, line: str) -> bool:
        return await self.service.dispatch(line, context=self)

    async def _dispatch(self, line: str) -> bool:
        """Legacy dispatch for any handlers still calling it."""
        return await self.service._dispatch_single(line, context=self)

    def _current_device_id(self) -> int | None:
        return self.service._current_device_id()

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

    def start_recording(self) -> None:
        self.service.start_recording()

    def stop_recording(self) -> list[str] | None:
        return self.service.stop_recording()

    def emit_message(self, text: str) -> None:
        self.query_one("#console-panel", ConsolePanel).system_message(text)

    async def connect(self, ip: str) -> None:
        self._connect(ip)

    async def on_unmount(self) -> None:
        await self.service.close()
