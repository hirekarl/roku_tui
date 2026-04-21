from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..themes import THEMES
from .registry import Command

if TYPE_CHECKING:
    from ..app import RokuTuiApp
    from ..commands.registry import CommandRegistry


def register_tui_commands(registry: CommandRegistry, app: RokuTuiApp) -> None:
    """Register built-in TUI-specific commands like 'clear' and 'theme'."""

    async def _handle_clear(client: Any, args: list[str], context: Any) -> str:
        app.action_clear_console()
        return ""

    registry.register(
        Command(
            name="clear",
            aliases=["cls"],
            args=[],
            handler=_handle_clear,
            help_text="Clear the console history",
        )
    )

    async def _handle_guide(client: Any, args: list[str], context: Any) -> str:
        app.action_show_manual()
        return ""

    registry.register(
        Command(
            name="guide",
            aliases=[],
            args=[],
            handler=_handle_guide,
            help_text="Open the full user manual",
        )
    )

    async def _handle_theme(client: Any, args: list[str], context: Any) -> str:
        if not args:
            options = "  ".join(
                f"[bold]{n}[/bold]" if n == app.theme else f"[dim]{n}[/dim]"
                for n in THEMES
            )
            return f"Theme: [bold]{app.theme}[/bold]   {options}"
        name = args[0].lower()
        if name not in THEMES:
            avail = ", ".join(THEMES.keys())
            return f"[yellow]Unknown theme:[/yellow] {name}. Options: {avail}"
        app.theme = name
        return f"[green]✓[/green] Theme → [bold]{name}[/bold]"

    registry.register(
        Command(
            name="theme",
            aliases=[],
            args=["name"],
            handler=_handle_theme,
            help_text="Switch color theme",
        )
    )
