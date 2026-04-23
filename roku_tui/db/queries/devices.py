from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Connection, Row, select, update

from ..schema import devices

if TYPE_CHECKING:
    from ...ecp.models import DeviceInfo


def upsert_device(conn: Connection, ip: str, info: DeviceInfo) -> int:
    """Insert or update a Roku device in the history.

    Args:
        conn: SQLAlchemy connection.
        ip: IP address of the device.
        info: Device information from ECP.

    Returns:
        The database ID of the device.
    """
    now = datetime.now(UTC)
    conn.execute(
        devices.insert()
        .prefix_with("OR IGNORE")
        .values(
            ip=ip,
            friendly_name=info.friendly_name,
            model_name=info.model_name,
            serial_number=info.serial_number,
            last_connected_at=now,
            connect_count=0,
        )
    )
    conn.execute(
        update(devices)
        .where(devices.c.ip == ip)
        .values(
            friendly_name=info.friendly_name,
            model_name=info.model_name,
            serial_number=info.serial_number,
            last_connected_at=now,
            connect_count=devices.c.connect_count + 1,
        )
    )
    conn.commit()
    row = conn.execute(select(devices.c.id).where(devices.c.ip == ip)).one()
    return int(row.id)


def get_device_id(conn: Connection, ip: str) -> int | None:
    """Get the database ID for a device IP.

    Args:
        conn: SQLAlchemy connection.
        ip: IP address of the device.

    Returns:
        The database ID or None if not found.
    """
    row = conn.execute(select(devices.c.id).where(devices.c.ip == ip)).one_or_none()
    return int(row.id) if row else None


def select_all_devices(conn: Connection) -> list[Row[Any]]:
    """Select all registered devices ordered by last connected date.

    Args:
        conn: SQLAlchemy connection.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(
            select(
                devices.c.ip,
                devices.c.friendly_name,
                devices.c.model_name,
                devices.c.last_connected_at,
                devices.c.connect_count,
            ).order_by(devices.c.last_connected_at.desc())
        ).fetchall()
    )
