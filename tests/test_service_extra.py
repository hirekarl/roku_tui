from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from roku_tui.service import RokuService


@pytest.fixture
def svc(tmp_path: Path) -> RokuService:
    return RokuService(mock=True, db_path=tmp_path / "test.db")


@pytest.fixture
def disconnected_svc(tmp_path: Path) -> RokuService:
    return RokuService(mock=False, db_path=tmp_path / "test.db")


# ── connect ───────────────────────────────────────────────────────────────────


async def test_connect_creates_client(tmp_path: Path) -> None:
    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    with patch("roku_tui.service.EcpClient") as MockClient:
        instance = MockClient.return_value
        instance.query_apps = AsyncMock(return_value=[])
        instance.query_device_info = AsyncMock(return_value=None)
        await svc.connect("192.168.1.50")
    assert svc.client is instance
    assert svc._current_ip == "192.168.1.50"


async def test_connect_with_full_url(tmp_path: Path) -> None:
    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    with patch("roku_tui.service.EcpClient") as MockClient:
        instance = MockClient.return_value
        instance.query_apps = AsyncMock(return_value=[])
        instance.query_device_info = AsyncMock(return_value=None)
        await svc.connect("http://192.168.1.50:8060")
    assert svc._current_ip == "192.168.1.50"


async def test_connect_prefetches_apps(tmp_path: Path) -> None:
    from roku_tui.ecp.models import AppInfo

    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    apps = [AppInfo("2285", "Netflix", "4.0", "ndka")]
    with patch("roku_tui.service.EcpClient") as MockClient:
        instance = MockClient.return_value
        instance.query_apps = AsyncMock(return_value=apps)
        instance.query_device_info = AsyncMock(return_value=None)
        await svc.connect("192.168.1.50")
    assert svc.app_cache == apps


async def test_connect_saves_device_info(tmp_path: Path) -> None:
    from roku_tui.ecp.models import AppInfo, DeviceInfo

    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    apps = [AppInfo("2285", "Netflix", "4.0", "ndka")]
    info = DeviceInfo(
        friendly_name="My Roku",
        model_name="Express",
        serial_number="SN1",
        software_version="11.0",
        ethernet_mac="",
        wifi_mac="",
    )
    with patch("roku_tui.service.EcpClient") as MockClient:
        instance = MockClient.return_value
        instance.query_apps = AsyncMock(return_value=apps)
        instance.query_device_info = AsyncMock(return_value=info)
        await svc.connect("192.168.1.50")
    dev_id = svc.db.get_device_id("192.168.1.50")
    assert dev_id is not None


async def test_connect_url_without_port(tmp_path: Path) -> None:
    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    with patch("roku_tui.service.EcpClient") as MockClient:
        instance = MockClient.return_value
        instance.query_apps = AsyncMock(return_value=[])
        instance.query_device_info = AsyncMock(return_value=None)
        await svc.connect("http://192.168.1.50")
    assert svc._current_ip == "192.168.1.50"


async def test_connect_handles_prefetch_exception(tmp_path: Path) -> None:
    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    with patch("roku_tui.service.EcpClient") as MockClient:
        instance = MockClient.return_value
        instance.query_apps = AsyncMock(side_effect=RuntimeError("network error"))
        await svc.connect("192.168.1.50")
    assert svc.client is not None


# ── discover ──────────────────────────────────────────────────────────────────


async def test_discover_uses_known_device(tmp_path: Path) -> None:
    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    svc.db.known_device_ips = Mock(return_value=["192.168.1.50"])

    with patch("roku_tui.service.probe_roku", return_value=True):
        ip = await svc.discover()

    assert ip == "192.168.1.50"


async def test_discover_falls_back_to_ssdp(tmp_path: Path) -> None:
    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    svc.db.known_device_ips = Mock(return_value=[])

    with patch(
        "roku_tui.service.discover_rokus", return_value=["http://10.0.0.1:8060"]
    ):
        ip = await svc.discover()

    assert ip == "10.0.0.1"


