from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from .queries import (
    count_command_days,
    delete_macro_by_name,
    get_device_id,
    insert_app_launch,
    insert_command,
    insert_macro,
    insert_network_request,
    macros_table_is_empty,
    search_commands_by_term,
    select_all_devices,
    select_all_macros,
    select_app_launch_frequencies,
    select_apps_for_device,
    select_macro_by_name,
    select_recent_commands,
    select_top_app_launches,
    select_top_commands,
    sync_device_apps,
    update_macro_run_stats,
    upsert_device,
    upsert_user_macro,
)
from .schema import metadata
from .seeds import BUILTIN_MACROS

if TYPE_CHECKING:
    from ..ecp.models import AppInfo, DeviceInfo, NetworkEvent


class Database:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )

    def initialize(self) -> None:
        metadata.create_all(self._engine)
        with self._engine.connect() as conn:
            if macros_table_is_empty(conn):
                now = datetime.utcnow()
                for m in BUILTIN_MACROS:
                    insert_macro(
                        conn,
                        name=m["name"],
                        description=m["description"],
                        commands_text=m["commands"],
                        created_at=now,
                        is_builtin=True,
                    )

    def close(self) -> None:
        self._engine.dispose()

    # ── devices ──────────────────────────────────────────────────────────────

    def upsert_device(self, info: DeviceInfo, ip: str) -> int:
        with self._engine.connect() as conn:
            return upsert_device(conn, ip, info)

    def get_device_id(self, ip: str) -> int | None:
        with self._engine.connect() as conn:
            return get_device_id(conn, ip)

    def list_devices(self) -> list[dict]:
        with self._engine.connect() as conn:
            rows = select_all_devices(conn)
        return [dict(r._mapping) for r in rows]

    def sync_device_apps(self, apps: list, device_id: int) -> None:
        with self._engine.connect() as conn:
            sync_device_apps(conn, device_id, apps)

    def get_device_apps(self, device_id: int) -> list[dict]:
        with self._engine.connect() as conn:
            rows = select_apps_for_device(conn, device_id)
        return [dict(r._mapping) for r in rows]

    # ── commands ─────────────────────────────────────────────────────────────

    def log_command(self, line: str, success: bool, device_id: int | None) -> None:
        with self._engine.connect() as conn:
            insert_command(conn, line, success, device_id, datetime.utcnow())

    def recent_commands(self, limit: int = 20) -> list[dict]:
        with self._engine.connect() as conn:
            rows = select_recent_commands(conn, limit)
        return [dict(r._mapping) for r in rows]

    def search_commands(self, term: str) -> list[dict]:
        with self._engine.connect() as conn:
            rows = search_commands_by_term(conn, term)
        return [dict(r._mapping) for r in rows]

    # ── network ───────────────────────────────────────────────────────────────

    def log_network_request(self, event: NetworkEvent, device_id: int | None) -> None:
        with self._engine.connect() as conn:
            insert_network_request(conn, event, device_id)

    # ── macros ────────────────────────────────────────────────────────────────

    def list_macros(self) -> list[dict]:
        with self._engine.connect() as conn:
            rows = select_all_macros(conn)
        return [dict(r._mapping) for r in rows]

    def get_macro(self, name: str) -> dict | None:
        with self._engine.connect() as conn:
            row = select_macro_by_name(conn, name)
        if row is None:
            return None
        d = dict(row._mapping)
        d["commands"] = [line for line in d["commands"].split("\n") if line.strip()]
        return d

    def save_macro(self, name: str, description: str, command_lines: list[str]) -> None:
        commands_text = "\n".join(command_lines)
        with self._engine.connect() as conn:
            existing = select_macro_by_name(conn, name)
            if existing and existing.is_builtin:
                raise ValueError(f"Cannot overwrite builtin macro '{name}'")
            upsert_user_macro(conn, name, description, commands_text)

    def delete_macro(self, name: str) -> None:
        with self._engine.connect() as conn:
            existing = select_macro_by_name(conn, name)
            if existing is None:
                raise ValueError(f"No macro named '{name}'")
            if existing.is_builtin:
                raise ValueError(f"Cannot delete builtin macro '{name}'")
            delete_macro_by_name(conn, name)

    def record_macro_run(self, name: str) -> None:
        with self._engine.connect() as conn:
            update_macro_run_stats(conn, name, datetime.utcnow())

    # ── app launches ──────────────────────────────────────────────────────────

    def log_app_launch(self, app: AppInfo, device_id: int | None) -> None:
        with self._engine.connect() as conn:
            insert_app_launch(conn, app.id, app.name, datetime.utcnow(), device_id)

    def app_launch_frequencies(self) -> dict[str, int]:
        with self._engine.connect() as conn:
            rows = select_app_launch_frequencies(conn)
        return {r.app_name: r.count for r in rows}

    # ── stats ─────────────────────────────────────────────────────────────────

    def usage_stats(self) -> dict:
        with self._engine.connect() as conn:
            top_apps = [
                dict(r._mapping) for r in select_top_app_launches(conn, limit=5)
            ]
            top_cmds = [dict(r._mapping) for r in select_top_commands(conn, limit=5)]
            total_days = count_command_days(conn)
        return {
            "top_apps": top_apps,
            "top_commands": top_cmds,
            "total_days": total_days,
        }
