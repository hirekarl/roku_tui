from __future__ import annotations

from roku_tui.commands.handlers import (
    _parse_count,
    handle_connect,
    handle_launch,
    handle_volume,
    register_all,
)
from roku_tui.commands.registry import CommandRegistry
from typing import Any
from roku_tui.ecp.mock import MOCK_APPS, MockEcpClient
from roku_tui.ecp.models import AppInfo, NetworkEvent

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_client() -> tuple[MockEcpClient, list[NetworkEvent]]:
    events: list[NetworkEvent] = []
    return MockEcpClient(on_network_event=events.append), events


class _MockSuggester:
    def update_app_names(self, names: list[str]) -> None:
        pass


class _MockDb:
    def log_app_launch(self, app: AppInfo, device_id: int | None) -> None:
        pass

    def get_deep_link(self, alias: str) -> dict[str, Any] | None:
        return None

    def record_deep_link_launch(self, alias: str) -> None:
        pass


class MockContext:
    def __init__(self) -> None:
        self.app_cache: list[AppInfo] = []
        self.registry = CommandRegistry()
        self.suggester = _MockSuggester()
        self.db = _MockDb()

    def _current_device_id(self) -> int | None:
        return None


# ── _parse_count ──────────────────────────────────────────────────────────────


def test_parse_count_digit() -> None:
    assert _parse_count(["3"]) == 3


def test_parse_count_non_digit_defaults_to_one() -> None:
    assert _parse_count(["up"]) == 1


def test_parse_count_empty_args_defaults_to_one() -> None:
    assert _parse_count([]) == 1


def test_parse_count_capped_at_max() -> None:
    assert _parse_count(["999"]) == 30


def test_parse_count_at_offset() -> None:
    assert _parse_count(["up", "5"], offset=1) == 5


# ── handle_volume ─────────────────────────────────────────────────────────────


async def test_volume_up_sends_keypress() -> None:
    client, events = _make_client()
    result = await handle_volume(client, ["up"], MockContext())
    assert "VolumeUp" in result
    assert any("/keypress/VolumeUp" in e.url for e in events)


async def test_volume_down_sends_keypress() -> None:
    client, _events = _make_client()
    result = await handle_volume(client, ["down"], MockContext())
    assert "VolumeDown" in result


async def test_volume_mute_sends_keypress() -> None:
    client, _events = _make_client()
    result = await handle_volume(client, ["mute"], MockContext())
    assert "VolumeMute" in result


async def test_volume_invalid_direction_returns_usage() -> None:
    client, _ = _make_client()
    result = await handle_volume(client, ["sideways"], MockContext())
    assert "Usage" in result


async def test_volume_no_args_returns_usage() -> None:
    client, _ = _make_client()
    result = await handle_volume(client, [], MockContext())
    assert "Usage" in result


async def test_volume_with_count() -> None:
    client, events = _make_client()
    await handle_volume(client, ["up", "3"], MockContext())
    assert len(events) == 3


# ── handle_launch ─────────────────────────────────────────────────────────────


async def test_launch_no_args_returns_usage() -> None:
    client, _ = _make_client()
    result = await handle_launch(client, [], MockContext())
    assert "Usage" in result


async def test_launch_exact_match() -> None:
    client, events = _make_client()
    ctx = MockContext()
    ctx.app_cache = list(MOCK_APPS)
    result = await handle_launch(client, ["Netflix"], ctx)
    assert "Netflix" in result
    assert any("/launch/" in e.url for e in events)


async def test_launch_fuzzy_match() -> None:
    client, _events = _make_client()
    ctx = MockContext()
    ctx.app_cache = list(MOCK_APPS)
    result = await handle_launch(client, ["netflix"], ctx)
    assert "Netflix" in result


async def test_launch_substring_match() -> None:
    client, _events = _make_client()
    ctx = MockContext()
    ctx.app_cache = list(MOCK_APPS)
    result = await handle_launch(client, ["peace"], ctx)
    assert "Peacock" in result


async def test_launch_no_match_returns_error() -> None:
    client, _ = _make_client()
    ctx = MockContext()
    ctx.app_cache = list(MOCK_APPS)
    result = await handle_launch(client, ["zzzznotanapp"], ctx)
    assert "No app" in result


async def test_launch_fetches_apps_when_cache_empty() -> None:
    client, events = _make_client()
    ctx = MockContext()
    result = await handle_launch(client, ["netflix"], ctx)
    assert any("/query/apps" in e.url for e in events)
    assert "Netflix" in result


# ── handle_connect ────────────────────────────────────────────────────────────


async def test_connect_no_args_returns_usage() -> None:
    client, _ = _make_client()
    result = await handle_connect(client, [], MockContext())
    assert "Usage" in result


# ── register_all ─────────────────────────────────────────────────────────────


def test_register_all_includes_nav_commands() -> None:
    reg = CommandRegistry()
    register_all(reg)
    for name in ["home", "back", "select", "up", "down", "left", "right", "play"]:
        assert reg.lookup(name) is not None


def test_register_all_includes_single_letter_aliases() -> None:
    reg = CommandRegistry()
    register_all(reg)
    for alias in ["u", "d", "l", "r", "s", "b", "p", "m"]:
        assert reg.lookup(alias) is not None


def test_register_all_volume_alias() -> None:
    reg = CommandRegistry()
    register_all(reg)
    cmd = reg.lookup("vol")
    assert cmd is not None
    assert cmd.name == "volume"