async def test_discover_returns_none_when_nothing_found(tmp_path: Path) -> None:
    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    svc.db.known_device_ips = Mock(return_value=[])

    with patch("roku_tui.service.discover_rokus", return_value=[]):
        ip = await svc.discover()

    assert ip is None


async def test_discover_skips_unreachable_known_device(tmp_path: Path) -> None:
    svc = RokuService(mock=False, db_path=tmp_path / "test.db")
    svc.db.known_device_ips = Mock(return_value=["192.168.1.50"])

    with (
        patch("roku_tui.service.probe_roku", return_value=False),
        patch("roku_tui.service.discover_rokus", return_value=["http://10.0.0.2:8060"]),
    ):
        ip = await svc.discover()

    assert ip == "10.0.0.2"


# ── recording ─────────────────────────────────────────────────────────────────


def test_start_and_stop_recording(svc: RokuService) -> None:
    svc.start_recording()
    assert svc._recording == []
    lines = svc.stop_recording()
    assert lines == []
    assert svc._recording is None


def test_stop_recording_without_start_returns_none(svc: RokuService) -> None:
    assert svc.stop_recording() is None


async def test_recording_captures_commands(svc: RokuService) -> None:
    svc.start_recording()
    await svc.dispatch("home")
    await svc.dispatch("up 2")
    lines = svc.stop_recording()
    assert lines is not None
    assert "home" in lines
    assert "up 2" in lines


# ── action stubs ──────────────────────────────────────────────────────────────


def test_action_show_about(svc: RokuService) -> None:
    svc.action_show_about()  # Should not raise


def test_action_show_manual(svc: RokuService) -> None:
    svc.action_show_manual()  # Should not raise


def test_action_show_tour(svc: RokuService) -> None:
    svc.action_show_tour()  # Should not raise


def test_action_clear_console(svc: RokuService) -> None:
    svc.action_clear_console()  # Should not raise


def test_toggle_keyboard_mode(svc: RokuService) -> None:
    svc.toggle_keyboard_mode()  # Should not raise


# ── dispatch error handling ───────────────────────────────────────────────────


async def test_dispatch_command_raises_outputs_error(tmp_path: Path) -> None:
    output_log: list[str] = []
    svc = RokuService(
        mock=True, db_path=tmp_path / "test.db", output_callback=output_log.append
    )

    original_handler = svc.registry.lookup("home")
    assert original_handler is not None

    async def exploding_handler(*args, **kwargs):  # type: ignore
        raise RuntimeError("boom")

    original_handler.handler = exploding_handler

    result = await svc.dispatch("home")
    assert result is False
    assert any("Error" in str(m) for m in output_log)


# ── on_network_event / _current_device_id ────────────────────────────────────


def test_on_network_event_logs_to_db(svc: RokuService) -> None:
    from roku_tui.ecp.models import NetworkEvent

    event = NetworkEvent(
        method="GET",
        url="http://mock-roku:8060/query/apps",
        request_headers={},
        status_code=200,
        response_headers={},
        response_time_ms=10.0,
        body="<apps/>",
        error=None,
    )
    svc._on_network_event(event)  # Should not raise


def test_current_device_id_handles_db_exception(svc: RokuService) -> None:
    svc.db.get_device_id = Mock(side_effect=RuntimeError("db error"))
    result = svc._current_device_id()
    assert result is None


# ── output ────────────────────────────────────────────────────────────────────


def test_output_without_callback(tmp_path: Path) -> None:
    svc = RokuService(mock=True, db_path=tmp_path / "test.db")
    svc._output("test message")  # Should not raise (falls back to Console)


# ── close ─────────────────────────────────────────────────────────────────────


async def test_close(svc: RokuService) -> None:
    await svc.close()  # Should not raise


async def test_close_without_client(disconnected_svc: RokuService) -> None:
    await disconnected_svc.close()  # Should not raise
