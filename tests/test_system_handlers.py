from __future__ import annotations

from unittest.mock import AsyncMock, Mock

from rich.table import Table

from roku_tui.commands.handlers.system import (
    handle_connect,
    handle_device_info,
    handle_help,
    handle_kb,
    handle_type,
)
from roku_tui.commands.registry import CommandRegistry
from roku_tui.ecp.mock import MockEcpClient
from roku_tui.ecp.models import NetworkEvent


def _make_client() -> MockEcpClient:
    return MockEcpClient(on_network_event=lambda _: None)


class MockContext:
    def __init__(self) -> None:
        self.registry = CommandRegistry()
        self._kb_toggled = False

    def toggle_keyboard_mode(self) -> None:
        self._kb_toggled = True

    async def connect(self, ip: str) -> None:
        pass


# ── handle_device_info ────────────────────────────────────────────────────────


async def test_device_info_no_client() -> None:
    result = await handle_device_info(None, [], MockContext())
    assert "Not connected" in result


async def test_device_info_returns_table() -> None:
    ctx = MockContext()
    client = _make_client()
    result = await handle_device_info(client, [], ctx)
    assert isinstance(result, Table)


async def test_device_info_no_response() -> None:
    ctx = MockContext()
    client = Mock()
    client.query_device_info = AsyncMock(return_value=None)
    result = await handle_device_info(client, [], ctx)
    assert "Could not retrieve" in result


# ── handle_connect ────────────────────────────────────────────────────────────


async def test_connect_with_ip() -> None:
    ctx = MockContext()
    result = await handle_connect(None, ["192.168.1.50"], ctx)
    assert "Connecting" in result
    assert "192.168.1.50" in result


# ── handle_help ───────────────────────────────────────────────────────────────


async def test_help_no_args_returns_table() -> None:
    from roku_tui.commands.handlers import register_all

    ctx = MockContext()
    register_all(ctx.registry)
    result = await handle_help(None, [], ctx)
    assert isinstance(result, Table)


async def test_help_with_known_long_help_key() -> None:
    ctx = MockContext()
    result = await handle_help(None, ["yt"], ctx)
    assert isinstance(result, str)
    assert "yt" in result.lower()


async def test_help_with_registry_command() -> None:
    from roku_tui.commands.handlers import register_all

    ctx = MockContext()
    register_all(ctx.registry)
    result = await handle_help(None, ["home"], ctx)
    assert isinstance(result, str)
    assert "home" in result.lower()


async def test_help_unknown_command() -> None:
    ctx = MockContext()
    result = await handle_help(None, ["zzznope"], ctx)
    assert "Unknown command" in result


# ── handle_type ───────────────────────────────────────────────────────────────


async def test_type_no_args() -> None:
    result = await handle_type(None, [], MockContext())
    assert "Usage" in result


async def test_type_with_client() -> None:
    ctx = MockContext()
    events: list[NetworkEvent] = []
    client = MockEcpClient(on_network_event=events.append)
    result = await handle_type(client, ["hello"], ctx)
    assert "hello" in result
    assert len(events) == 5
    assert "/keypress/Lit_h" in events[0].url


async def test_type_no_client() -> None:
    ctx = MockContext()
    result = await handle_type(None, ["hello world"], ctx)
    assert "hello world" in result


async def test_type_multi_word() -> None:
    ctx = MockContext()
    events: list[NetworkEvent] = []
    client = MockEcpClient(on_network_event=events.append)
    result = await handle_type(client, ["hello", "world"], ctx)
    assert "hello world" in result
    assert len(events) == 11
    assert "/keypress/Lit_%20" in events[5].url


# ── handle_kb ────────────────────────────────────────────────────────────────


async def test_kb_toggles_keyboard_mode() -> None:
    ctx = MockContext()
    result = await handle_kb(None, [], ctx)
    assert result == ""
    assert ctx._kb_toggled is True
