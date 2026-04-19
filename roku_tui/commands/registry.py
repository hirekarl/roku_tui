from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass
class Command:
    name: str
    aliases: list[str]
    args: list[str]
    handler: Callable[..., Awaitable[str]]
    help_text: str
    dynamic_args: bool = False


class CommandRegistry:
    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._alias_map: dict[str, str] = {}

    def register(self, cmd: Command) -> None:
        self._commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self._alias_map[alias] = cmd.name

    def lookup(self, name: str) -> Command | None:
        if name in self._commands:
            return self._commands[name]
        canonical = self._alias_map.get(name)
        return self._commands.get(canonical) if canonical else None

    def all_names(self) -> list[str]:
        return sorted(self._commands.keys())

    def all_commands(self) -> list[Command]:
        return list(self._commands.values())

    def parse(self, line: str) -> tuple[Command, list[str]] | None:
        parts = line.strip().split()
        if not parts:
            return None
        cmd = self.lookup(parts[0])
        if cmd is None:
            return None
        return cmd, parts[1:]
