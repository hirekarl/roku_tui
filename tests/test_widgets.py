from __future__ import annotations

import pytest
from textual.widgets import DataTable, Label, Input

from roku_tui.ecp.models import NetworkEvent
from roku_tui.widgets.network_panel import NetworkPanel
from roku_tui.widgets.console_panel import ConsolePanel, CommandHighlighter
from roku_tui.commands.registry import CommandRegistry, Command
from roku_tui.commands.suggester import RokuSuggester


@pytest.fixture
def registry() -> CommandRegistry:
    reg = CommandRegistry()
    reg.register(Command("home", [], [], lambda *a, **k: "", "Home"))
    reg.register(Command("launch", ["l"], ["app"], lambda *a, **k: "", "Launch"))
    return reg


@pytest.fixture
def suggester(registry: CommandRegistry) -> RokuSuggester:
    return RokuSuggester(registry)


# ── NetworkPanel Tests ────────────────────────────────────────────────────────


async def test_network_panel_matches_filter() -> None:
    panel = NetworkPanel()
    
    # POST /keypress/Home
    ev1 = NetworkEvent("POST", "http://1.1.1.1:8060/keypress/Home", {}, 200)
    # GET /query/apps
    ev2 = NetworkEvent("GET", "http://1.1.1.1:8060/query/apps", {}, 200)
    
    panel._filter = "POST"
    assert panel._matches_filter(ev1) is True
    assert panel._matches_filter(ev2) is False
    
    panel._filter = "apps"
    assert panel._matches_filter(ev1) is False
    assert panel._matches_filter(ev2) is True
    
    panel._filter = "200"
    assert panel._matches_filter(ev1) is True
    assert panel._matches_filter(ev2) is True


async def test_network_panel_limits_events() -> None:
    panel = NetworkPanel()
    panel.MAX_EVENTS = 5
    from collections import deque
    panel._events = deque(maxlen=5)
    
    # Mock refresh_table because it requires the widget to be mounted
    panel._refresh_table = lambda: None
    
    for i in range(10):
        panel.add_event(NetworkEvent("GET", f"/test/{i}", {}, 200))
        
    assert len(panel._events) == 5
    assert panel._events[-1].url == "/test/9"


# ── ConsolePanel / Highlighter Tests ──────────────────────────────────────────


def test_command_highlighter_logic(registry: CommandRegistry) -> None:
    from rich.text import Text
    highlighter = CommandHighlighter(registry)
    
    # 1. Valid primary command
    t1 = Text("home")
    highlighter.highlight(t1)
    assert any(s.style == "bold #7aa2f7" for s in t1._spans)
    
    # 2. Valid alias
    t2 = Text("l netflix")
    highlighter.highlight(t2)
    assert any(s.style == "bold #bb9af7" for s in t2._spans)
    
    # 3. Unknown command
    t3 = Text("unknown")
    highlighter.highlight(t3)
    assert any(s.style == "bold #f7768e" for s in t3._spans)


async def test_console_panel_hint_updates(suggester: RokuSuggester, registry: CommandRegistry) -> None:
    panel = ConsolePanel(suggester, registry)
    
    hints = []
    def _mock_set_hint(content: str):
        hints.append(content)
    panel._set_hint = _mock_set_hint
    
    # 1. Type exact command
    panel.on_input_changed(Input.Changed(Input(), "launch"))
    assert "Launch" in hints[-1]
    
    # 2. Type command with space
    panel.on_input_changed(Input.Changed(Input(), "launch "))
    assert "Usage" in hints[-1]
    assert "[app]" in hints[-1]
