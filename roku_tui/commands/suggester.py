from __future__ import annotations

from textual.suggester import Suggester

from .registry import CommandRegistry


class RokuSuggester(Suggester):
    def __init__(self, registry: CommandRegistry):
        super().__init__(use_cache=False, case_sensitive=False)
        self._registry = registry
        self._app_names: list[str] = []

    def update_app_names(self, names: list[str]) -> None:
        self._app_names = names

    async def get_suggestion(self, value: str) -> str | None:
        if not value.strip():
            return None

        parts = value.split()
        has_trailing_space = value.endswith(" ")

        # Complete the first token (command name)
        if len(parts) == 1 and not has_trailing_space:
            prefix = parts[0].lower()
            all_names = self._registry.all_names()
            # Also include aliases
            all_completions: list[str] = []
            for cmd in self._registry.all_commands():
                all_completions.append(cmd.name)
                all_completions.extend(cmd.aliases)
            for name in sorted(all_completions):
                if name.startswith(prefix) and name != prefix:
                    return name
            return None

        # Complete the argument (second token)
        cmd_name = parts[0].lower()
        cmd = self._registry.lookup(cmd_name)
        if cmd is None:
            return None

        args_pool = self._app_names if cmd.dynamic_args else cmd.args
        if not args_pool:
            return None

        prefix = parts[-1].lower() if not has_trailing_space and len(parts) > 1 else ""
        for arg in args_pool:
            if arg.lower().startswith(prefix) and arg.lower() != prefix:
                if cmd.dynamic_args:
                    return f"{cmd_name} {arg}"
                return f"{cmd_name} {arg}"
        return None
