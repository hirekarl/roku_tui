from __future__ import annotations

import asyncio
import contextlib
import difflib
from typing import TYPE_CHECKING, Any

from rich.table import Table

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
    "power": "Power",
    "search": "Search",
    "enter": "Enter",
    "backspace": "Backspace",
}

_HELP_SECTIONS: list[tuple[str, list[str]]] = [
    ("Navigation", [
        "home", "back", "select", "up", "down", "left", "right",
        "play", "pause", "rev", "fwd", "replay", "mute", "power",
    ]),
    ("Volume",            ["volume"]),
    ("Apps",              ["launch", "apps", "active"]),
    ("Device",            ["info", "connect", "devices"]),
    ("Macros & History",  ["macro", "history", "stats", "sleep"]),
    ("Session",           ["help", "clear"]),
]

VOLUME_MAP: dict[str, str] = {
    "up": "VolumeUp",
    "down": "VolumeDown",
    "mute": "VolumeMute",
}

_MAX_REPEAT = 30
_REPEAT_DELAY = 0.12


def _parse_count(args: list[str], offset: int = 0) -> int:
    """Return repeat count from args[offset] if it's a digit string, else 1."""
    val = args[offset] if len(args) > offset else ""
    return min(int(val), _MAX_REPEAT) if val.isdigit() else 1


async def _repeat(client: Any, ecp_key: str, count: int) -> None:
    for i in range(count):
        await client.keypress(ecp_key)
        if i < count - 1:
            await asyncio.sleep(_REPEAT_DELAY)


def _repeat_suffix(count: int) -> str:
    return f" [dim]×{count}[/dim]" if count > 1 else ""


async def handle_key(client: Any, args: list[str], context: Any) -> str:
    key_name = args[0] if args else "Select"
    count = _parse_count(args, offset=1)
    ecp_key = KEYMAP.get(key_name, key_name)
    await _repeat(client, ecp_key, count)
    return f"[dim]↵[/dim] [bold]{ecp_key}[/bold]{_repeat_suffix(count)}"


async def handle_volume(client: Any, args: list[str], context: Any) -> str:
    direction = args[0].lower() if args else ""
    count = _parse_count(args, offset=1)
    ecp_key = VOLUME_MAP.get(direction)
    if not ecp_key:
        return "[red]Usage:[/red] volume up | down | mute [count]"
    await _repeat(client, ecp_key, count)
    return f"[dim]↵[/dim] [bold]{ecp_key}[/bold]{_repeat_suffix(count)}"


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
    matches = difflib.get_close_matches(
        query, [n.lower() for n in names], n=1, cutoff=0.4
    )
    if not matches:
        for app in app_cache:
            if query in app.name.lower():
                matches = [app.name.lower()]
                break

    if not matches:
        return (
            f"[yellow]No app matching[/yellow] '{query}'. "
            "Try [bold]apps[/bold] to see installed apps."
        )

    matched_name = matches[0]
    app = next(a for a in app_cache if a.name.lower() == matched_name)
    await client.launch(app.id)
    with contextlib.suppress(Exception):
        context.db.log_app_launch(app, context._current_device_id())
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
    await context.connect(args[0])
    return f"[dim]Connecting to[/dim] [bold]{args[0]}[/bold]..."


async def handle_help(client: Any, args: list[str], context: Any) -> Table:
    table = Table(box=None, show_header=False, padding=(0, 1, 0, 0))
    table.add_column(width=26)
    table.add_column(style="dim")
    for i, (section, names) in enumerate(_HELP_SECTIONS):
        if i > 0:
            table.add_row("", "")
        table.add_row(f"[bold #bb9af7]{section}[/bold #bb9af7]", "")
        for name in names:
            cmd = context.registry.lookup(name)
            if cmd is None:
                continue
            aliases = (
                f" [dim][{', '.join(cmd.aliases)}][/dim]" if cmd.aliases else ""
            )
            table.add_row(
                f"  [bold #7aa2f7]{cmd.name}[/bold #7aa2f7]{aliases}",
                cmd.help_text,
            )
    return table


async def handle_clear(client: Any, args: list[str], context: Any) -> str:
    context.query_one("#repl-panel").clear_history()
    return ""


_LETTER_ALIASES: dict[str, str] = {
    "up": "u", "down": "d", "left": "l", "right": "r",
    "select": "s", "back": "b", "play": "p", "mute": "m",
}


def register_all(registry: CommandRegistry) -> None:
    nav_keys = [
        "home", "back", "select", "up", "down", "left", "right",
        "play", "pause", "rev", "fwd", "replay", "mute", "power", "enter",
    ]

    for key in nav_keys:
        async def _handler(client, args, context, k=key):
            return await handle_key(client, [k, *args], context)

        if key == "pause":
            help_text = "Play/Pause toggle — same ECP key as play"
        else:
            help_text = f"Send {KEYMAP.get(key, key)} keypress  (add count: {key} 3)"

        registry.register(Command(
            name=key,
            aliases=[_LETTER_ALIASES[key]] if key in _LETTER_ALIASES else [],
            args=[],
            handler=_handler,
            help_text=help_text,
        ))

    registry.register(Command(
        name="volume",
        aliases=["vol"],
        args=["up", "down", "mute"],
        handler=handle_volume,
        help_text="volume up | down | mute  (add count: volume up 5)",
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
        aliases=["?"],
        args=[],
        handler=handle_help,
        help_text="Show command list  (or press ? for the full guide)",
    ))
    registry.register(Command(
        name="clear",
        aliases=["cls"],
        args=[],
        handler=handle_clear,
        help_text="Clear the REPL history",
    ))

    # Single-letter aliases for rapid navigation
    _aliases = [
        ("u", "up"), ("d", "down"), ("l", "left"), ("r", "right"),
        ("s", "select"), ("b", "back"), ("p", "play"), ("m", "mute"),
    ]
    for alias, target in _aliases:
        target_cmd = registry.lookup(target)
        if target_cmd:
            registry.register(Command(
                name=alias,
                aliases=[],
                args=[],
                handler=target_cmd.handler,
                help_text=f"Alias for {target}",
            ))
