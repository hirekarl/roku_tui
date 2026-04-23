from __future__ import annotations

import pytest

from roku_tui.commands.handlers.fun import handle_ratsay


class MockContext:
    pass


@pytest.mark.asyncio
async def test_handle_ratsay_with_message() -> None:
    result = await handle_ratsay(None, ["Hello", "World"], MockContext())
    assert "Hello World" in result
    assert r"(\,;,/)" in result  # Part of the rat ASCII


@pytest.mark.asyncio
async def test_handle_ratsay_empty() -> None:
    result = await handle_ratsay(None, [], MockContext())
    assert r"(\,;,/)" in result
