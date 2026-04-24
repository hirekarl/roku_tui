from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import Mock

import pytest
from rich.table import Table

from roku_tui.commands.db_commands import (
    handle_devices,
    handle_history,
    handle_macro,
    handle_sleep,
    handle_stats,
)


class MockContext:
    def __init__(self) -> None:
        self.db: Any = Mock()
        self._messages: list[str] = []
        self._recording: list[str] | None = None

    def emit_message(self, msg: str) -> None:
        self._messages.append(msg)

    async def dispatch(self, line: str) -> bool:
        return True

    def start_recording(self) -> None:
        self._recording = []

    def stop_recording(self) -> list[str] | None:
        lines, self._recording = self._recording, None
        return lines


# ── handle_sleep ──────────────────────────────────────────────────────────────


async def test_sleep_no_args() -> None:
    result = await handle_sleep(None, [], MockContext())
    assert "Usage" in result


async def test_sleep_bad_value() -> None:
    result = await handle_sleep(None, ["notanumber"], MockContext())
    assert "Usage" in result


async def test_sleep_zero() -> None:
    result = await handle_sleep(None, ["0"], MockContext())
    assert "value must be between" in result


async def test_sleep_too_large() -> None:
    result = await handle_sleep(None, ["999"], MockContext())
    assert "value must be between" in result


async def test_sleep_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []

    async def fake_sleep(s: float) -> None:
        slept.append(s)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    result = await handle_sleep(None, ["0.5"], MockContext())
    assert "Slept" in result
    assert slept == [pytest.approx(0.5)]


# ── handle_history ────────────────────────────────────────────────────────────


async def test_history_empty() -> None:
    ctx = MockContext()
    ctx.db.recent_commands.return_value = []
    result = await handle_history(None, [], ctx)
    assert "No command history" in result


async def test_history_with_rows() -> None:
    from io import StringIO

    from rich.console import Console

    ctx = MockContext()
    ctx.db.recent_commands.return_value = [
        {"executed_at": datetime(2025, 1, 1, 12, 0), "line": "home", "success": True}
    ]
    result = await handle_history(None, [], ctx)
    assert isinstance(result, Table)
    buf = StringIO()
    Console(file=buf, width=120, highlight=False).print(result)
    rendered = buf.getvalue()
    assert "home" in rendered
    assert "✓" in rendered


async def test_history_with_limit() -> None:
    ctx = MockContext()
    ctx.db.recent_commands.return_value = []
    await handle_history(None, ["5"], ctx)
    ctx.db.recent_commands.assert_called_once_with(5)


async def test_history_search_no_term() -> None:
    ctx = MockContext()
    result = await handle_history(None, ["search"], ctx)
    assert "Usage" in result


async def test_history_search_with_results() -> None:
    ctx = MockContext()
    ctx.db.search_commands.return_value = [
        {
            "executed_at": datetime(2025, 1, 1, 12, 0),
            "line": "launch netflix",
            "success": True,
        }
    ]
    result = await handle_history(None, ["search", "netflix"], ctx)
    assert isinstance(result, Table)


async def test_history_search_empty_results() -> None:
    ctx = MockContext()
    ctx.db.search_commands.return_value = []
    result = await handle_history(None, ["search", "zzz"], ctx)
    assert "No command history" in result


async def test_history_row_with_failed_command() -> None:
    ctx = MockContext()
    ctx.db.recent_commands.return_value = [
        {"executed_at": None, "line": "badcmd", "success": False}
    ]
    result = await handle_history(None, [], ctx)
    assert isinstance(result, Table)


# ── handle_stats ──────────────────────────────────────────────────────────────


async def test_stats_empty() -> None:
    ctx = MockContext()
    ctx.db.usage_stats.return_value = {
        "top_apps": [],
        "top_commands": [],
        "total_days": 0,
    }
    result = await handle_stats(None, [], ctx)
    assert isinstance(result, Table)


async def test_stats_with_data() -> None:
    from io import StringIO

    from rich.console import Console

    ctx = MockContext()
    ctx.db.usage_stats.return_value = {
        "top_apps": [{"app_name": "Netflix", "count": 5}],
        "top_commands": [{"line": "home", "count": 10}],
        "total_days": 3,
    }
    result = await handle_stats(None, [], ctx)
    assert isinstance(result, Table)
    buf = StringIO()
    Console(file=buf, width=120, highlight=False).print(result)
    rendered = buf.getvalue()
    assert "Days active" in rendered
    assert "Netflix" in rendered


# ── handle_devices ────────────────────────────────────────────────────────────


async def test_devices_empty() -> None:
    ctx = MockContext()
    ctx.db.list_devices.return_value = []
    result = await handle_devices(None, [], ctx)
    assert "No devices" in result


