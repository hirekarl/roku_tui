from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Connection, Row, func, select, update

from ..schema import macros


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
