from __future__ import annotations

import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from roku_tui.__main__ import main, run_headless

# ── run_headless ──────────────────────────────────────────────────────────────


async def test_run_headless_mock_mode() -> None:
    with patch("roku_tui.__main__.RokuService") as MockService:
        instance = MockService.return_value
        instance.dispatch = AsyncMock(return_value=True)
        instance.close = AsyncMock()

        await run_headless("home", mock=True)

        MockService.assert_called_once_with(mock=True)
        instance.dispatch.assert_called_once_with("home")
        instance.close.assert_called_once()


async def test_run_headless_with_explicit_ip() -> None:
    with patch("roku_tui.__main__.RokuService") as MockService:
        instance = MockService.return_value
        instance.connect = AsyncMock()
        instance.dispatch = AsyncMock(return_value=True)
        instance.close = AsyncMock()

        await run_headless("home", ip="192.168.1.50", mock=False)

        instance.connect.assert_called_once_with("192.168.1.50")
        instance.dispatch.assert_called_once_with("home")
        instance.close.assert_called_once()


async def test_run_headless_discovers_device() -> None:
    with patch("roku_tui.__main__.RokuService") as MockService:
        instance = MockService.return_value
        instance.discover = AsyncMock(return_value="192.168.1.60")
        instance.connect = AsyncMock()
        instance.dispatch = AsyncMock(return_value=True)
        instance.close = AsyncMock()

        await run_headless("home", ip=None, mock=False)

        instance.discover.assert_called_once()
        instance.connect.assert_called_once_with("192.168.1.60")


async def test_run_headless_no_device_exits() -> None:
    with patch("roku_tui.__main__.RokuService") as MockService:
        instance = MockService.return_value
        instance.discover = AsyncMock(return_value=None)
        instance.close = AsyncMock()

        with pytest.raises(SystemExit):
            await run_headless("home", ip=None, mock=False)


async def test_run_headless_close_called_on_error() -> None:
    with patch("roku_tui.__main__.RokuService") as MockService:
        instance = MockService.return_value
        instance.dispatch = AsyncMock(side_effect=RuntimeError("fail"))
        instance.close = AsyncMock()

        with pytest.raises(RuntimeError):
            await run_headless("home", mock=True)

        instance.close.assert_called_once()


# ── main ──────────────────────────────────────────────────────────────────────


def test_main_with_command_calls_asyncio_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["roku-tui", "-c", "home"])

    with patch("roku_tui.__main__.asyncio") as mock_asyncio:
        main()
        mock_asyncio.run.assert_called_once()


def test_main_with_mock_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["roku-tui", "--mock", "-c", "home"])

    with patch("roku_tui.__main__.asyncio") as mock_asyncio:
        main()
        mock_asyncio.run.assert_called_once()


def test_main_without_command_runs_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["roku-tui"])

    with patch("roku_tui.__main__.RokuTuiApp") as MockApp:
        instance = MockApp.return_value
        instance.run = Mock()
        main()
        instance.run.assert_called_once()


def test_main_keyboard_interrupt_suppressed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["roku-tui", "-c", "home"])

    with patch("roku_tui.__main__.asyncio") as mock_asyncio:
        mock_asyncio.run.side_effect = KeyboardInterrupt
        main()  # Should not raise


def test_main_exception_calls_sys_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["roku-tui", "-c", "home"])

    with patch("roku_tui.__main__.asyncio") as mock_asyncio:
        mock_asyncio.run.side_effect = RuntimeError("network error")
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


def test_main_with_ip_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["roku-tui", "--ip", "10.0.0.5"])

    with patch("roku_tui.__main__.RokuTuiApp") as MockApp:
        instance = MockApp.return_value
        instance.run = Mock()
        main()
        MockApp.assert_called_once_with(mock=False, initial_ip="10.0.0.5")
