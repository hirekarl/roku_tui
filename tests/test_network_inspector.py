from __future__ import annotations

from textual.app import App, ComposeResult

from roku_tui.ecp.models import NetworkEvent
from roku_tui.widgets.network_inspector import NetworkInspector


def _make_event(**kwargs) -> NetworkEvent:
    defaults = dict(
        method="GET",
        url="http://192.168.1.50:8060/query/apps",
        request_headers={"Host": "192.168.1.50:8060"},
        status_code=200,
        response_headers={"Content-Type": "text/xml"},
        response_time_ms=42.5,
        body="<apps><app id='2285'>Netflix</app></apps>",
        error=None,
    )
    defaults.update(kwargs)
    return NetworkEvent(**defaults)


class _InspectorApp(App):
    def __init__(self, event: NetworkEvent) -> None:
        super().__init__()
        self._event = event

    def compose(self) -> ComposeResult:
        yield NetworkInspector(self._event)


# ── compose / on_mount ────────────────────────────────────────────────────────


async def test_inspector_mounts_with_xml_body() -> None:
    app = _InspectorApp(_make_event())
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(NetworkInspector)
        assert inspector is not None


async def test_inspector_mounts_with_json_body() -> None:
    app = _InspectorApp(
        _make_event(body='{"key": "value", "nested": {"a": 1}}', status_code=200)
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(NetworkInspector)
        assert inspector is not None


async def test_inspector_mounts_with_error() -> None:
    app = _InspectorApp(
        _make_event(body="", error="Connection refused", status_code=None)
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(NetworkInspector)
        assert inspector is not None


async def test_inspector_mounts_with_empty_body() -> None:
    app = _InspectorApp(_make_event(body=""))
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(NetworkInspector)
        assert inspector is not None


async def test_inspector_mounts_with_plain_text_body() -> None:
    app = _InspectorApp(_make_event(body="plain text response"))
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(NetworkInspector)
        assert inspector is not None


async def test_inspector_error_status_code() -> None:
    app = _InspectorApp(_make_event(status_code=404))
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(NetworkInspector)
        assert inspector is not None


async def test_inspector_empty_headers() -> None:
    app = _InspectorApp(_make_event(request_headers={}, response_headers={}))
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(NetworkInspector)
        assert inspector is not None


# ── _format_headers ───────────────────────────────────────────────────────────


def test_format_headers_empty() -> None:
    event = _make_event()
    inspector = NetworkInspector(event)
    result = inspector._format_headers({})
    assert "None" in str(result)


def test_format_headers_with_values() -> None:
    event = _make_event()
    inspector = NetworkInspector(event)
    result = inspector._format_headers(
        {"Content-Type": "text/xml", "Host": "localhost"}
    )
    assert "Content-Type" in str(result)
    assert "text/xml" in str(result)


# ── _format_body ──────────────────────────────────────────────────────────────


def test_format_body_json() -> None:
    event = _make_event()
    inspector = NetworkInspector(event)
    result = inspector._format_body('{"key": "value"}')
    from rich.syntax import Syntax

    assert isinstance(result, Syntax)


def test_format_body_xml() -> None:
    event = _make_event()
    inspector = NetworkInspector(event)
    result = inspector._format_body("<root><child>data</child></root>")
    from rich.syntax import Syntax

    assert isinstance(result, Syntax)


def test_format_body_invalid_xml_falls_through() -> None:
    event = _make_event()
    inspector = NetworkInspector(event)
    result = inspector._format_body("<broken xml")
    from rich.text import Text

    assert isinstance(result, Text)


def test_format_body_plain_text() -> None:
    event = _make_event()
    inspector = NetworkInspector(event)
    result = inspector._format_body("just some text")
    from rich.text import Text

    assert isinstance(result, Text)
