from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
)

metadata = MetaData()

devices = Table(
    "devices",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("ip", Text, nullable=False, unique=True),
    Column("friendly_name", Text),
    Column("model_name", Text),
    Column("serial_number", Text),
    Column("last_connected_at", DateTime),
    Column("connect_count", Integer, nullable=False, server_default="0"),
)

commands = Table(
    "commands",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("line", Text, nullable=False),
    Column("executed_at", DateTime, nullable=False),
    Column("device_id", Integer, ForeignKey("devices.id"), nullable=True),
    Column("success", Boolean, nullable=False),
)

network_requests = Table(
    "network_requests",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("method", Text, nullable=False),
    Column("url", Text, nullable=False),
    Column("status_code", Integer, nullable=True),
    Column("response_time_ms", Float, nullable=True),
    Column("body", Text),
    Column("error", Text, nullable=True),
    Column("requested_at", DateTime, nullable=False),
    Column("device_id", Integer, ForeignKey("devices.id"), nullable=True),
)

macros = Table(
    "macros",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text),
    Column("commands", Text, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("last_run_at", DateTime, nullable=True),
    Column("run_count", Integer, nullable=False, server_default="0"),
    Column("is_builtin", Boolean, nullable=False, server_default="0"),
)

device_apps = Table(
    "device_apps",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("device_id", Integer, ForeignKey("devices.id"), nullable=False),
    Column("app_id", Text, nullable=False),
    Column("app_name", Text, nullable=False),
    Column("version", Text),
    Column("subtype", Text),
    Column("last_seen_at", DateTime, nullable=False),
)

app_launches = Table(
    "app_launches",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("app_id", Text, nullable=False),
    Column("app_name", Text, nullable=False),
    Column("launched_at", DateTime, nullable=False),
    Column("device_id", Integer, ForeignKey("devices.id"), nullable=True),
)
