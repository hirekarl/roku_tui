from __future__ import annotations

from textual.binding import Binding

# ── Bindings ──────────────────────────────────────────────────────────────────

BINDINGS: list[Binding | tuple[str, str] | tuple[str, str, str]] = [
    Binding("ctrl+q", "quit", "Quit"),
    Binding("ctrl+t", "toggle_tab", "Console/Remote"),
    Binding("ctrl+n", "toggle_network", "Network"),
    Binding("ctrl+l", "clear_console", "Clear"),
    Binding("f1", "show_guide", "Quick ref", key_display="F1"),
    Binding("f2", "show_manual", "Guide", key_display="F2"),
    Binding("/", "focus_network_filter", "Filter", show=False),
    Binding("c", "show_discovery", "Connect"),
]

# ── Hotkeys ───────────────────────────────────────────────────────────────────

# Universal navigation and control hotkeys (Arrows + Space + Backspace)
HOTKEYS: dict[str, str] = {
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "enter": "Select",
    "space": "Play",
    "backspace": "Back",
}

# Remote-tab specific hotkeys
REMOTE_HOTKEYS: dict[str, str] = {
    "h": "Home",
    "m": "VolumeMute",
    ",": "Rev",
    ".": "Fwd",
    "=": "VolumeUp",
    "-": "VolumeDown",
}

# ── Logic Constants ───────────────────────────────────────────────────────────

# Commands that should NOT be recorded into macros
RECORDING_SKIP: frozenset[str] = frozenset(
    {
        "macro",
        "history",
        "stats",
        "devices",
        "help",
        "clear",
        "cls",
        "guide",
        "theme",
    }
)