async def test_devices_with_data() -> None:
    ctx = MockContext()
    ctx.db.list_devices.return_value = [
        {
            "ip": "192.168.1.50",
            "friendly_name": "Living Room Roku",
            "model_name": "Express",
            "last_connected_at": datetime(2025, 1, 1, 12, 0),
            "connect_count": 3,
        }
    ]
    result = await handle_devices(None, [], ctx)
    assert isinstance(result, Table)


async def test_devices_null_timestamp() -> None:
    ctx = MockContext()
    ctx.db.list_devices.return_value = [
        {
            "ip": "10.0.0.1",
            "friendly_name": None,
            "model_name": None,
            "last_connected_at": None,
            "connect_count": 0,
        }
    ]
    result = await handle_devices(None, [], ctx)
    assert isinstance(result, Table)


# ── handle_macro unknown / missing sub ───────────────────────────────────────


async def test_macro_no_args_shows_usage() -> None:
    ctx = MockContext()
    result = await handle_macro(None, [], ctx)
    assert "Usage" in result


async def test_macro_unknown_sub_shows_usage() -> None:
    ctx = MockContext()
    result = await handle_macro(None, ["badcmd"], ctx)
    assert "Usage" in result


# ── macro list ────────────────────────────────────────────────────────────────


async def test_macro_list_empty() -> None:
    ctx = MockContext()
    ctx.db.list_macros.return_value = []
    result = await handle_macro(None, ["list"], ctx)
    assert "No macros" in result


async def test_macro_list_with_user_macro() -> None:
    from io import StringIO

    from rich.console import Console

    ctx = MockContext()
    ctx.db.list_macros.return_value = [
        {
            "name": "mymacro",
            "description": "Does stuff",
            "run_count": 2,
            "is_builtin": False,
            "abort_on_fail": False,
        }
    ]
    result = await handle_macro(None, ["list"], ctx)
    assert isinstance(result, Table)
    buf = StringIO()
    Console(file=buf, width=120, highlight=False).print(result)
    rendered = buf.getvalue()
    assert "mymacro" in rendered
    assert "Does stuff" in rendered
    assert "2" in rendered
    assert "user" in rendered


async def test_macro_list_builtin_badge() -> None:
    from io import StringIO

    from rich.console import Console

    ctx = MockContext()
    ctx.db.list_macros.return_value = [
        {
            "name": "boot",
            "description": "Boot sequence",
            "run_count": 5,
            "is_builtin": True,
            "abort_on_fail": False,
        }
    ]
    result = await handle_macro(None, ["list"], ctx)
    assert isinstance(result, Table)
    buf = StringIO()
    Console(file=buf, width=120, highlight=False).print(result)
    rendered = buf.getvalue()
    assert "boot" in rendered
    assert "Boot sequence" in rendered
    assert "builtin" in rendered


async def test_macro_list_abort_badge() -> None:
    from io import StringIO

    from rich.console import Console

    ctx = MockContext()
    ctx.db.list_macros.return_value = [
        {
            "name": "critical",
            "description": None,
            "run_count": 0,
            "is_builtin": False,
            "abort_on_fail": True,
        }
    ]
    result = await handle_macro(None, ["list"], ctx)
    assert isinstance(result, Table)
    buf = StringIO()
    Console(file=buf, width=120, highlight=False).print(result)
    rendered = " ".join(buf.getvalue().split())
    assert "critical" in rendered
    assert "user abort" in rendered


# ── macro run ─────────────────────────────────────────────────────────────────


async def test_macro_run_no_name() -> None:
    ctx = MockContext()
    result = await handle_macro(None, ["run"], ctx)
    assert "Usage" in result


async def test_macro_run_not_found() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = None
    result = await handle_macro(None, ["run", "ghost"], ctx)
    assert "No macro" in result


async def test_macro_run_success() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = {
        "abort_on_fail": False,
        "commands": ["home", "up"],
    }
    ctx.db.record_macro_run = Mock()
    result = await handle_macro(None, ["run", "mymacro"], ctx)
    assert "done" in result


async def test_macro_run_single_step() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = {
        "abort_on_fail": False,
        "commands": ["home"],
    }
    ctx.db.record_macro_run = Mock()
    result = await handle_macro(None, ["run", "single"], ctx)
    assert "1 step" in result


async def test_macro_run_abort_on_fail() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = {
        "abort_on_fail": True,
        "commands": ["home", "badcmd"],
    }
    ctx.db.record_macro_run = Mock()
    call_count = [0]

    async def failing_dispatch(line: str) -> bool:
        call_count[0] += 1
        return call_count[0] == 1

    ctx.dispatch = failing_dispatch  # type: ignore[method-assign]
    result = await handle_macro(None, ["run", "mymacro"], ctx)
    assert "aborted" in result


