from __future__ import annotations

from typing import Any

from rich.table import Table

from ..registry import Command, CommandRegistry
from .apps import (
    handle_active,
    handle_apps,
    handle_launch,
    handle_link,
    handle_youtube,
)
from .base import KEYMAP, LETTER_ALIASES, parse_count
from .fun import handle_ratsay
from .navigation import handle_key, handle_volume
from .system import (
    handle_connect,
    handle_device_info,
    handle_help,
    handle_kb,
    handle_type,
)

__all__ = [
    "handle_active",
    "handle_apps",
    "handle_connect",
    "handle_device_info",
    "handle_help",
    "handle_kb",
    "handle_key",
    "handle_launch",
    "handle_link",
    "handle_ratsay",
    "handle_type",
    "handle_volume",
    "handle_youtube",
    "parse_count",
    "register_all",
]


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
                aliases=[LETTER_ALIASES[key]] if key in LETTER_ALIASES else [],
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
