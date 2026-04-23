from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest
from rich.table import Table

from roku_tui.commands.handlers.apps import handle_youtube


class MockContext:
    def __init__(self) -> None:
        self.db = Mock()
        self._yt_results: list[dict[str, str]] = []


@pytest.fixture
def mock_client() -> AsyncMock:
    client = AsyncMock()
    client.launch = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_yt_search_no_args() -> None:
    result = await handle_youtube(None, [], MockContext())
    assert isinstance(result, str) and "Usage" in result


@pytest.mark.asyncio
async def test_yt_search_success() -> None:
    ctx = MockContext()
    mock_results = [{"id": "vid123", "title": "Lo-fi Beats", "channel": "Lofi Girl"}]

    with patch("roku_tui.commands.handlers.apps.YouTubeClient") as MockYT:
        instance = MockYT.return_value
        instance.search = AsyncMock(return_value=mock_results)

        result = await handle_youtube(None, ["search", "lo-fi"], ctx)

        assert isinstance(result, Table)
        assert ctx._yt_results == mock_results
        instance.search.assert_called_once_with("lo-fi")


@pytest.mark.asyncio
async def test_yt_launch_by_id(mock_client: AsyncMock) -> None:
    ctx = MockContext()
    result = await handle_youtube(mock_client, ["launch", "vid123"], ctx)

    assert isinstance(result, str) and "YouTube launched" in result
    assert "vid123" in result
    mock_client.launch.assert_called_once()
    args, kwargs = mock_client.launch.call_args
    assert args[0] == "837"  # YouTube App ID
    assert kwargs["params"] == {"contentId": "vid123"}


@pytest.mark.asyncio
async def test_yt_launch_by_index(mock_client: AsyncMock) -> None:
    ctx = MockContext()
    ctx._yt_results = [{"id": "vid456", "title": "Test Video", "channel": "Test"}]

    result = await handle_youtube(mock_client, ["launch", "1"], ctx)

    assert isinstance(result, str) and "vid456" in result
    mock_client.launch.assert_called_once_with("837", params={"contentId": "vid456"})


@pytest.mark.asyncio
async def test_yt_save(mock_client: AsyncMock) -> None:
    ctx = MockContext()
    result = await handle_youtube(mock_client, ["save", "my-beat", "vid789"], ctx)

    assert isinstance(result, str) and "Saved YouTube alias" in result
    ctx.db.save_deep_link.assert_called_once_with("my-beat", "837", "YouTube", "vid789")
