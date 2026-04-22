from __future__ import annotations

from pathlib import Path

import pytest

from roku_tui.service import RokuService


@pytest.fixture
def service(tmp_path: Path) -> RokuService:
    db_path = tmp_path / "test_headless.db"
    service = RokuService(mock=True, db_path=db_path)
    return service


@pytest.mark.asyncio
async def test_service_initialization(service: RokuService) -> None:
    assert service.mock is True
    assert service.client is not None
    assert service.db is not None
    assert service.registry is not None


@pytest.mark.asyncio
async def test_service_dispatch_known_command(service: RokuService) -> None:
    result = await service.dispatch("version")
    assert result is True


@pytest.mark.asyncio
async def test_service_dispatch_unknown_command(service: RokuService) -> None:
    result = await service.dispatch("nonexistent_command_123")
    assert result is False


@pytest.mark.asyncio
async def test_service_dispatch_chained_commands(service: RokuService) -> None:
    result = await service.dispatch("home; up 2; down")
    assert result is True


@pytest.mark.asyncio
async def test_service_dispatch_chained_failure_continues(service: RokuService) -> None:
    # First and last are valid, middle is invalid.
    # We want to ensure it tries all of them if that's our policy.
    # In my implementation of dispatch:
    # for part in ...: if not await self._dispatch_single(part): success = False
    result = await service.dispatch("home; bad_cmd; up")
    assert result is False  # Because one failed


@pytest.mark.asyncio
async def test_service_output_callback(tmp_path: Path) -> None:
    output_log = []

    def callback(content: str) -> None:
        output_log.append(content)

    db_path = tmp_path / "test_callback.db"
    service = RokuService(mock=True, db_path=db_path, output_callback=callback)

    await service.dispatch("version")
    assert len(output_log) > 0
    assert any("v" in str(line) for line in output_log)


@pytest.mark.asyncio
async def test_service_disconnected_ecp_command(tmp_path: Path) -> None:
    db_path = tmp_path / "test_disconnected.db"
    service = RokuService(mock=False, db_path=db_path)
    # No connect() called, so client is None
    result = await service.dispatch("up")
    assert result is False
