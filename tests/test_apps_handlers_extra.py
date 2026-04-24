from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from rich.table import Table

from roku_tui.commands.handlers.apps import handle_active, handle_apps, handle_link
from roku_tui.ecp.mock import MOCK_APPS, MockEcpClient
from roku_tui.ecp.models import AppInfo, NetworkEvent


def _make_client() -> MockEcpClient:
    return MockEcpClient(on_network_event=lambda _: None)


class MockContext:
    def __init__(self) -> None:
        self.db: Any = Mock()
        self.app_cache: list[AppInfo] = []
        self._current_ip: str | None = None

    def _current_device_id(self) -> int | None:
        return None


# ── handle_apps ───────────────────────────────────────────────────────────────


async def test_handle_apps_no_client() -> None:
    result = await handle_apps(None, [], MockContext())
    assert "Not connected" in result


async def test_handle_apps_returns_table() -> None:
    ctx = MockContext()
    client = _make_client()
    result = await handle_apps(client, [], ctx)
    assert isinstance(result, Table)
    assert ctx.app_cache == list(MOCK_APPS)


async def test_handle_apps_updates_suggester() -> None:
    ctx = MockContext()
    ctx.suggester = Mock()  # type: ignore[attr-defined]
    client = _make_client()
    await handle_apps(client, [], ctx)
    ctx.suggester.update_app_names.assert_called_once()


# ── handle_active ─────────────────────────────────────────────────────────────


async def test_handle_active_no_client() -> None:
    result = await handle_active(None, [], MockContext())
    assert "Not connected" in result


async def test_handle_active_with_app() -> None:
    ctx = MockContext()
    client = _make_client()
    result = await handle_active(client, [], ctx)
    assert "Netflix" in result


async def test_handle_active_no_app() -> None:
    ctx = MockContext()
    client = Mock()
    client.query_active_app = AsyncMock(return_value=None)
    result = await handle_active(client, [], ctx)
    assert "No active app" in result


# ── handle_launch deep link path ─────────────────────────────────────────────


async def test_launch_deep_link() -> None:
    from roku_tui.commands.handlers.apps import handle_launch

    ctx = MockContext()
    ctx.db.get_deep_link.return_value = {
        "alias": "bb",
        "app_id": "2285",
        "app_name": "Netflix",
        "content_id": "tt0903747",
    }
    ctx.db.record_deep_link_launch = Mock()
    events: list[NetworkEvent] = []
    client = MockEcpClient(on_network_event=events.append)

    result = await handle_launch(client, ["bb"], ctx)
    assert "Deep link launched" in result
    assert "Netflix" in result
    assert any("/launch/2285" in e.url for e in events)
    assert any("contentId=tt0903747" in e.url for e in events)
    ctx.db.record_deep_link_launch.assert_called_once_with("bb")


async def test_launch_deep_link_no_client() -> None:
    from roku_tui.commands.handlers.apps import handle_launch

    ctx = MockContext()
    ctx.db.get_deep_link.return_value = {
        "alias": "bb",
        "app_id": "2285",
        "app_name": None,
        "content_id": "tt0903747",
    }
    ctx.db.record_deep_link_launch = Mock()

    result = await handle_launch(None, ["bb"], ctx)
    assert "Deep link launched" in result
    assert "App" in result


async def test_launch_substring_only_match() -> None:
    from roku_tui.commands.handlers.apps import handle_launch

    ctx = MockContext()
    ctx.db.get_deep_link.return_value = None
    # Use app name that won't fuzzy-match but will substring-match
    ctx.app_cache = [AppInfo("999", "XYZABCDEFGHIJKLMNO", "1.0", "ndka")]
    client = _make_client()

    result = await handle_launch(client, ["abc"], ctx)
    assert "XYZABCDEFGHIJKLMNO" in result


# ── handle_link ───────────────────────────────────────────────────────────────


async def test_link_save() -> None:
    ctx = MockContext()
    ctx.db.save_deep_link = Mock()
    result = await handle_link(None, ["save", "myalias", "netflix", "tt1234567"], ctx)
    assert "Saved" in result
    ctx.db.save_deep_link.assert_called_once()


async def test_link_save_missing_args() -> None:
    ctx = MockContext()
    result = await handle_link(None, ["save", "myalias"], ctx)
    assert "Usage" in result


async def test_link_list_empty() -> None:
    ctx = MockContext()
    ctx.db.list_deep_links.return_value = []
    result = await handle_link(None, ["list"], ctx)
    assert "No deep links" in result


async def test_link_list_with_data() -> None:
    ctx = MockContext()
    ctx.db.list_deep_links.return_value = [
        {
            "alias": "bb",
            "app_name": "Netflix",
            "content_id": "tt0903747",
            "launch_count": 3,
        }
    ]
    result = await handle_link(None, ["list"], ctx)
    assert isinstance(result, Table)


async def test_link_list_is_default() -> None:
    ctx = MockContext()
    ctx.db.list_deep_links.return_value = []
    result_explicit = await handle_link(None, ["list"], ctx)
    result_default = await handle_link(None, [], ctx)
    assert result_explicit == result_default


async def test_link_delete() -> None:
    ctx = MockContext()
    ctx.db.delete_deep_link = Mock()
    result = await handle_link(None, ["delete", "myalias"], ctx)
    assert "Deleted" in result
    ctx.db.delete_deep_link.assert_called_once_with("myalias")


async def test_link_delete_missing_arg() -> None:
    ctx = MockContext()
    result = await handle_link(None, ["delete"], ctx)
    assert "Usage" in result


async def test_link_unknown_sub() -> None:
    ctx = MockContext()
    result = await handle_link(None, ["unknown"], ctx)
    assert "Unknown link" in result


# ── handle_youtube extra paths ────────────────────────────────────────────────


async def test_yt_search_empty_query() -> None:
    from roku_tui.commands.handlers.apps import handle_youtube

    ctx = MockContext()
    result = await handle_youtube(None, ["search"], ctx)
    assert "Usage" in result


async def test_yt_search_no_results() -> None:
    from roku_tui.commands.handlers.apps import handle_youtube

    ctx = MockContext()
    with patch("roku_tui.commands.handlers.apps.YouTubeClient") as MockYT:
        instance = MockYT.return_value
        instance.search = AsyncMock(return_value=[])
        result = await handle_youtube(None, ["search", "nothing"], ctx)
    assert "No results" in result


async def test_yt_launch_missing_arg() -> None:
    from roku_tui.commands.handlers.apps import handle_youtube

    ctx = MockContext()
    result = await handle_youtube(None, ["launch"], ctx)
    assert "Usage" in result


async def test_yt_save_missing_args() -> None:
    from roku_tui.commands.handlers.apps import handle_youtube

    ctx = MockContext()
    result = await handle_youtube(None, ["save", "alias"], ctx)
    assert "Usage" in result


async def test_yt_unknown_subcommand() -> None:
    from roku_tui.commands.handlers.apps import handle_youtube

    ctx = MockContext()
    result = await handle_youtube(None, ["badcmd"], ctx)
    assert "Unknown yt command" in result


async def test_launch_no_app_cache_and_no_client() -> None:
    from roku_tui.commands.handlers.apps import handle_launch

    ctx = MockContext()
    ctx.db.get_deep_link.return_value = None
    ctx.app_cache = []
    result = await handle_launch(None, ["netflix"], ctx)
    assert "No app matching" in result
