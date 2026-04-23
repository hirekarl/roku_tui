from __future__ import annotations

import asyncio
from typing import Any

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

VOLUME_MAP: dict[str, str] = {
    "up": "VolumeUp",
    "down": "VolumeDown",
    "mute": "VolumeMute",
}

MAX_REPEAT = 30
REPEAT_DELAY = 0.12

LETTER_ALIASES: dict[str, str] = {
    "up": "u",
    "down": "d",
    "left": "l",
    "right": "r",
    "select": "s",
    "back": "b",
    "play": "p",
    "mute": "m",
}


def parse_count(args: list[str], offset: int = 0) -> int:
    """Return repeat count from args[offset] if it's a digit string, else 1."""
    val = args[offset] if len(args) > offset else ""
    return min(int(val), MAX_REPEAT) if val.isdigit() else 1


async def repeat(client: Any, ecp_key: str, count: int) -> None:
    """Send a keypress to the Roku device multiple times."""
    for i in range(count):
        await client.keypress(ecp_key)
        if i < count - 1:
            await asyncio.sleep(REPEAT_DELAY)


def repeat_suffix(count: int) -> str:
    """Return a Rich markup suffix for repeated commands."""
    return f" [dim]×{count}[/dim]" if count > 1 else ""
