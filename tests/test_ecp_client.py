from __future__ import annotations

import httpx
import respx

from roku_tui.ecp.client import EcpClient, _parse_apps, _parse_device_info
from roku_tui.ecp.models import NetworkEvent

BASE = "http://192.168.1.50:8060"

APPS_XML = """\
<apps>
  <app id="2285" subtype="ndka" type="appl" version="4.1.218">Netflix</app>
  <app id="13" subtype="ndka" type="appl" version="3.0">Prime Video</app>
</apps>"""

ACTIVE_APP_XML = """\
<active-app>
  <app id="2285" subtype="ndka" version="4.1.218">Netflix</app>
</active-app>"""

DEVICE_XML = """\
<device-info>
  <user-device-name>Living Room Roku</user-device-name>
  <model-name>Express 4K+</model-name>
  <serial-number>X12345</serial-number>
  <software-version>11.5.0</software-version>
  <ethernet-mac>00:11:22:33:44:55</ethernet-mac>
  <wifi-mac>00:11:22:33:44:56</wifi-mac>
</device-info>"""


# ── _parse_apps ───────────────────────────────────────────────────────────────


def test_parse_apps_from_apps_tag() -> None:
    apps = _parse_apps(APPS_XML)
    assert len(apps) == 2
    assert apps[0].name == "Netflix"
    assert apps[0].id == "2285"


def test_parse_apps_from_active_app_tag() -> None:
    apps = _parse_apps(ACTIVE_APP_XML)
    assert len(apps) == 1
    assert apps[0].name == "Netflix"


def test_parse_apps_invalid_xml_returns_empty() -> None:
    apps = _parse_apps("not xml")
    assert apps == []


def test_parse_apps_empty_xml() -> None:
    apps = _parse_apps("<apps></apps>")
    assert apps == []


# ── _parse_device_info ────────────────────────────────────────────────────────


def test_parse_device_info() -> None:
    info = _parse_device_info(DEVICE_XML)
    assert info.friendly_name == "Living Room Roku"
    assert info.model_name == "Express 4K+"
    assert info.serial_number == "X12345"
    assert info.ethernet_mac == "00:11:22:33:44:55"
    assert info.wifi_mac == "00:11:22:33:44:56"


def test_parse_device_info_fallback_friendly_name() -> None:
    xml = """\
<device-info>
  <friendly-device-name>My Roku</friendly-device-name>
  <model-name>Model X</model-name>
  <serial-number>SN001</serial-number>
  <software-version>10.0</software-version>
  <ethernet-mac></ethernet-mac>
  <wifi-mac></wifi-mac>
</device-info>"""
    info = _parse_device_info(xml)
    assert info.friendly_name == "My Roku"


# ── EcpClient with respx ──────────────────────────────────────────────────────


@respx.mock
async def test_keypress_fires_network_event() -> None:
    respx.post(f"{BASE}/keypress/Home").mock(return_value=httpx.Response(200))
    events: list[NetworkEvent] = []
    client = EcpClient(BASE, on_network_event=events.append)
    await client.keypress("Home")
    assert len(events) == 1
    assert events[0].method == "POST"
    assert "keypress/Home" in events[0].url
    await client.close()


@respx.mock
async def test_keypress_without_callback() -> None:
    respx.post(f"{BASE}/keypress/Select").mock(return_value=httpx.Response(200))
    client = EcpClient(BASE)
    await client.keypress("Select")
    await client.close()


@respx.mock
async def test_launch_with_params() -> None:
    respx.post(f"{BASE}/launch/2285").mock(return_value=httpx.Response(200))
    events: list[NetworkEvent] = []
    client = EcpClient(BASE, on_network_event=events.append)
    await client.launch("2285", params={"contentId": "tt123"})
    assert len(events) == 1
    assert "contentId=tt123" in events[0].url
    await client.close()


@respx.mock
async def test_query_apps_parses_xml() -> None:
    respx.get(f"{BASE}/query/apps").mock(
        return_value=httpx.Response(200, text=APPS_XML)
    )
    client = EcpClient(BASE)
    apps = await client.query_apps()
    assert len(apps) == 2
    assert apps[0].name == "Netflix"
    await client.close()


@respx.mock
async def test_query_apps_returns_empty_on_error() -> None:
    respx.get(f"{BASE}/query/apps").mock(return_value=httpx.Response(500))
    events: list[NetworkEvent] = []
    client = EcpClient(BASE, on_network_event=events.append)
    apps = await client.query_apps()
    assert apps == []
    assert len(events) == 1
    assert events[0].error is not None
    await client.close()


@respx.mock
async def test_query_active_app() -> None:
    respx.get(f"{BASE}/query/active-app").mock(
        return_value=httpx.Response(200, text=ACTIVE_APP_XML)
    )
    client = EcpClient(BASE)
    app = await client.query_active_app()
    assert app is not None
    assert app.name == "Netflix"
    await client.close()


@respx.mock
async def test_query_active_app_no_response() -> None:
    respx.get(f"{BASE}/query/active-app").mock(return_value=httpx.Response(500))
    events: list[NetworkEvent] = []
    client = EcpClient(BASE, on_network_event=events.append)
    app = await client.query_active_app()
    assert app is None
    await client.close()


@respx.mock
async def test_query_active_app_empty_xml() -> None:
    respx.get(f"{BASE}/query/active-app").mock(
        return_value=httpx.Response(200, text="<active-app></active-app>")
    )
    client = EcpClient(BASE)
    app = await client.query_active_app()
    assert app is None
    await client.close()


@respx.mock
async def test_query_active_app_connection_error() -> None:
    respx.get(f"{BASE}/query/active-app").mock(
        side_effect=httpx.ConnectError("timeout")
    )
    client = EcpClient(BASE)
    app = await client.query_active_app()
    assert app is None
    await client.close()


@respx.mock
async def test_query_device_info() -> None:
    respx.get(f"{BASE}/query/device-info").mock(
        return_value=httpx.Response(200, text=DEVICE_XML)
    )
    client = EcpClient(BASE)
    info = await client.query_device_info()
    assert info is not None
    assert info.model_name == "Express 4K+"
    await client.close()


@respx.mock
async def test_request_records_error_in_event() -> None:
    respx.post(f"{BASE}/keypress/Up").mock(side_effect=httpx.ConnectError("timeout"))
    events: list[NetworkEvent] = []
    client = EcpClient(BASE, on_network_event=events.append)
    await client.keypress("Up")
    assert len(events) == 1
    assert events[0].error is not None
    assert events[0].status_code is None
    await client.close()
