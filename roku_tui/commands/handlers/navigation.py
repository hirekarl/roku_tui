from __future__ import annotations

from typing import Any

from .base import KEYMAP, VOLUME_MAP, parse_count, repeat, repeat_suffix


async def handle_key(client: Any, args: list[str], context: Any) -> str:
    """Handle standard ECP keypress commands."""
    key_name = args[0] if args else "Select"
    count = parse_count(args, offset=1)
    ecp_key = KEYMAP.get(key_name, key_name)
    if client:
        await repeat(client, ecp_key, count)
    return f"[dim]↵[/dim] [bold]{ecp_key}[/bold]{repeat_suffix(count)}"


async def handle_volume(client: Any, args: list[str], context: Any) -> str:
    """Handle volume control commands."""
    direction = args[0].lower() if args else ""
    count = parse_count(args, offset=1)
    ecp_key = VOLUME_MAP.get(direction)
    if not ecp_key:
        return "[red]Usage:[/red] volume up | down | mute [count]"
    if client:
        await repeat(client, ecp_key, count)
    return f"[dim]↵[/dim] [bold]{ecp_key}[/bold]{repeat_suffix(count)}"
