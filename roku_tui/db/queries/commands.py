from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Connection, Row, func, select

from ..schema import commands


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
