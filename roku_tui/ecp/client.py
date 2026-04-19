import time
from datetime import datetime
from typing import Callable
from xml.etree import ElementTree as ET

import httpx

from .models import AppInfo, DeviceInfo, NetworkEvent


class EcpClient:
    def __init__(self, base_url: str, on_network_event: Callable[[NetworkEvent], None]):
        self._base = base_url.rstrip("/")
        self._callback = on_network_event
        self._http = httpx.AsyncClient(timeout=5.0)

    async def keypress(self, key: str) -> None:
        await self._request("POST", f"/keypress/{key}")

    async def query_apps(self) -> list[AppInfo]:
        resp = await self._request("GET", "/query/apps")
        return _parse_apps(resp.text) if resp else []

    async def query_active_app(self) -> AppInfo | None:
        resp = await self._request("GET", "/query/active-app")
        if not resp:
            return None
        root = ET.fromstring(resp.text)
        app_el = root.find("app")
        if app_el is None:
            return None
        return AppInfo(
            id=app_el.get("id", ""),
            name=app_el.text or "",
            version=app_el.get("version", ""),
            subtype=app_el.get("subtype", ""),
        )

    async def query_device_info(self) -> DeviceInfo | None:
        resp = await self._request("GET", "/query/device-info")
        if not resp:
            return None
        return _parse_device_info(resp.text)

    async def close(self) -> None:
        await self._http.aclose()

    async def _request(self, method: str, path: str) -> httpx.Response | None:
        url = f"{self._base}{path}"
        t0 = time.perf_counter()
        event = NetworkEvent(
            method=method,
            url=url,
            request_headers={"Host": self._base.split("://")[-1], "Content-Length": "0"},
        )
        try:
            resp = await self._http.request(method, url)
            event.status_code = resp.status_code
            event.response_time_ms = (time.perf_counter() - t0) * 1000
            event.body = resp.text
            event.response_headers = dict(resp.headers)
            self._callback(event)
            return resp
        except httpx.RequestError as e:
            event.error = str(e)
            event.response_time_ms = (time.perf_counter() - t0) * 1000
            self._callback(event)
            return None


def _parse_apps(xml: str) -> list[AppInfo]:
    root = ET.fromstring(xml)
    return [
        AppInfo(
            id=el.get("id", ""),
            name=el.text or "",
            version=el.get("version", ""),
            subtype=el.get("subtype", ""),
        )
        for el in root.findall("app")
    ]


def _parse_device_info(xml: str) -> DeviceInfo:
    root = ET.fromstring(xml)

    def get(tag: str) -> str:
        el = root.find(tag)
        return el.text or "" if el is not None else ""

    return DeviceInfo(
        friendly_name=get("friendly-device-name"),
        model_name=get("model-name"),
        serial_number=get("serial-number"),
        software_version=get("software-version"),
        ethernet_mac=get("ethernet-mac"),
        wifi_mac=get("wifi-mac"),
    )
