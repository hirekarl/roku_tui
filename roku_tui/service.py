from __future__ import annotations

import asyncio
import contextlib
import difflib
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from .commands.db_commands import register_db_commands
from .commands.handlers import register_all
from .commands.registry import CommandRegistry
from .commands.suggester import RokuSuggester
from .db.database import Database
from .ecp.client import EcpClient
from .ecp.mock import MockEcpClient
from .ecp.models import AppInfo, NetworkEvent


def _normalize_url(url: str) -> str:
    if "://" not in url:
        url = f"http://{url}:8060"
    base_url = url.rstrip("/")
    if not base_url.endswith(":8060"):
        base_url = base_url.split(":8060")[0] + ":8060"
    return base_url


@runtime_checkable
class HandlerContext(Protocol):
    """Interface that any Roku interface (TUI, bot, etc.) must satisfy so that
    command handlers can run without knowing which UI they're inside."""

    db: Database
    app_cache: list[AppInfo]
    client: EcpClient | MockEcpClient | None
    registry: CommandRegistry
    suggester: RokuSuggester

    def current_device_id(self) -> int | None: ...
    async def connect(self, ip: str) -> None: ...
    def emit_message(self, text: str) -> None: ...
    async def dispatch(self, line: str) -> bool: ...


class RokuService:
    """Owns an EcpClient and DB handle for one interface.

    Create one instance per interface (TUI, Discord bot, etc.) inside that
    interface's event loop. Do NOT share an instance across event loops —
    httpx.AsyncClient binds to the loop that was running at creation time.

    Shared state (history, macros, device info) lives in the SQLite DB,
    which is safe to access from multiple processes via separate instances.
    """

    def __init__(
        self,
        db: Database,
        client: EcpClient | MockEcpClient | None = None,
        on_message: Callable[[str], None] | None = None,
        on_network_event: Callable[[NetworkEvent], None] | None = None,
    ) -> None:
        self.db = db
        self.client = client
        self._on_message = on_message or (lambda _: None)
        self._on_network_event = on_network_event or (lambda _: None)
        self.app_cache: list[AppInfo] = []
        self._current_ip: str | None = None
        self.registry = CommandRegistry()
        self.suggester = RokuSuggester(self.registry)
        register_all(self.registry)
        register_db_commands(self.registry)

    # ── HandlerContext protocol ────────────────────────────────────────────

    def emit_message(self, text: str) -> None:
        self._on_message(text)

    async def dispatch(self, line: str) -> bool:
        success, _ = await self.execute(line)
        return success

    def current_device_id(self) -> int | None:
        if not self._current_ip:
            return None
        with contextlib.suppress(Exception):
            return self.db.get_device_id(self._current_ip)
        return None

    async def connect(self, ip: str) -> None:
        base_url = _normalize_url(ip)
        if self.client and hasattr(self.client, "close"):
            await self.client.close()
        self._current_ip = base_url.split("://")[-1].split(":")[0]
        self.client = EcpClient(
            base_url=base_url, on_network_event=self._on_network_event
        )
        self._prefetch_task = asyncio.create_task(self._prefetch_info())

    # ── Core execution ────────────────────────────────────────────────────

    async def execute(self, line: str) -> tuple[bool, Any]:
        """Parse and run a command. Returns (success, output)."""
        line = line.strip()
        if not line:
            return False, None

        _no_client_needed = {
            "connect", "help", "?", "macro", "history", "stats", "devices", "sleep",
        }
        if self.client is None and line.split()[0] not in _no_client_needed:
            return (
                False,
                "[yellow]Not connected.[/yellow] Use [bold]connect <ip>[/bold] first.",
            )

        result = self.registry.parse(line)
        if result is None:
            cmd_name = line.split()[0]
            suggestions = difflib.get_close_matches(
                cmd_name, list(self.registry.all_names()), n=1, cutoff=0.6
            )
            hint = f" — did you mean {suggestions[0]}?" if suggestions else ""
            return False, f"Unknown command: {cmd_name}{hint}"

        cmd, args = result
        try:
            output = await cmd.handler(self.client, args, context=self)
            self.db.log_command(line, success=True, device_id=self.current_device_id())
            return True, output
        except Exception as e:
            self.db.log_command(line, success=False, device_id=self.current_device_id())
            return False, f"Error: {e}"

    async def _prefetch_info(self) -> None:
        if not self.client or not self._current_ip:
            return
        device_id: int | None = None
        info = None
        try:
            info = await self.client.query_device_info()
            if info:
                device_id = await asyncio.to_thread(
                    self.db.upsert_device, info, self._current_ip
                )
                cached_apps = await asyncio.to_thread(
                    self.db.get_device_apps, device_id
                )
                if cached_apps:
                    freq = await asyncio.to_thread(self.db.app_launch_frequencies)
                    self.suggester.update_launch_frequencies(freq)
                    self.suggester.update_app_names(
                        [a["app_name"] for a in cached_apps]
                    )
                self.emit_message(
                    f"[dim]Connected to[/dim] [bold]{info.friendly_name}[/bold]"
                )

            apps = await self.client.query_apps()
            self.app_cache = apps
            if info and device_id is not None:
                await asyncio.to_thread(self.db.sync_device_apps, apps, device_id)

            freq = await asyncio.to_thread(self.db.app_launch_frequencies)
            self.suggester.update_launch_frequencies(freq)
            self.suggester.update_app_names([a.name for a in apps])
        except Exception:
            self.emit_message(
                "[red]Connection failed.[/red] Check the IP and try again."
            )

    async def close(self) -> None:
        if self.client and hasattr(self.client, "close"):
            await self.client.close()
