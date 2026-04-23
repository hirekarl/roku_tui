from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Connection

from ..schema import network_requests

if TYPE_CHECKING:
    from ...ecp.models import NetworkEvent


def insert_network_request(
    conn: Connection,
    event: NetworkEvent,
    device_id: int | None,
) -> None:
    """Log an ECP HTTP request.

    Args:
        conn: SQLAlchemy connection.
        event: The network event data.
        device_id: Optional target device ID.
    """
    conn.execute(
        network_requests.insert().values(
            method=event.method,
            url=event.url,
            status_code=event.status_code,
            response_time_ms=event.response_time_ms,
            body=event.body[:4096] if event.body else "",
            error=event.error,
            requested_at=event.timestamp,
            device_id=device_id,
        )
    )
    conn.commit()
