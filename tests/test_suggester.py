from __future__ import annotations

import pytest

from roku_tui.commands.handlers import register_all
from roku_tui.commands.registry import CommandRegistry
from roku_tui.commands.suggester import RokuSuggester


@pytest.fixture
def suggester() -> RokuSuggester:
    from roku_tui.commands.db_commands import register_db_commands

    registry = CommandRegistry()
    register_all(registry)
    register_db_commands(registry)
    return RokuSuggester(registry)


# ── empty input ───────────────────────────────────────────────────────────────


async def test_empty_string_returns_none(suggester: RokuSuggester) -> None:
    assert await suggester.get_suggestion("") is None


async def test_whitespace_only_returns_none(suggester: RokuSuggester) -> None:
    assert await suggester.get_suggestion("   ") is None


# ── base command completion ───────────────────────────────────────────────────


async def test_completes_command_prefix(suggester: RokuSuggester) -> None:
    result = await suggester.get_suggestion("ho")
    assert result is not None
    assert "me" in result


async def test_completes_volume(suggester: RokuSuggester) -> None:
    result = await suggester.get_suggestion("vol")
    assert result is not None


async def test_no_match_returns_none(suggester: RokuSuggester) -> None:
    result = await suggester.get_suggestion("zzznomatch")
    assert result is None


async def test_full_command_with_trailing_space_returns_none(
    suggester: RokuSuggester,
) -> None:
    result = await suggester.get_suggestion("home ")
    assert result is None


# ── subcommand argument completion ───────────────────────────────────────────


async def test_completes_macro_subcommand(suggester: RokuSuggester) -> None:
    result = await suggester.get_suggestion("macro li")
    assert result is not None
    assert "st" in result


async def test_completes_history_search(suggester: RokuSuggester) -> None:
    result = await suggester.get_suggestion("history se")
    assert result is not None


async def test_no_subcommand_match_returns_none(suggester: RokuSuggester) -> None:
    result = await suggester.get_suggestion("macro zzz")
    assert result is None


async def test_command_no_subargs_returns_none(suggester: RokuSuggester) -> None:
    result = await suggester.get_suggestion("home li")
    assert result is None


# ── launch app name completion ────────────────────────────────────────────────


async def test_launch_with_partial_app_name(suggester: RokuSuggester) -> None:
    suggester.update_app_names(["Netflix", "Amazon Video", "Disney+"])
    result = await suggester.get_suggestion("launch Net")
    assert result is not None


async def test_launch_sorts_by_frequency(suggester: RokuSuggester) -> None:
    suggester.update_app_names(["Netflix", "Nebula"])
    suggester.update_launch_frequencies({"Nebula": 10, "Netflix": 1})
    result = await suggester.get_suggestion("launch Ne")
    # Nebula has higher freq, should come first
    assert result is not None
    assert "bula" in result


async def test_launch_no_app_match_returns_none(suggester: RokuSuggester) -> None:
    suggester.update_app_names(["Netflix", "Hulu"])
    result = await suggester.get_suggestion("launch zzznomatch")
    assert result is None


async def test_launch_with_trailing_space_returns_none(
    suggester: RokuSuggester,
) -> None:
    suggester.update_app_names(["Netflix"])
    result = await suggester.get_suggestion("launch ")
    assert result is None


async def test_update_app_names_sorts(suggester: RokuSuggester) -> None:
    suggester.update_app_names(["Zebra", "Apple", "Mango"])
    assert suggester._app_names == ["Apple", "Mango", "Zebra"]
