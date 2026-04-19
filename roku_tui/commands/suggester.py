from __future__ import annotations

from typing import TYPE_CHECKING

from textual.suggester import Suggester

if TYPE_CHECKING:
    from .registry import CommandRegistry


class RokuSuggester(Suggester):
    def __init__(self, registry: CommandRegistry):
        super().__init__(use_cache=False, case_sensitive=False)
        self._registry = registry
        self._app_names: list[str] = []
        self._launch_frequencies: dict[str, int] = {}

    def update_app_names(self, names: list[str]) -> None:
        self._app_names = sorted(names)

    def update_launch_frequencies(self, freq: dict[str, int]) -> None:
        self._launch_frequencies = freq

    async def get_suggestion(self, value: str) -> str | None:
        parts = value.strip().split()
        if not parts:
            return None

        # 1. Base command completion
        if len(parts) == 1 and not value.endswith(" "):
            typed = parts[0].lower()
            matches = [c for c in self._registry.all_names() if c.startswith(typed)]
            if matches:
                return matches[0][len(typed) :]
            return None

        # 2. Argument completion (subcommands)
        cmd_name = parts[0].lower()
        if cmd_name in self._registry.all_names():
            cmd = self._registry.lookup(cmd_name)
            if cmd and cmd.args:
                if len(parts) > 1:
                    sub = parts[1].lower()
                    matches = [a for a in cmd.args if a.startswith(sub)]
                    if matches:
                        return matches[0][len(sub) :]
                return None

        # 3. App name completion for 'launch'
        if cmd_name == "launch" and len(parts) >= 1 and value.endswith(" "):
            # If nothing typed yet, return nothing or most frequent
            return None

        if cmd_name == "launch" and len(parts) > 1:
            typed_name = " ".join(parts[1:]).lower()
            if not typed_name:
                return None

            # Sort by frequency, then alpha
            candidates = [
                n for n in self._app_names if n.lower().startswith(typed_name)
            ]
            if candidates:
                candidates.sort(
                    key=lambda x: (self._launch_frequencies.get(x, 0), x), reverse=True
                )
                match = candidates[0]
                return match[len(typed_name) :]

        return None
