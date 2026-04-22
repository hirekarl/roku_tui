from __future__ import annotations

import time
from collections.abc import Callable
from xml.etree import ElementTree as ET

import httpx

from .models import AppInfo, DeviceInfo, NetworkEvent


class EcpClient:
    """Async HTTP client for the Roku External Control Protocol (ECP)."""

    def __init__(
        self,
        base_url: str,
        on_network_event: Callable[[NetworkEvent], None] | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            base_url: The base URL of the Roku device (e.g., http://192.168.1.42:8060).
            on_network_event: Optional callback for logging HTTP traffic.
        """
        self._base = base_url.rstrip("/")
        self.on_network_event = on_network_event
        self._http = httpx.AsyncClient(timeout=5.0)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def _request(
        self, method: str, path: str, body: str = ""
    ) -> httpx.Response | None:
        """Send an HTTP request and fire the network callback."""
        url = f"{self._base}{path}"
        start = time.perf_counter()
        resp: httpx.Response | None = None
        error: str | None = None

        try:
            resp = await self._http.request(method, url, content=body)
            resp.raise_for_status()
        except Exception as e:
            error = str(e)

        duration = (time.perf_counter() - start) * 1000

        if self.on_network_event:
            event = NetworkEvent(
                method=method,
                url=url,
                request_headers=dict(self._http.headers),
                status_code=resp.status_code if resp else None,
                response_headers=dict(resp.headers) if resp else {},
                response_time_ms=duration,
                body=resp.text if resp else "",
                error=error,
            )
            self.on_network_event(event)

        return resp

    async def keypress(self, key: str) -> None:
        """Send a keypress event to the Roku device.

        Args:
            key: The ECP key name (e.g., 'Home', 'Play').
        """
        await self._request("POST", f"/keypress/{key}")

    async def launch(self, app_id: str, params: dict[str, str] | None = None) -> None:
        """Launch an app, optionally with deep link parameters.

        Args:
            app_id: The Roku application ID.
            params: Optional query parameters for deep linking.
        """
        path = f"/launch/{app_id}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            path = f"{path}?{query}"
        await self._request("POST", path)

    async def query_apps(self) -> list[AppInfo]:
        """Fetch the list of installed apps from the device."""
        resp = await self._request("GET", "/query/apps")
        return _parse_apps(resp.text) if resp else []

    async def query_active_app(self) -> AppInfo | None:
        """Get information about the currently running app."""
        resp = await self._request("GET", "/query/active-app")
        if not resp:
            return None
        apps = _parse_apps(resp.text)
        return apps[0] if apps else None

    async def query_device_info(self) -> DeviceInfo | None:
        """Get hardware and software details about the Roku device."""
        resp = await self._request("GET", "/query/device-info")
        return _parse_device_info(resp.text) if resp else None


def _parse_apps(xml_str: str) -> list[AppInfo]:
    """Parse the ECP /query/apps XML response."""
    try:
        root = ET.fromstring(xml_str)
        apps_to_parse = (
            root.findall("app") if root.tag == "apps" else [root.find("app")]
        )
        return [
            AppInfo(
                id=el.get("id", ""),
                name=el.text or "Unknown",
                version=el.get("version", ""),
                subtype=el.get("subtype", ""),
            )
            for el in apps_to_parse
            if el is not None
        ]
    except Exception:
        return []


def _parse_device_info(xml_str: str) -> DeviceInfo:
    """Parse the ECP /query/device-info XML response."""
    root = ET.fromstring(xml_str)

    def get(tag: str) -> str:
        el = root.find(tag)
        return el.text if el is not None and el.text else ""

    return DeviceInfo(
        friendly_name=get("user-device-name") or get("friendly-device-name"),
        model_name=get("model-name"),
        serial_number=get("serial-number"),
        software_version=get("software-version"),
        ethernet_mac=get("ethernet-mac"),
        wifi_mac=get("wifi-mac"),
    )
