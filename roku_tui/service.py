from __future__ import annotations

import asyncio
import contextlib
import urllib.parse
from pathlib import Path
from typing import Any

import platformdirs
from rich.console import Console

from .commands.db_commands import register_db_commands
from .commands.handlers import register_all
from .commands.registry import CommandRegistry
from .commands.tui_commands import register_tui_commands
from .constants import RECORDING_SKIP
from .db import Database
from .ecp.client import EcpClient
from .ecp.discovery import discover_rokus, probe_roku
from .ecp.mock import MockEcpClient
from .ecp.models import AppInfo, NetworkEvent


class RokuService:
    """Headless service for Roku interaction."""

    def __init__(
        self,
        mock: bool = False,
        db_path: Path | None = None,
        output_callback: Any = None,
    ):
        self.mock = mock
        self.db = Database(db_path or self._get_default_db_path())
        self.registry = CommandRegistry()
        self.client: EcpClient | MockEcpClient | None = None
        self._current_ip: str | None = None
        self.app_cache: list[AppInfo] = []
        self._recording: list[str] | None = None
        self.output_callback = output_callback

        # Initialize
        self.db.initialize()
        register_all(self.registry)
        register_db_commands(self.registry)
        register_tui_commands(self.registry, self)  # type: ignore

        if self.mock:
            self._init_mock()

    def _get_default_db_path(self) -> Path:
        data_dir = Path(platformdirs.user_data_dir("roku-tui"))
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "roku_tui.db"

    def _init_mock(self) -> None:
        self._current_ip = "mock-roku"
        self.client = MockEcpClient(on_network_event=self._on_network_event)

    def _on_network_event(self, event: NetworkEvent) -> None:
        device_id = self._current_device_id()
        with contextlib.suppress(Exception):
            self.db.log_network_request(event, device_id)

    def _current_device_id(self) -> int | None:
        try:
            return self.db.get_device_id(self._current_ip) if self._current_ip else None
        except Exception:
            return None

    async def connect(self, ip: str) -> None:
        if "://" not in ip:
            url = f"http://{ip}:8060"
        else:
            url = ip

        base_url = url.rstrip("/")
        if not base_url.endswith(":8060"):
            base_url = base_url.split(":8060")[0] + ":8060"

        self._current_ip = base_url.split("://")[-1].split(":")[0]
        self.client = EcpClient(
            base_url=base_url, on_network_event=self._on_network_event
        )

        # Prefetch apps to warm cache
        try:
            self.app_cache = await self.client.query_apps()
            info = await self.client.query_device_info()
            if info:
                self.db.upsert_device(info, self._current_ip)
                dev_id = self.db.get_device_id(self._current_ip)
                if dev_id:
                    self.db.sync_device_apps(self.app_cache, dev_id)
        except Exception:
            pass

    async def discover(self) -> str | None:
        """Find a Roku on the network."""
        known_ips = self.db.known_device_ips()
        for ip in known_ips:
            if probe_roku(ip):
                return ip

        urls = discover_rokus(timeout=3.0)
        if urls:
            return urls[0].split("://")[-1].split(":")[0]
        return None

    async def dispatch(self, line: str, context: Any = None) -> bool:
        """Execute a command string."""
        success = True
        ctx = context or self
        for part in [p.strip() for p in line.split(";") if p.strip()]:
            if not await self._dispatch_single(part, context=ctx):
                success = False
        return success

    async def _dispatch_single(self, line: str, context: Any = None) -> bool:
        if self.client is None and line.split()[0] not in RECORDING_SKIP:
            self._output("[bold yellow]Not connected.[/bold yellow]")
            return False

        result = self.registry.parse(line)
        if result is None:
            self._output(f"[red]Unknown command:[/red] [bold]{line.split()[0]}[/bold]")
            return False

        cmd, args = result
        ctx = context or self
        try:
            output = await cmd.handler(self.client, args, context=ctx)
            if output:
                self._output(output)
            return True
        except Exception as e:
            self._output(f"[red]Error:[/red] {e}")
            return False
        finally:
            dev_id = self._current_device_id()
            self.db.log_command(line, success=True, device_id=dev_id)
            if self._recording is not None and line.split()[0] not in RECORDING_SKIP:
                self._recording.append(line)

    def _output(self, content: Any) -> None:
        if self.output_callback:
            self.output_callback(content)
        else:
            # Fallback to rich console printing for headless
            Console().print(content)

    # Compat methods for handlers that expect certain app methods
    def toggle_keyboard_mode(self) -> None:
        pass

    def start_recording(self) -> None:
        self._recording = []

    def stop_recording(self) -> list[str] | None:
        lines, self._recording = self._recording, None
        return lines

    # UI actions that handlers might call (though they shouldn't in headless)
    def action_show_about(self) -> None:
        pass

    def action_show_manual(self) -> None:
        pass

    def action_show_tour(self) -> None:
        pass

    def action_clear_console(self) -> None:
        pass

    async def close(self) -> None:
        if self.client:
            await self.client.close()
        self.db.close()
