from __future__ import annotations

import asyncio
import contextlib
import difflib
import urllib.parse
from typing import TYPE_CHECKING, Any

from rich.table import Table

from ..mascot import ratsay as _ratsay
from ..service_yt import YouTubeClient
from .registry import Command, CommandRegistry
from .tips import LONG_HELP

if TYPE_CHECKING:
    from ..ecp.models import AppInfo

APP_IDS: dict[str, str] = {
    "youtube": "837",
    "netflix": "12",
    "hulu": "2285",
    "disney": "291097",
    "pluto": "74519",
    "prime": "13",
}

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
    """Send a keypress to the Roku device multiple times."""
    for i in range(count):
        await client.keypress(ecp_key)
        if i < count - 1:
            await asyncio.sleep(_REPEAT_DELAY)


def _repeat_suffix(count: int) -> str:
    """Return a Rich markup suffix for repeated commands."""
    return f" [dim]×{count}[/dim]" if count > 1 else ""


async def handle_key(client: Any, args: list[str], context: Any) -> str:
    """Handle standard ECP keypress commands."""
    key_name = args[0] if args else "Select"
    count = _parse_count(args, offset=1)
    ecp_key = KEYMAP.get(key_name, key_name)
    if client:
        await _repeat(client, ecp_key, count)
    return f"[dim]↵[/dim] [bold]{ecp_key}[/bold]{_repeat_suffix(count)}"


async def handle_volume(client: Any, args: list[str], context: Any) -> str:
    """Handle volume control commands."""
    direction = args[0].lower() if args else ""
    count = _parse_count(args, offset=1)
    ecp_key = VOLUME_MAP.get(direction)
    if not ecp_key:
        return "[red]Usage:[/red] volume up | down | mute [count]"
    if client:
        await _repeat(client, ecp_key, count)
    return f"[dim]↵[/dim] [bold]{ecp_key}[/bold]{_repeat_suffix(count)}"


async def handle_launch(client: Any, args: list[str], context: Any) -> str:
    """Handle app launching by name or deep link alias."""
    if not args:
        return "[red]Usage:[/red] launch <app name | alias>"

    query = " ".join(args).lower()

    # 1. Try deep link alias first
    link = context.db.get_deep_link(query)
    if link:
        if client:
            p = {"contentId": link["content_id"]}
            await client.launch(link["app_id"], params=p)
        with contextlib.suppress(Exception):
            context.db.record_deep_link_launch(query)
        name = link["app_name"] or "App"
        return (
            f"[dim]↵[/dim] Deep link launched: [bold #7aa2f7]{name}[/bold #7aa2f7] "
            f"([dim]{link['alias']}[/dim])"
        )

    # 2. Try regular app launch
    app_cache: list[AppInfo] = context.app_cache

    if not app_cache and client:
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
    if client:
        await client.launch(app.id)
    with contextlib.suppress(Exception):
        context.db.log_app_launch(app, context._current_device_id())
    return f"[dim]↵[/dim] Launched [bold #7aa2f7]{app.name}[/bold #7aa2f7]"


async def handle_apps(client: Any, args: list[str], context: Any) -> Table | str:
    """List all installed apps on the Roku device."""
    if not client:
        return "[yellow]Not connected.[/yellow]"
    apps = await client.query_apps()
    context.app_cache = apps
    context.suggester.update_app_names([a.name for a in apps])
    table = Table(
        "ID",
        "Name",
        "Version",
        box=None,
        show_header=True,
        header_style="bold #7aa2f7",
        padding=(0, 2, 0, 0),
    )
    for app in apps:
        table.add_row(app.id, app.name, app.version)
    return table


async def handle_active(client: Any, args: list[str], context: Any) -> str:
    """Identify the currently active/foreground app."""
    if not client:
        return "[yellow]Not connected.[/yellow]"
    app = await client.query_active_app()
    if not app:
        return "[dim]No active app.[/dim]"
    return f"[bold #7aa2f7]{app.name}[/bold #7aa2f7] [dim](id: {app.id})[/dim]"


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


