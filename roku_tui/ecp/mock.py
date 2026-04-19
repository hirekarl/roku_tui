import asyncio
import random
from datetime import datetime
from typing import Callable

from .models import AppInfo, DeviceInfo, NetworkEvent

MOCK_APPS = [
    AppInfo("tvinput.hdmi1", "HDMI 1", "1.0.0", "ndka"),
    AppInfo("2285", "Netflix", "4.1.218", "ndka"),
    AppInfo("13", "Amazon Video", "4.1.218", "ndka"),
    AppInfo("2156", "The Roku Channel", "6.1.218", "ndka"),
    AppInfo("34399", "Disney+", "1.22.0", "ndka"),
    AppInfo("tvinput.hdmi2", "HDMI 2", "1.0.0", "ndka"),
    AppInfo("12", "Crackle", "3.1.0", "ndka"),
    AppInfo("26950", "Peacock TV", "4.0.0", "ndka"),
    AppInfo("2595", "Paramount+", "4.0.0", "ndka"),
]

MOCK_DEVICE = DeviceInfo(
    friendly_name="My Roku TV (Mock)",
    model_name="Roku Express 4K+",
    serial_number="X12000AB1234",
    software_version="11.5.0 build 4981",
    ethernet_mac="00:0d:4b:00:ab:cd",
    wifi_mac="00:0d:4b:00:ab:ce",
)

_APPS_XML = "\n".join(
    f'  <app id="{a.id}" subtype="{a.subtype}" type="appl" version="{a.version}">{a.name}</app>'
    for a in MOCK_APPS
)
MOCK_APPS_XML = f"<apps>\n{_APPS_XML}\n</apps>"

MOCK_DEVICE_XML = f"""<device-info>
  <friendly-device-name>{MOCK_DEVICE.friendly_name}</friendly-device-name>
  <model-name>{MOCK_DEVICE.model_name}</model-name>
  <serial-number>{MOCK_DEVICE.serial_number}</serial-number>
  <software-version>{MOCK_DEVICE.software_version}</software-version>
  <ethernet-mac>{MOCK_DEVICE.ethernet_mac}</ethernet-mac>
  <wifi-mac>{MOCK_DEVICE.wifi_mac}</wifi-mac>
</device-info>"""


class MockEcpClient:
    def __init__(self, on_network_event: Callable[[NetworkEvent], None]):
        self._callback = on_network_event
        self._base = "http://mock-roku:8060"

    async def keypress(self, key: str) -> None:
        await self._fake_request("POST", f"/keypress/{key}", body="")

    async def query_apps(self) -> list[AppInfo]:
        await self._fake_request("GET", "/query/apps", body=MOCK_APPS_XML)
        return list(MOCK_APPS)

    async def query_active_app(self) -> AppInfo | None:
        app = MOCK_APPS[1]  # Netflix
        xml = f'<active-app><app id="{app.id}" subtype="{app.subtype}" version="{app.version}">{app.name}</app></active-app>'
        await self._fake_request("GET", "/query/active-app", body=xml)
        return app

    async def query_device_info(self) -> DeviceInfo:
        await self._fake_request("GET", "/query/device-info", body=MOCK_DEVICE_XML)
        return MOCK_DEVICE

    async def close(self) -> None:
        pass

    async def _fake_request(self, method: str, path: str, body: str) -> None:
        delay_ms = random.uniform(30, 120)
        await asyncio.sleep(delay_ms / 1000)
        self._callback(
            NetworkEvent(
                method=method,
                url=f"{self._base}{path}",
                request_headers={"Host": "mock-roku:8060", "Content-Length": "0"},
                status_code=200,
                response_headers={"Content-Type": "text/xml; charset=utf-8"},
                response_time_ms=delay_ms,
                body=body,
                timestamp=datetime.now(),
            )
        )
