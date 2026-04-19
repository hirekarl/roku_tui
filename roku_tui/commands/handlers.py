from __future__ import annotations

import difflib
from typing import TYPE_CHECKING, Any

from rich.table import Table
from rich.text import Text

from .registry import Command, CommandRegistry

if TYPE_CHECKING:
    from ..ecp.models import AppInfo

KEYMAP: dict[str, str] = {
    "home": "Home",
    "back": "Back",
    "select": "Select",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "play": "Play",
    "pause": "Play",
    "rev": "Rev",
    "fwd": "Fwd",
    "replay": "InstantReplay",
    "info": "Info",
    "mute": "VolumeMute",
    "power": "PowerOff",
    "search": "Search",
    "enter": "Enter",
    "backspace": "Backspace",
}

VOLUME_MAP: dict[str, str] = {
    "up": "VolumeUp",
    "down": "VolumeDown",
    "mute": "VolumeMute",
}


async def handle_key(client: Any, args: list[str], context: Any) -> str:
    key_name = args[0] if args else "Select"
    ecp_key = KEYMAP.get(key_name, key_name)
    await client.keypress(ecp_key)
    return f"[dim]↵[/dim] [bold]{ecp_key}[/bold]"


async def handle_volume(client: Any, args: list[str], context: Any) -> str:
    direction = args[0].lower() if args else ""
    ecp_key = VOLUME_MAP.get(direction)
    if not ecp_key:
        return f"[red]Usage:[/red] volume up | down | mute"
    await client.keypress(ecp_key)
    return f"[dim]↵[/dim] [bold]{ecp_key}[/bold]"


async def handle_launch(client: Any, args: list[str], context: Any) -> str:
    if not args:
        return "[red]Usage:[/red] launch <app name>"
    query = " ".join(args).lower()
    app_cache: list[AppInfo] = context.app_cache

    if not app_cache:
        app_cache = await client.query_apps()
        context.app_cache = app_cache
        context.suggester.update_app_names([a.name for a in app_cache])

    names = [a.name for a in app_cache]
    matches = difflib.get_close_matches(query, [n.lower() for n in names], n=1, cutoff=0.4)
    if not matches:
        # Fallback: substring match
        for app in app_cache:
            if query in app.name.lower():
                matches = [app.name.lower()]
                break

    if not matches:
        return f"[red]No app matching[/red] '{query}'. Try [bold]apps[/bold] to see installed apps."

    matched_name = matches[0]
    app = next(a for a in app_cache if a.name.lower() == matched_name)
    await client.keypress(f"launch/{app.id}")
    try:
        context.db.log_app_launch(app, context._current_device_id())
    except Exception:
        pass
    return f"[dim]↵[/dim] Launched [bold #7aa2f7]{app.name}[/bold #7aa2f7]"


async def handle_apps(client: Any, args: list[str], context: Any) -> str:
    apps = await client.query_apps()
    context.app_cache = apps
    context.suggester.update_app_names([a.name for a in apps])

    table = Table(
        "ID", "Name", "Version",
        box=None,
        show_header=True,
        header_style="bold #7aa2f7",
        padding=(0, 2, 0, 0),
    )
    for app in apps:
        table.add_row(app.id, app.name, app.version)
    return table


async def handle_active(client: Any, args: list[str], context: Any) -> str:
    app = await client.query_active_app()
    if not app:
        return "[dim]No active app.[/dim]"
    return f"[bold #7aa2f7]{app.name}[/bold #7aa2f7] [dim](id: {app.id})[/dim]"


async def handle_device_info(client: Any, args: list[str], context: Any) -> str:
    info = await client.query_device_info()
    if not info:
        return "[red]Could not retrieve device info.[/red]"
    table = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    table.add_column(style="dim", width=18)
    table.add_column(style="bold")
    table.add_row("Device", info.friendly_name)
    table.add_row("Model", info.model_name)
    table.add_row("Serial", info.serial_number)
    table.add_row("Software", info.software_version)
    table.add_row("Ethernet MAC", info.ethernet_mac)
    table.add_row("Wi-Fi MAC", info.wifi_mac)
    return table


async def handle_connect(client: Any, args: list[str], context: Any) -> str:
    if not args:
        return "[red]Usage:[/red] connect <ip>"
    ip = args[0]
    await context.connect(ip)
    return f"[dim]Connecting to[/dim] [bold]{ip}[/bold]..."


async def handle_help(client: Any, args: list[str], context: Any) -> str:
    table = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    table.add_column(style=f"bold #7aa2f7", width=20)
    table.add_column(style="dim")
    for cmd in sorted(context.registry.all_commands(), key=lambda c: c.name):
        aliases = f"  [{', '.join(cmd.aliases)}]" if cmd.aliases else ""
        table.add_row(cmd.name + aliases, cmd.help_text)
    return table


async def handle_clear(client: Any, args: list[str], context: Any) -> str:
    context.query_one("#repl-panel").clear_history()
    return ""


def register_all(registry: CommandRegistry) -> None:
    nav_keys = ["home", "back", "select", "up", "down", "left", "right",
                 "play", "pause", "rev", "fwd", "replay", "mute", "power", "enter"]

    for key in nav_keys:
        ecp = KEYMAP.get(key, key)

        async def _handler(client, args, context, k=key):
            return await handle_key(client, [k], context)

        registry.register(Command(
            name=key,
            aliases=[],
            args=[],
            handler=_handler,
            help_text=f"Send {KEYMAP.get(key, key)} keypress",
        ))

    registry.register(Command(
        name="volume",
        aliases=["vol"],
        args=["up", "down", "mute"],
        handler=handle_volume,
        help_text="volume up | down | mute",
    ))
    registry.register(Command(
        name="launch",
        aliases=[],
        args=[],
        handler=handle_launch,
        help_text="Launch an app by name (fuzzy match)",
        dynamic_args=True,
    ))
    registry.register(Command(
        name="apps",
        aliases=["channels"],
        args=[],
        handler=handle_apps,
        help_text="List installed apps",
    ))
    registry.register(Command(
        name="active",
        aliases=["now"],
        args=[],
        handler=handle_active,
        help_text="Show currently active app",
    ))
    registry.register(Command(
        name="info",
        aliases=["device"],
        args=[],
        handler=handle_device_info,
        help_text="Show device information",
    ))
    registry.register(Command(
        name="connect",
        aliases=[],
        args=[],
        handler=handle_connect,
        help_text="connect <ip> — connect to a Roku device",
    ))
    registry.register(Command(
        name="help",
        aliases=["?", "h"],
        args=[],
        handler=handle_help,
        help_text="Show this help",
    ))
    registry.register(Command(
        name="clear",
        aliases=["cls"],
        args=[],
        handler=handle_clear,
        help_text="Clear the REPL history",
    ))