# ── macro record ──────────────────────────────────────────────────────────────


async def test_macro_record_starts_recording() -> None:
    ctx = MockContext()
    result = await handle_macro(None, ["record"], ctx)
    assert "Recording started" in result
    assert ctx._recording == []


# ── macro stop ────────────────────────────────────────────────────────────────


async def test_macro_stop_no_name() -> None:
    ctx = MockContext()
    result = await handle_macro(None, ["stop"], ctx)
    assert "Usage" in result


async def test_macro_stop_no_active_recording() -> None:
    ctx = MockContext()
    ctx._recording = None
    result = await handle_macro(None, ["stop", "myname"], ctx)
    assert "No recording" in result


async def test_macro_stop_empty_recording() -> None:
    ctx = MockContext()
    ctx._recording = []
    result = await handle_macro(None, ["stop", "myname"], ctx)
    assert "Nothing recorded" in result


async def test_macro_stop_saves_macro() -> None:
    ctx = MockContext()
    ctx._recording = ["home", "up 3"]
    ctx.db.save_macro = Mock()
    result = await handle_macro(None, ["stop", "myname", "my description"], ctx)
    assert "saved" in result
    ctx.db.save_macro.assert_called_once_with(
        "myname", "my description", ["home", "up 3"]
    )


async def test_macro_stop_save_error() -> None:
    ctx = MockContext()
    ctx._recording = ["home"]
    ctx.db.save_macro = Mock(side_effect=ValueError("Cannot overwrite builtin"))
    result = await handle_macro(None, ["stop", "boot"], ctx)
    assert "Error" in result


# ── macro show ────────────────────────────────────────────────────────────────


async def test_macro_show_no_name() -> None:
    ctx = MockContext()
    result = await handle_macro(None, ["show"], ctx)
    assert "Usage" in result


async def test_macro_show_not_found() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = None
    result = await handle_macro(None, ["show", "ghost"], ctx)
    assert "No macro" in result


async def test_macro_show_found_abort_on() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = {
        "name": "mymacro",
        "abort_on_fail": True,
        "commands": ["home", "up"],
    }
    result = await handle_macro(None, ["show", "mymacro"], ctx)
    assert isinstance(result, Table)


async def test_macro_show_found_abort_off() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = {
        "name": "mymacro",
        "abort_on_fail": False,
        "commands": ["home"],
    }
    result = await handle_macro(None, ["show", "mymacro"], ctx)
    assert isinstance(result, Table)


# ── macro set ─────────────────────────────────────────────────────────────────


async def test_macro_set_bad_args() -> None:
    ctx = MockContext()
    result = await handle_macro(None, ["set"], ctx)
    assert "Usage" in result


async def test_macro_set_wrong_flag() -> None:
    ctx = MockContext()
    result = await handle_macro(None, ["set", "name", "abort", "maybe"], ctx)
    assert "Usage" in result


async def test_macro_set_not_found() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = None
    result = await handle_macro(None, ["set", "ghost", "abort", "on"], ctx)
    assert "No macro" in result


async def test_macro_set_on() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = {"name": "mymacro"}
    ctx.db.set_macro_abort_flag = Mock()
    result = await handle_macro(None, ["set", "mymacro", "abort", "on"], ctx)
    ctx.db.set_macro_abort_flag.assert_called_once_with("mymacro", True)
    assert "mymacro" in result


async def test_macro_set_off() -> None:
    ctx = MockContext()
    ctx.db.get_macro.return_value = {"name": "mymacro"}
    ctx.db.set_macro_abort_flag = Mock()
    result = await handle_macro(None, ["set", "mymacro", "abort", "off"], ctx)
    ctx.db.set_macro_abort_flag.assert_called_once_with("mymacro", False)
    assert "mymacro" in result


# ── macro delete ──────────────────────────────────────────────────────────────


async def test_macro_delete_no_name() -> None:
    ctx = MockContext()
    result = await handle_macro(None, ["delete"], ctx)
    assert "Usage" in result


async def test_macro_delete_success() -> None:
    ctx = MockContext()
    ctx.db.delete_macro = Mock()
    result = await handle_macro(None, ["delete", "mymacro"], ctx)
    assert "Deleted" in result
    ctx.db.delete_macro.assert_called_once_with("mymacro")


async def test_macro_delete_error() -> None:
    ctx = MockContext()
    ctx.db.delete_macro = Mock(side_effect=ValueError("Cannot delete builtin"))
    result = await handle_macro(None, ["delete", "boot"], ctx)
    assert "Error" in result