async def handle_link(client: Any, args: list[str], context: Any) -> Table | str:
    """Manage persistent deep link content shortcuts."""
    sub = args[0].lower() if args else "list"

    if sub == "save":
        if len(args) < 4:
            return "[red]Usage:[/red] link save <alias> <app_name | id> <content_id>"
        alias, app_input, content_id = args[1].lower(), args[2].lower(), args[3]

        # Resolve app ID
        app_id = APP_IDS.get(app_input, app_input)

        context.db.save_deep_link(alias, app_id, app_input.capitalize(), content_id)
        return f"[green]✓[/green] Saved deep link alias: [bold]{alias}[/bold]"

    elif sub == "list":
        links = context.db.list_deep_links()
        if not links:
            return (
                "[dim]No deep links saved. Use [bold]link save[/bold] to add one.[/dim]"
            )

        table = Table(
            "Alias",
            "App",
            "Content ID",
            "L-Count",
            box=None,
            show_header=True,
            header_style="bold #bb9af7",
            padding=(0, 2, 0, 0),
        )
        for link in links:
            table.add_row(
                link["alias"],
                link["app_name"] or "Unknown",
                link["content_id"],
                str(link["launch_count"]),
            )
        return table

    elif sub == "delete":
        if len(args) < 2:
            return "[red]Usage:[/red] link delete <alias>"
        context.db.delete_deep_link(args[1].lower())
        return f"[green]✓[/green] Deleted alias: [bold]{args[1].lower()}[/bold]"

    else:
        return "[red]Unknown link command.[/red] Try: list, save, delete"


async def handle_youtube(client: Any, args: list[str], context: Any) -> Table | str:
    """Search for and launch YouTube content."""
    if not args:
        usage = (
            "[red]Usage:[/red] yt search <query> | "
            "yt launch <id> | yt save <alias> <id>"
        )
        return usage

    sub = args[0].lower()
    yt_client = YouTubeClient()
    yt_app_id = APP_IDS["youtube"]

    if sub == "search":
        query = " ".join(args[1:])
        if not query:
            return "[red]Usage:[/red] yt search <query>"

        results = await yt_client.search(query)
        if not results:
            return "[yellow]No results found.[/yellow]"

        context._yt_results = results  # Cache for numerical launch

        table = Table(
            "#",
            "Title",
            "Channel",
            "ID",
            box=None,
            show_header=True,
            header_style="bold #f70000",
            padding=(0, 2, 0, 0),
        )
        for i, res in enumerate(results, 1):
            table.add_row(str(i), res["title"], res["channel"], res["id"])

        table.add_section()
        table.add_row(
            "",
            "[dim]Type [bold]yt launch 1[/bold] to play first result[/dim]",
            "",
            "",
        )
        return table

    elif sub == "launch":
        if len(args) < 2:
            return "[red]Usage:[/red] yt launch <id | index>"

        val = args[1]
        video_id = val

        # Check if it's a numeric index from last search
        if val.isdigit() and hasattr(context, "_yt_results"):
            idx = int(val) - 1
            if 0 <= idx < len(context._yt_results):
                video_id = context._yt_results[idx]["id"]

        if client:
            await client.launch(yt_app_id, params={"contentId": video_id})
        return f"[dim]↵[/dim] YouTube launched: [bold]{video_id}[/bold]"

    elif sub == "save":
        if len(args) < 3:
            return "[red]Usage:[/red] yt save <alias> <id>"
        alias, video_id = args[1].lower(), args[2]
        context.db.save_deep_link(alias, yt_app_id, "YouTube", video_id)
        return f"[green]✓[/green] Saved YouTube alias: [bold]{alias}[/bold]"

    return f"[red]Unknown yt command:[/red] {sub}"


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


