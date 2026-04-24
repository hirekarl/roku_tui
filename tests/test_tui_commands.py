from __future__ import annotations

from typing import Any

from roku_tui.commands.registry import CommandRegistry
from roku_tui.commands.tui_commands import register_tui_commands
from roku_tui.themes import THEMES


class MockApp:
    def __init__(self) -> None:
        self.theme = "roku-night"
        self._cleared = False
        self._manual_shown = False
        self._tour_shown = False
        self._about_shown = False

    def action_clear_console(self) -> None:
        self._cleared = True

    def action_show_manual(self) -> None:
        self._manual_shown = True

    def action_show_tour(self) -> None:
        self._tour_shown = True

    def action_show_about(self) -> None:
        self._about_shown = True


def _make_registry(app: MockApp | None = None) -> tuple[CommandRegistry, MockApp]:
    registry = CommandRegistry()
    mock_app = app or MockApp()
    register_tui_commands(registry, mock_app)  # type: ignore[arg-type]
    return registry, mock_app


async def _call(registry: CommandRegistry, name: str, args: list[str], ctx: Any) -> Any:
    cmd = registry.lookup(name)
    assert cmd is not None
    return await cmd.handler(None, args, ctx)


# ── clear ─────────────────────────────────────────────────────────────────────


async def test_clear_calls_action() -> None:
    registry, app = _make_registry()
    result = await _call(registry, "clear", [], app)
    assert result == ""
    assert app._cleared is True


# ── guide ─────────────────────────────────────────────────────────────────────


async def test_guide_calls_action() -> None:
    registry, app = _make_registry()
    result = await _call(registry, "guide", [], app)
    assert result == ""
    assert app._manual_shown is True


# ── tour ──────────────────────────────────────────────────────────────────────


async def test_tour_calls_action() -> None:
    registry, app = _make_registry()
    result = await _call(registry, "tour", [], app)
    assert result == ""
    assert app._tour_shown is True


# ── about ─────────────────────────────────────────────────────────────────────


async def test_about_calls_action() -> None:
    registry, app = _make_registry()
    result = await _call(registry, "about", [], app)
    assert result == ""
    assert app._about_shown is True


# ── version ───────────────────────────────────────────────────────────────────


async def test_version_returns_string() -> None:
    registry, app = _make_registry()
    result = await _call(registry, "version", [], app)
    assert "roku-tui" in result


# ── theme ─────────────────────────────────────────────────────────────────────


async def test_theme_no_args_shows_current() -> None:
    registry, app = _make_registry()
    result = await _call(registry, "theme", [], app)
    assert "roku-night" in result


async def test_theme_switches_valid_theme() -> None:
    registry, app = _make_registry()
    valid = next(n for n in THEMES if n != "roku-night")
    result = await _call(registry, "theme", [valid], app)
    assert valid in result
    assert app.theme == valid


async def test_theme_unknown_returns_error() -> None:
    registry, app = _make_registry()
    result = await _call(registry, "theme", ["nonexistent"], app)
    assert "Unknown theme" in result


async def test_theme_context_without_theme_attr() -> None:
    registry, _app = _make_registry()

    class NoThemeCtx:
        pass

    result = await _call(registry, "theme", ["nord"], NoThemeCtx())
    assert "nord" in result
