from __future__ import annotations

import urllib.parse
from typing import Any

from rich.table import Table

from ..tips import LONG_HELP

_HELP_SECTIONS: list[tuple[str, list[str]]] = [
    (
        "Navigation",
        [
            "home",
            "back",
            "select",
            "up",
            "down",
            "left",
            "right",
            "play",
            "pause",
            "rev",
            "fwd",
            "replay",
            "mute",
            "power",
        ],
    ),
    ("Volume", ["volume"]),
    ("Apps & Deep Links", ["launch", "apps", "active", "link", "yt"]),
    ("Device", ["info", "connect", "devices"]),
    ("Macros & History", ["macro", "history", "stats", "sleep"]),
    ("Text Input", ["type", "kb"]),
    ("Session", ["guide", "tour", "about", "theme", "clear", "help", "version"]),
    ("Mascot", ["ratsay"]),
]


async def handle_device_info(client: Any, args: list[str], context: Any) -> Table | str:
    """Display detailed hardware and software information about the Roku."""
    if not client:
        return "[yellow]Not connected.[/yellow]"
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
    """Initiate a connection to a specific Roku IP address."""
    if not args:
        return "[red]Usage:[/red] connect <ip>"
    await context.connect(args[0])
    return f"[dim]Connecting to[/dim] [bold]{args[0]}[/bold]..."


async def handle_help(client: Any, args: list[str], context: Any) -> Table | str:
    """Display command help; with an argument, show detailed per-command docs."""
    if args:
        cmd_name = args[0].lower()
        if cmd_name in LONG_HELP:
            return LONG_HELP[cmd_name]
        cmd = context.registry.lookup(cmd_name)
        if cmd:
            aliases = f"  [dim][{', '.join(cmd.aliases)}][/dim]" if cmd.aliases else ""
            return (
                f"[bold #7aa2f7]{cmd.name}[/bold #7aa2f7]{aliases}\n\n"
                f"  {cmd.help_text}\n\n"
                "[dim]No extended help available for this command.[/dim]"
            )
        return (
            f"[yellow]Unknown command:[/yellow] '{cmd_name}'. "
            "Try [bold]help[/bold] for all commands."
        )

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
            aliases = f" [dim][{', '.join(cmd.aliases)}][/dim]" if cmd.aliases else ""
            table.add_row(
                f"  [bold #7aa2f7]{cmd.name}[/bold #7aa2f7]{aliases}",
                cmd.help_text,
            )
    return table


async def handle_type(client: Any, args: list[str], context: Any) -> str:
    """Send a string to the Roku as individual Lit_ keypresses."""
    if not args:
        return "[red]Usage:[/red] type <text>"
    text = " ".join(args)
    if client:
        for char in text:
            await client.keypress(f"Lit_{urllib.parse.quote(char, safe='')}")
    return f"[dim]↵[/dim] Typed: [bold]{text}[/bold]"


async def handle_kb(client: Any, args: list[str], context: Any) -> str:
    """Toggle keyboard passthrough mode."""
    context.toggle_keyboard_mode()
    return ""
