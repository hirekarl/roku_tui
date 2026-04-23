from __future__ import annotations

from typing import Any

from ...mascot import ratsay


async def handle_ratsay(client: Any, args: list[str], context: Any) -> str:
    """Print a message with the rat mascot."""
    return ratsay(" ".join(args) if args else None)
