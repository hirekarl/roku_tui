from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NetworkEvent:
    method: str
    url: str
    request_headers: dict[str, str]
    status_code: int | None = None
    response_headers: dict[str, str] = field(default_factory=dict)
    response_time_ms: float | None = None
    body: str = ""
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AppInfo:
    id: str
    name: str
    version: str
    subtype: str


@dataclass
class DeviceInfo:
    friendly_name: str
    model_name: str
    serial_number: str
    software_version: str
    ethernet_mac: str
    wifi_mac: str