_LETTER_ALIASES: dict[str, str] = {
    "up": "u",
    "down": "d",
    "left": "l",
    "right": "r",
    "select": "s",
    "back": "b",
    "play": "p",
    "mute": "m",
}


def register_all(registry: CommandRegistry) -> None:
    """Register all available console commands into the registry."""
    nav_keys = [
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
        "enter",
    ]

    for key in nav_keys:

        async def _h(
            client: Any, args: list[str], context: Any, k: str = key
        ) -> str | Table:
            return await handle_key(client, [k, *args], context)

        if key == "pause":
            help_text = "Play/Pause toggle — same ECP key as play"
        else:
            help_text = f"Send {KEYMAP.get(key, key)} keypress  (add count: {key} 3)"

        registry.register(
            Command(
                name=key,
                aliases=[_LETTER_ALIASES[key]] if key in _LETTER_ALIASES else [],
                args=[],
                handler=_h,
                help_text=help_text,
            )
        )

    registry.register(
        Command(
            name="volume",
            aliases=["vol"],
            args=["up", "down", "mute"],
            handler=handle_volume,
            help_text="volume up | down | mute  (add count: volume up 5)",
        )
    )
    registry.register(
        Command(
            name="launch",
            aliases=[],
            args=[],
            handler=handle_launch,
            help_text="Launch app by name or deep link alias",
            dynamic_args=True,
        )
    )
    registry.register(
        Command(
            name="link",
            aliases=["shortcut"],
            args=["list", "save", "delete"],
            handler=handle_link,
            help_text="Manage deep link shortcuts",
            dynamic_args=True,
        )
    )
    registry.register(
        Command(
            name="yt",
            aliases=["youtube"],
            args=["search", "launch", "save"],
            handler=handle_youtube,
            help_text="YouTube search and deep linking",
            dynamic_args=True,
        )
    )
    registry.register(
        Command(
            name="apps",
            aliases=["channels"],
            args=[],
            handler=handle_apps,
            help_text="List installed apps",
        )
    )
    registry.register(
        Command(
            name="active",
            aliases=["now"],
            args=[],
            handler=handle_active,
            help_text="Show currently active app",
        )
    )
    registry.register(
        Command(
            name="info",
            aliases=["device"],
            args=[],
            handler=handle_device_info,
            help_text="Show device information",
        )
    )
    registry.register(
        Command(
            name="connect",
            aliases=[],
            args=[],
            handler=handle_connect,
            help_text="connect <ip> — connect to a Roku device",
        )
    )
    registry.register(
        Command(
            name="help",
            aliases=["?"],
            args=[],
            handler=handle_help,
            help_text="Show command list  (or press ? for the full guide)",
        )
    )

    registry.register(
        Command(
            name="type",
            aliases=[],
            args=[],
            handler=handle_type,
            help_text="type <text> — send text to the TV as keypresses",
            dynamic_args=True,
        )
    )
    registry.register(
        Command(
            name="kb",
            aliases=["keyboard"],
            args=[],
            handler=handle_kb,
            help_text="Toggle keyboard passthrough mode  (ESC to exit)",
        )
    )

    async def handle_ratsay(client: Any, args: list[str], context: Any) -> str:
        return _ratsay(" ".join(args) if args else None)

    registry.register(
        Command(
            name="ratsay",
            aliases=[],
            args=[],
            handler=handle_ratsay,
            help_text="ratsay <message> — print a message with the mascot",
            dynamic_args=True,
        )
    )

    # Single-letter aliases for rapid navigation
    _aliases = [
        ("u", "up"),
        ("d", "down"),
        ("l", "left"),
        ("r", "right"),
        ("s", "select"),
        ("b", "back"),
        ("p", "play"),
        ("m", "mute"),
    ]
    for alias, target in _aliases:
        target_cmd = registry.lookup(target)
        if target_cmd:
            registry.register(
                Command(
                    name=alias,
                    aliases=[],
                    args=[],
                    handler=target_cmd.handler,
                    help_text=f"Alias for {target}",
                )
            )
