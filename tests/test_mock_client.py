from __future__ import annotations

from roku_tui.ecp.mock import MOCK_APPS, MOCK_DEVICE, MockEcpClient
from roku_tui.ecp.models import NetworkEvent


def _make_client() -> tuple[MockEcpClient, list[NetworkEvent]]:
    events: list[NetworkEvent] = []
    return MockEcpClient(on_network_event=events.append), events


async def test_keypress_fires_post_callback() -> None:
    client, events = _make_client()
    await client.keypress("Home")
    assert len(events) == 1
    ev = events[0]
    assert isinstance(ev, NetworkEvent)
    assert ev.method == "POST"
    assert "/keypress/Home" in ev.url
    assert ev.status_code == 200


async def test_keypress_response_time_set() -> None:
    client, events = _make_client()
    await client.keypress("Select")
    assert events[0].response_time_ms is not None
    assert events[0].response_time_ms > 0


async def test_query_apps_returns_mock_list() -> None:
    client, _events = _make_client()
    apps = await client.query_apps()
    assert apps == list(MOCK_APPS)


async def test_query_apps_fires_get_callback() -> None:
    client, events = _make_client()
    await client.query_apps()
    assert len(events) == 1
    assert events[0].method == "GET"
    assert "/query/apps" in events[0].url
    assert events[0].body != ""


async def test_query_device_info_returns_mock_device() -> None:
    client, _events = _make_client()
    info = await client.query_device_info()
    assert info == MOCK_DEVICE


async def test_query_device_info_fires_callback() -> None:
    client, events = _make_client()
    await client.query_device_info()
    assert len(events) == 1
    assert "/query/device-info" in events[0].url


async def test_query_active_app_returns_netflix() -> None:
    client, _events = _make_client()
    app = await client.query_active_app()
    assert app is not None
    assert app.name == "Netflix"


async def test_query_active_app_fires_callback() -> None:
    client, events = _make_client()
    await client.query_active_app()
    assert len(events) == 1
    assert "/query/active-app" in events[0].url


async def test_launch_fires_post_callback() -> None:
    client, events = _make_client()
    await client.launch("2285")
    assert len(events) == 1
    ev = events[0]
    assert ev.method == "POST"
    assert "/launch/2285" in ev.url


async def test_multiple_calls_fire_separate_events() -> None:
    client, events = _make_client()
    await client.keypress("Up")
    await client.keypress("Down")
    await client.keypress("Select")
    assert len(events) == 3
