from __future__ import annotations

from roku_tui.commands.registry import Command, CommandRegistry


async def _noop(client, args, context):
    return "ok"


def _make_registry() -> CommandRegistry:
    reg = CommandRegistry()
    reg.register(
        Command(
            name="foo", aliases=["f", "fo"], args=[], handler=_noop, help_text="Foo"
        )
    )
    reg.register(
        Command(name="bar", aliases=[], args=["x"], handler=_noop, help_text="Bar")
    )
    return reg


def test_parse_known_command():
    reg = _make_registry()
    result = reg.parse("foo")
    assert result is not None
    cmd, args = result
    assert cmd.name == "foo"
    assert args == []


def test_parse_passes_args():
    reg = _make_registry()
    result = reg.parse("bar hello world")
    assert result is not None
    cmd, args = result
    assert cmd.name == "bar"
    assert args == ["hello", "world"]


def test_parse_via_alias():
    reg = _make_registry()
    result = reg.parse("f")
    assert result is not None
    assert result[0].name == "foo"


def test_parse_via_second_alias():
    reg = _make_registry()
    result = reg.parse("fo extra")
    assert result is not None
    cmd, args = result
    assert cmd.name == "foo"
    assert args == ["extra"]


def test_parse_unknown_returns_none():
    reg = _make_registry()
    assert reg.parse("zzz") is None


def test_parse_whitespace_only_returns_none():
    reg = _make_registry()
    assert reg.parse("   ") is None


def test_parse_empty_returns_none():
    reg = _make_registry()
    assert reg.parse("") is None


def test_all_names_sorted():
    reg = _make_registry()
    names = reg.all_names()
    assert names == sorted(names)


def test_lookup_by_name():
    reg = _make_registry()
    cmd = reg.lookup("foo")
    assert cmd is not None
    assert cmd.name == "foo"


def test_lookup_by_alias():
    reg = _make_registry()
    cmd = reg.lookup("f")
    assert cmd is not None
    assert cmd.name == "foo"


def test_lookup_missing_returns_none():
    reg = _make_registry()
    assert reg.lookup("zzz") is None


def test_all_commands_returns_list():
    reg = _make_registry()
    cmds = reg.all_commands()
    assert len(cmds) == 2
    assert {c.name for c in cmds} == {"foo", "bar"}
