from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from .queries import (
    count_command_days,
    delete_deep_link_by_alias,
    delete_macro_by_name,
    get_device_id,
    insert_app_launch,
    insert_command,
    insert_macro,
    insert_network_request,
    macros_table_is_empty,
    search_commands_by_term,
    select_all_deep_links,
    select_all_devices,
    select_all_macros,
    select_app_launch_frequencies,
    select_apps_for_device,
    select_deep_link_by_alias,
    select_macro_by_name,
    select_recent_commands,
    select_top_app_launches,
    select_top_commands,
    set_macro_abort_flag,
    sync_device_apps,
    update_deep_link_launch_stats,
    update_macro_run_stats,
    upsert_deep_link,
    upsert_device,
    upsert_user_macro,
)
from .schema import metadata
from .seeds import BUILTIN_MACROS

if TYPE_CHECKING:
    from ..ecp.models import AppInfo, DeviceInfo, NetworkEvent


class Database:
    """Public API for the local SQLite database."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the database engine.

        Args:
            db_path: Path to the SQLite database file.
        """
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )

    def initialize(self) -> None:
        """Create tables and seed built-in macros if empty."""
        metadata.create_all(self._engine)
        with self._engine.connect() as conn:
            self._migrate(conn)
            if macros_table_is_empty(conn):
                now = datetime.now(UTC)
                for m in BUILTIN_MACROS:
                    insert_macro(
                        conn,
                        name=m["name"],
                        description=m["description"],
                        commands_text=m["commands"],
                        created_at=now,
                        is_builtin=True,
                    )

    def _migrate(self, conn: Any) -> None:
        """Perform simple schema migrations."""
        cols = {
            row[1] for row in conn.execute(text("PRAGMA table_info(macros)")).fetchall()
        }
        if "abort_on_fail" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE macros ADD COLUMN"
                    " abort_on_fail BOOLEAN NOT NULL DEFAULT 0"
                )
            )
            conn.commit()

    def close(self) -> None:
        """Dispose of the database engine."""
        self._engine.dispose()

    # ── devices ──────────────────────────────────────────────────────────────

    def upsert_device(self, info: DeviceInfo, ip: str) -> int:
        """Register or update a Roku device."""
        with self._engine.connect() as conn:
            return upsert_device(conn, ip, info)

    def get_device_id(self, ip: str) -> int | None:
        """Get the database ID for a device IP."""
        with self._engine.connect() as conn:
            return get_device_id(conn, ip)

    def list_devices(self) -> list[dict[str, Any]]:
        """List all registered devices."""
        with self._engine.connect() as conn:
            rows = select_all_devices(conn)
        return [dict(r._mapping) for r in rows]

    def known_device_ips(self) -> list[str]:
        """Return known device IPs ordered by most recently connected."""
        return [d["ip"] for d in self.list_devices()]

    def sync_device_apps(self, apps: list[AppInfo], device_id: int) -> None:
        """Update the list of apps associated with a device."""
        with self._engine.connect() as conn:
            sync_device_apps(conn, device_id, apps)

    def get_device_apps(self, device_id: int) -> list[dict[str, Any]]:
        """Get the cached list of apps for a device."""
        with self._engine.connect() as conn:
            rows = select_apps_for_device(conn, device_id)
        return [dict(r._mapping) for r in rows]

    # ── commands ─────────────────────────────────────────────────────────────

    def log_command(self, line: str, success: bool, device_id: int | None) -> None:
        """Log a command execution attempt."""
        with self._engine.connect() as conn:
            insert_command(conn, line, success, device_id, datetime.now(UTC))

    def recent_commands(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent command history."""
        with self._engine.connect() as conn:
            rows = select_recent_commands(conn, limit)
        return [dict(r._mapping) for r in rows]

    def search_commands(self, term: str) -> list[dict[str, Any]]:
        """Search command history by line content."""
        with self._engine.connect() as conn:
            rows = search_commands_by_term(conn, term)
        return [dict(r._mapping) for r in rows]

    # ── network ───────────────────────────────────────────────────────────────

    def log_network_request(self, event: NetworkEvent, device_id: int | None) -> None:
        """Log an ECP network request/response event."""
        with self._engine.connect() as conn:
            insert_network_request(conn, event, device_id)

    # ── macros ────────────────────────────────────────────────────────────────

    def list_macros(self) -> list[dict[str, Any]]:
        """List all defined macros."""
        with self._engine.connect() as conn:
            rows = select_all_macros(conn)
        return [dict(r._mapping) for r in rows]

    def get_macro(self, name: str) -> dict[str, Any] | None:
        """Get a single macro definition."""
        with self._engine.connect() as conn:
            row = select_macro_by_name(conn, name)
        if row is None:
            return None
        d = dict(row._mapping)
        d["commands"] = [line for line in d["commands"].split("\n") if line.strip()]
        return d

    def save_macro(self, name: str, description: str, command_lines: list[str]) -> None:
        """Create or update a user macro."""
        commands_text = "\n".join(command_lines)
        with self._engine.connect() as conn:
            existing = select_macro_by_name(conn, name)
            if existing and existing.is_builtin:
                raise ValueError(f"Cannot overwrite builtin macro '{name}'")
            upsert_user_macro(conn, name, description, commands_text)

    def delete_macro(self, name: str) -> None:
        """Delete a user macro."""
        with self._engine.connect() as conn:
            existing = select_macro_by_name(conn, name)
            if existing is None:
                raise ValueError(f"No macro named '{name}'")
            if existing.is_builtin:
                raise ValueError(f"Cannot delete builtin macro '{name}'")
            delete_macro_by_name(conn, name)

    def record_macro_run(self, name: str) -> None:
        """Increment run count and update timestamp for a macro."""
        with self._engine.connect() as conn:
            update_macro_run_stats(conn, name, datetime.now(UTC))

    def set_macro_abort_flag(self, name: str, abort_on_fail: bool) -> None:
        """Set the 'abort on fail' policy for a macro."""
        with self._engine.connect() as conn:
            set_macro_abort_flag(conn, name, abort_on_fail)

    # ── app launches ──────────────────────────────────────────────────────────

    def log_app_launch(self, app: AppInfo, device_id: int | None) -> None:
        """Log an app launch event."""
        with self._engine.connect() as conn:
            insert_app_launch(conn, app.id, app.name, datetime.now(UTC), device_id)

    def app_launch_frequencies(self) -> dict[str, int]:
        """Get launch counts for all apps."""
        with self._engine.connect() as conn:
            rows = select_app_launch_frequencies(conn)
        return {str(r._mapping["app_name"]): int(r._mapping["count"]) for r in rows}

    # ── stats ─────────────────────────────────────────────────────────────────

    def usage_stats(self) -> dict[str, Any]:
        """Calculate application-wide usage statistics."""
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

    # ── deep links ────────────────────────────────────────────────────────────

    def list_deep_links(self) -> list[dict[str, Any]]:
        """List all saved deep link content shortcuts."""
        with self._engine.connect() as conn:
            rows = select_all_deep_links(conn)
        return [dict(r._mapping) for r in rows]

    def get_deep_link(self, alias: str) -> dict[str, Any] | None:
        """Get a deep link definition by its alias."""
        with self._engine.connect() as conn:
            row = select_deep_link_by_alias(conn, alias)
        return dict(row._mapping) if row else None

    def save_deep_link(
        self,
        alias: str,
        app_id: str,
        app_name: str | None,
        content_id: str,
        media_type: str | None = None,
    ) -> None:
        """Create or update a deep link shortcut."""
        with self._engine.connect() as conn:
            upsert_deep_link(conn, alias, app_id, app_name, content_id, media_type)

    def delete_deep_link(self, alias: str) -> None:
        """Delete a deep link shortcut."""
        with self._engine.connect() as conn:
            delete_deep_link_by_alias(conn, alias)

    def record_deep_link_launch(self, alias: str) -> None:
        """Increment launch stats for a deep link shortcut."""
        with self._engine.connect() as conn:
            update_deep_link_launch_stats(conn, alias, datetime.now(UTC))
