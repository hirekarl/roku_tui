from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Connection, Row, func, select, update

from .schema import (
    app_launches,
    commands,
    deep_links,
    device_apps,
    devices,
    macros,
    network_requests,
)

if TYPE_CHECKING:
    from ..ecp.models import AppInfo, DeviceInfo, NetworkEvent


# ── devices ──────────────────────────────────────────────────────────────────


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


# ── commands ─────────────────────────────────────────────────────────────────


def insert_command(
    conn: Connection,
    line: str,
    success: bool,
    device_id: int | None,
    executed_at: datetime,
) -> None:
    """Log a command execution.

    Args:
        conn: SQLAlchemy connection.
        line: The command line input.
        success: Whether the command succeeded.
        device_id: Optional ID of the device it was sent to.
        executed_at: Timestamp of execution.
    """
    conn.execute(
        commands.insert().values(
            line=line,
            success=success,
            device_id=device_id,
            executed_at=executed_at,
        )
    )
    conn.commit()


def select_recent_commands(conn: Connection, limit: int = 20) -> list[Row[Any]]:
    """Select the most recent commands.

    Args:
        conn: SQLAlchemy connection.
        limit: Number of commands to return.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(
            select(commands).order_by(commands.c.executed_at.desc()).limit(limit)
        ).fetchall()
    )


def search_commands_by_term(conn: Connection, term: str) -> list[Row[Any]]:
    """Search command history by content.

    Args:
        conn: SQLAlchemy connection.
        term: Search substring.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(
            select(commands)
            .where(commands.c.line.like(f"%{term}%"))
            .order_by(commands.c.executed_at.desc())
            .limit(50)
        ).fetchall()
    )


# ── network_requests ──────────────────────────────────────────────────────────


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


# ── macros ────────────────────────────────────────────────────────────────────


def macros_table_is_empty(conn: Connection) -> bool:
    """Check if any macros exist in the database.

    Args:
        conn: SQLAlchemy connection.

    Returns:
        True if the table is empty.
    """
    row = conn.execute(select(func.count()).select_from(macros)).one()
    return bool(row[0] == 0)


def select_all_macros(conn: Connection) -> list[Row[Any]]:
    """Select all macro definitions.

    Args:
        conn: SQLAlchemy connection.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(
            select(
                macros.c.name,
                macros.c.description,
                macros.c.run_count,
                macros.c.is_builtin,
                macros.c.abort_on_fail,
                macros.c.last_run_at,
            ).order_by(macros.c.is_builtin.desc(), macros.c.name)
        ).fetchall()
    )


def select_macro_by_name(conn: Connection, name: str) -> Row[Any] | None:
    """Find a macro by name.

    Args:
        conn: SQLAlchemy connection.
        name: Unique name of the macro.

    Returns:
        The SQLAlchemy Row or None.
    """
    return conn.execute(select(macros).where(macros.c.name == name)).one_or_none()


def insert_macro(
    conn: Connection,
    name: str,
    description: str,
    commands_text: str,
    created_at: datetime,
    is_builtin: bool = False,
) -> None:
    """Insert a new macro definition.

    Args:
        conn: SQLAlchemy connection.
        name: Name of the macro.
        description: User-provided description.
        commands_text: Newline-separated command lines.
        created_at: Creation timestamp.
        is_builtin: Whether this is a factory default macro.
    """
    conn.execute(
        macros.insert().values(
            name=name,
            description=description,
            commands=commands_text,
            created_at=created_at,
            is_builtin=is_builtin,
        )
    )
    conn.commit()


def upsert_user_macro(
    conn: Connection,
    name: str,
    description: str,
    commands_text: str,
) -> None:
    """Create or update a user macro.

    Args:
        conn: SQLAlchemy connection.
        name: Name of the macro.
        description: Macro description.
        commands_text: Command sequence.
    """
    now = datetime.now(UTC)
    existing = select_macro_by_name(conn, name)
    if existing:
        conn.execute(
            update(macros)
            .where(macros.c.name == name)
            .values(description=description, commands=commands_text)
        )
    else:
        conn.execute(
            macros.insert().values(
                name=name,
                description=description,
                commands=commands_text,
                created_at=now,
                is_builtin=False,
            )
        )
    conn.commit()


def delete_macro_by_name(conn: Connection, name: str) -> int:
    """Delete a non-builtin macro.

    Args:
        conn: SQLAlchemy connection.
        name: Name to delete.

    Returns:
        Number of rows deleted.
    """
    result = conn.execute(
        macros.delete().where(macros.c.name == name).where(~macros.c.is_builtin)
    )
    conn.commit()
    return int(result.rowcount)


def set_macro_abort_flag(conn: Connection, name: str, abort_on_fail: bool) -> None:
    """Update the abort policy for a macro.

    Args:
        conn: SQLAlchemy connection.
        name: Macro name.
        abort_on_fail: New policy value.
    """
    conn.execute(
        update(macros).where(macros.c.name == name).values(abort_on_fail=abort_on_fail)
    )
    conn.commit()


def update_macro_run_stats(conn: Connection, name: str, ran_at: datetime) -> None:
    """Increment run count and update timestamp.

    Args:
        conn: SQLAlchemy connection.
        name: Macro name.
        ran_at: Timestamp of execution.
    """
    conn.execute(
        update(macros)
        .where(macros.c.name == name)
        .values(run_count=macros.c.run_count + 1, last_run_at=ran_at)
    )
    conn.commit()


# ── app_launches ──────────────────────────────────────────────────────────────


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


def select_top_commands(conn: Connection, limit: int = 10) -> list[Row[Any]]:
    """Select commands ordered by execution frequency.

    Args:
        conn: SQLAlchemy connection.
        limit: Max results.

    Returns:
        A list of SQLAlchemy Row objects.
    """
    return list(
        conn.execute(
            select(
                commands.c.line,
                func.count().label("count"),
            )
            .group_by(commands.c.line)
            .order_by(func.count().desc())
            .limit(limit)
        ).fetchall()
    )


def count_command_days(conn: Connection) -> int:
    """Count the total number of unique days with command activity.

    Args:
        conn: SQLAlchemy connection.

    Returns:
        The unique day count.
    """
    row = conn.execute(
        select(func.count(func.distinct(func.date(commands.c.executed_at))))
    ).one()
    return int(row[0])


# ── device_apps ───────────────────────────────────────────────────────────────


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


# ── deep_links ───────────────────────────────────────────────────────────────


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
