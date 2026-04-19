from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Connection, func, select, update

from .schema import (
    app_launches,
    commands,
    device_apps,
    devices,
    macros,
    network_requests,
)

if TYPE_CHECKING:
    from ..ecp.models import DeviceInfo, NetworkEvent


# ── devices ──────────────────────────────────────────────────────────────────

def upsert_device(conn: Connection, ip: str, info: DeviceInfo) -> int:
    now = datetime.now(UTC)
    conn.execute(
        devices.insert().prefix_with("OR IGNORE").values(
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
    return row.id


def get_device_id(conn: Connection, ip: str) -> int | None:
    row = conn.execute(select(devices.c.id).where(devices.c.ip == ip)).one_or_none()
    return row.id if row else None


def select_all_devices(conn: Connection) -> list:
    return conn.execute(
        select(
            devices.c.ip,
            devices.c.friendly_name,
            devices.c.model_name,
            devices.c.last_connected_at,
            devices.c.connect_count,
        ).order_by(devices.c.last_connected_at.desc())
    ).fetchall()


# ── commands ─────────────────────────────────────────────────────────────────

def insert_command(
    conn: Connection,
    line: str,
    success: bool,
    device_id: int | None,
    executed_at: datetime,
) -> None:
    conn.execute(
        commands.insert().values(
            line=line,
            success=success,
            device_id=device_id,
            executed_at=executed_at,
        )
    )
    conn.commit()


def select_recent_commands(conn: Connection, limit: int = 20) -> list:
    return conn.execute(
        select(commands).order_by(commands.c.executed_at.desc()).limit(limit)
    ).fetchall()


def search_commands_by_term(conn: Connection, term: str) -> list:
    return conn.execute(
        select(commands)
        .where(commands.c.line.like(f"%{term}%"))
        .order_by(commands.c.executed_at.desc())
        .limit(50)
    ).fetchall()


# ── network_requests ──────────────────────────────────────────────────────────

def insert_network_request(
    conn: Connection,
    event: NetworkEvent,
    device_id: int | None,
) -> None:
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
    row = conn.execute(select(func.count()).select_from(macros)).one()
    return row[0] == 0


def select_all_macros(conn: Connection) -> list:
    return conn.execute(
        select(
            macros.c.name,
            macros.c.description,
            macros.c.run_count,
            macros.c.is_builtin,
            macros.c.abort_on_fail,
            macros.c.last_run_at,
        ).order_by(macros.c.is_builtin.desc(), macros.c.name)
    ).fetchall()


def select_macro_by_name(conn: Connection, name: str):
    return conn.execute(
        select(macros).where(macros.c.name == name)
    ).one_or_none()


def insert_macro(
    conn: Connection,
    name: str,
    description: str,
    commands_text: str,
    created_at: datetime,
    is_builtin: bool = False,
) -> None:
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
    result = conn.execute(
        macros.delete().where(macros.c.name == name).where(~macros.c.is_builtin)
    )
    conn.commit()
    return result.rowcount


def set_macro_abort_flag(conn: Connection, name: str, abort_on_fail: bool) -> None:
    conn.execute(
        update(macros).where(macros.c.name == name).values(abort_on_fail=abort_on_fail)
    )
    conn.commit()


def update_macro_run_stats(conn: Connection, name: str, ran_at: datetime) -> None:
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
    conn.execute(
        app_launches.insert().values(
            app_id=app_id,
            app_name=app_name,
            launched_at=launched_at,
            device_id=device_id,
        )
    )
    conn.commit()


def select_top_app_launches(conn: Connection, limit: int = 10) -> list:
    return conn.execute(
        select(
            app_launches.c.app_id,
            app_launches.c.app_name,
            func.count().label("count"),
        )
        .group_by(app_launches.c.app_id)
        .order_by(func.count().desc())
        .limit(limit)
    ).fetchall()


def select_app_launch_frequencies(conn: Connection) -> list:
    return conn.execute(
        select(
            app_launches.c.app_name,
            func.count().label("count"),
        )
        .group_by(app_launches.c.app_name)
        .order_by(func.count().desc())
    ).fetchall()


def select_top_commands(conn: Connection, limit: int = 10) -> list:
    return conn.execute(
        select(
            commands.c.line,
            func.count().label("count"),
        )
        .group_by(commands.c.line)
        .order_by(func.count().desc())
        .limit(limit)
    ).fetchall()


def count_command_days(conn: Connection) -> int:
    row = conn.execute(
        select(func.count(func.distinct(func.date(commands.c.executed_at))))
    ).one()
    return row[0]


# ── device_apps ───────────────────────────────────────────────────────────────

def sync_device_apps(conn: Connection, device_id: int, apps: list) -> None:
    """Replace all app rows for a device with the current list."""
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


def select_apps_for_device(conn: Connection, device_id: int) -> list:
    return conn.execute(
        select(device_apps)
        .where(device_apps.c.device_id == device_id)
        .order_by(device_apps.c.app_name)
    ).fetchall()
