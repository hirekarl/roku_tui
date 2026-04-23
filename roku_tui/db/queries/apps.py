from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Connection, Row, func, select, update

from ..schema import app_launches, deep_links, device_apps

if TYPE_CHECKING:
    from ...ecp.models import AppInfo


def insert_app_launch(
    conn: Connection,
    app_id: str,
    app_name: str,
    launched_at: datetime,
    device_id: int | None,
) -> None:
    """Log an app launch event.

    Args:
        conn: SQLAlchemy connection.
        app_id: Roku app ID.
        app_name: Display name.
        launched_at: Timestamp.
        device_id: Target device.
    """
    conn.execute(
        app_launches.insert().values(
            app_id=app_id,
            app_name=app_name,
            launched_at=launched_at,
            device_id=device_id,
        )
    )
    conn.commit()


def select_top_app_launches(conn: Connection, limit: int = 10) -> list[Row[Any]]:
    """Select apps ordered by launch frequency.

    Args:
        conn: SQLAlchemy connection.
        limit: Max results.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(
            select(
                app_launches.c.app_id,
                app_launches.c.app_name,
                func.count().label("count"),
            )
            .group_by(app_launches.c.app_id)
            .order_by(func.count().desc())
            .limit(limit)
        ).fetchall()
    )


def select_app_launch_frequencies(conn: Connection) -> list[Row[Any]]:
    """Select total launch counts for all apps.

    Args:
        conn: SQLAlchemy connection.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(
            select(
                app_launches.c.app_name,
                func.count().label("count"),
            )
            .group_by(app_launches.c.app_name)
            .order_by(func.count().desc())
        ).fetchall()
    )


def sync_device_apps(conn: Connection, device_id: int, apps: list[AppInfo]) -> None:
    """Replace all cached app rows for a device.

    Args:
        conn: SQLAlchemy connection.
        device_id: Target device.
        apps: Current list of apps from ECP.
    """
    now = datetime.now(UTC)
    conn.execute(device_apps.delete().where(device_apps.c.device_id == device_id))
    if apps:
        conn.execute(
            device_apps.insert(),
            [
                {
                    "device_id": device_id,
                    "app_id": a.id,
                    "app_name": a.name,
                    "version": a.version,
                    "subtype": a.subtype,
                    "last_seen_at": now,
                }
                for a in apps
            ],
        )
    conn.commit()


def select_apps_for_device(conn: Connection, device_id: int) -> list[Row[Any]]:
    """Select cached apps for a specific device.

    Args:
        conn: SQLAlchemy connection.
        device_id: Target device ID.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(
            select(device_apps)
            .where(device_apps.c.device_id == device_id)
            .order_by(device_apps.c.app_name)
        ).fetchall()
    )


def upsert_deep_link(
    conn: Connection,
    alias: str,
    app_id: str,
    app_name: str | None,
    content_id: str,
    media_type: str | None,
) -> None:
    """Create or update a deep link shortcut.

    Args:
        conn: SQLAlchemy connection.
        alias: Unique command alias.
        app_id: Roku app ID.
        app_name: App display name.
        content_id: Content ID for deep linking.
        media_type: Optional media type.
    """
    now = datetime.now(UTC)
    existing = conn.execute(
        select(deep_links).where(deep_links.c.alias == alias)
    ).one_or_none()

    if existing:
        conn.execute(
            update(deep_links)
            .where(deep_links.c.alias == alias)
            .values(
                app_id=app_id,
                app_name=app_name,
                content_id=content_id,
                media_type=media_type,
            )
        )
    else:
        conn.execute(
            deep_links.insert().values(
                alias=alias,
                app_id=app_id,
                app_name=app_name,
                content_id=content_id,
                media_type=media_type,
                created_at=now,
            )
        )
    conn.commit()


def select_all_deep_links(conn: Connection) -> list[Row[Any]]:
    """Select all content shortcuts.

    Args:
        conn: SQLAlchemy connection.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(select(deep_links).order_by(deep_links.c.alias)).fetchall()
    )


def select_deep_link_by_alias(conn: Connection, alias: str) -> Row[Any] | None:
    """Find a content shortcut by alias.

    Args:
        conn: SQLAlchemy connection.
        alias: Unique command alias.

    Returns:
        The SQLAlchemy Row or None.
    """
    return conn.execute(
        select(deep_links).where(deep_links.c.alias == alias)
    ).one_or_none()


def delete_deep_link_by_alias(conn: Connection, alias: str) -> int:
    """Delete a content shortcut.

    Args:
        conn: SQLAlchemy connection.
        alias: Alias to delete.

    Returns:
        Number of rows deleted.
    """
    result = conn.execute(deep_links.delete().where(deep_links.c.alias == alias))
    conn.commit()
    return int(result.rowcount)


def update_deep_link_launch_stats(
    conn: Connection, alias: str, ran_at: datetime
) -> None:
    """Increment shortcut launch count.

    Args:
        conn: SQLAlchemy connection.
        alias: Shortcut alias.
        ran_at: Timestamp.
    """
    conn.execute(
        update(deep_links)
        .where(deep_links.c.alias == alias)
        .values(launch_count=deep_links.c.launch_count + 1, last_launched_at=ran_at)
    )
    conn.commit()
