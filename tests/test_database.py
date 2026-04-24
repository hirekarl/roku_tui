from __future__ import annotations

from pathlib import Path

import pytest

from roku_tui.db.database import Database
from roku_tui.ecp.models import AppInfo, DeviceInfo, NetworkEvent


@pytest.fixture
def db(tmp_path: Path) -> Database:
    d = Database(tmp_path / "test.db")
    d.initialize()
    return d


def _device_info(name: str = "Test Roku") -> DeviceInfo:
    return DeviceInfo(
        friendly_name=name,
        model_name="Express",
        serial_number="SN123",
        software_version="11.0",
        ethernet_mac="00:11:22:33:44:55",
        wifi_mac="00:11:22:33:44:56",
    )


# ── devices ───────────────────────────────────────────────────────────────────


def test_upsert_and_get_device(db: Database) -> None:
    info = _device_info()
    device_id = db.upsert_device(info, "192.168.1.10")
    assert isinstance(device_id, int)
    assert device_id > 0
    fetched = db.get_device_id("192.168.1.10")
    assert fetched == device_id


def test_upsert_device_twice_increments_count(db: Database) -> None:
    info = _device_info()
    db.upsert_device(info, "192.168.1.10")
    db.upsert_device(info, "192.168.1.10")
    devs = db.list_devices()
    assert len(devs) == 1
    assert devs[0]["connect_count"] == 2


def test_get_device_id_unknown_returns_none(db: Database) -> None:
    assert db.get_device_id("1.2.3.4") is None


def test_list_devices_empty(db: Database) -> None:
    assert db.list_devices() == []


def test_list_devices_returns_rows(db: Database) -> None:
    db.upsert_device(_device_info("Bedroom"), "192.168.1.11")
    devs = db.list_devices()
    assert len(devs) == 1
    assert devs[0]["ip"] == "192.168.1.11"


def test_known_device_ips(db: Database) -> None:
    db.upsert_device(_device_info(), "10.0.0.1")
    ips = db.known_device_ips()
    assert "10.0.0.1" in ips


# ── device apps ───────────────────────────────────────────────────────────────


def test_sync_and_get_device_apps(db: Database) -> None:
    dev_id = db.upsert_device(_device_info(), "192.168.1.20")
    apps = [
        AppInfo("2285", "Netflix", "4.0", "ndka"),
        AppInfo("13", "Prime Video", "3.0", "ndka"),
    ]
    db.sync_device_apps(apps, dev_id)
    result = db.get_device_apps(dev_id)
    assert len(result) == 2
    names = {r["app_name"] for r in result}
    assert names == {"Netflix", "Prime Video"}


def test_sync_device_apps_replaces_old(db: Database) -> None:
    dev_id = db.upsert_device(_device_info(), "192.168.1.20")
    db.sync_device_apps([AppInfo("2285", "Netflix", "4.0", "ndka")], dev_id)
    db.sync_device_apps([AppInfo("13", "Prime", "3.0", "ndka")], dev_id)
    result = db.get_device_apps(dev_id)
    assert len(result) == 1
    assert result[0]["app_name"] == "Prime"


# ── commands ─────────────────────────────────────────────────────────────────


def test_log_and_recent_commands(db: Database) -> None:
    db.log_command("home", success=True, device_id=None)
    db.log_command("up 3", success=True, device_id=None)
    rows = db.recent_commands(limit=10)
    assert len(rows) == 2


def test_recent_commands_respects_limit(db: Database) -> None:
    for i in range(5):
        db.log_command(f"cmd{i}", success=True, device_id=None)
    rows = db.recent_commands(limit=3)
    assert len(rows) == 3


def test_search_commands(db: Database) -> None:
    db.log_command("launch netflix", success=True, device_id=None)
    db.log_command("home", success=True, device_id=None)
    results = db.search_commands("netflix")
    assert len(results) == 1
    assert results[0]["line"] == "launch netflix"


def test_search_commands_no_match(db: Database) -> None:
    db.log_command("home", success=True, device_id=None)
    assert db.search_commands("zzznomatch") == []


# ── macros ────────────────────────────────────────────────────────────────────


def test_list_macros_returns_builtins(db: Database) -> None:
    macros = db.list_macros()
    assert len(macros) > 0
    assert all(isinstance(m["name"], str) for m in macros)


def test_get_macro_not_found(db: Database) -> None:
    assert db.get_macro("nonexistent") is None


def test_save_and_get_macro(db: Database) -> None:
    db.save_macro("mymacro", "test macro", ["home", "up 2"])
    macro = db.get_macro("mymacro")
    assert macro is not None
    assert macro["commands"] == ["home", "up 2"]
    assert macro["description"] == "test macro"


def test_save_macro_overwrite_user_macro(db: Database) -> None:
    db.save_macro("mymacro", "v1", ["home"])
    db.save_macro("mymacro", "v2", ["up"])
    macro = db.get_macro("mymacro")
    assert macro is not None
    assert macro["commands"] == ["up"]


def test_save_macro_cannot_overwrite_builtin(db: Database) -> None:
    builtins = db.list_macros()
    builtin_name = next(m["name"] for m in builtins if m["is_builtin"])
    with pytest.raises(ValueError, match="builtin"):
        db.save_macro(builtin_name, "override", ["home"])


def test_delete_macro(db: Database) -> None:
    db.save_macro("deleteme", "", ["home"])
    db.delete_macro("deleteme")
    assert db.get_macro("deleteme") is None


def test_delete_macro_not_found_raises(db: Database) -> None:
    with pytest.raises(ValueError):
        db.delete_macro("nonexistent")


def test_delete_builtin_macro_raises(db: Database) -> None:
    builtins = db.list_macros()
    builtin_name = next(m["name"] for m in builtins if m["is_builtin"])
    with pytest.raises(ValueError, match="builtin"):
        db.delete_macro(builtin_name)


def test_record_macro_run(db: Database) -> None:
    db.save_macro("runner", "", ["home"])
    db.record_macro_run("runner")
    macro = db.get_macro("runner")
    assert macro is not None


def test_set_macro_abort_flag(db: Database) -> None:
    db.save_macro("flagtest", "", ["home"])
    db.set_macro_abort_flag("flagtest", True)
    macro = db.get_macro("flagtest")
    assert macro is not None
    assert macro["abort_on_fail"] is True


# ── app launches ──────────────────────────────────────────────────────────────


def test_log_app_launch(db: Database) -> None:
    app = AppInfo("2285", "Netflix", "4.0", "ndka")
    db.log_app_launch(app, device_id=None)
    freqs = db.app_launch_frequencies()
    assert "Netflix" in freqs
    assert freqs["Netflix"] == 1


def test_app_launch_frequencies_empty(db: Database) -> None:
    assert db.app_launch_frequencies() == {}


# ── stats ─────────────────────────────────────────────────────────────────────


def test_usage_stats_empty(db: Database) -> None:
    stats = db.usage_stats()
    assert "top_apps" in stats
    assert "top_commands" in stats
    assert "total_days" in stats


def test_usage_stats_with_data(db: Database) -> None:
    app = AppInfo("2285", "Netflix", "4.0", "ndka")
    db.log_app_launch(app, device_id=None)
    db.log_command("home", success=True, device_id=None)
    stats = db.usage_stats()
    assert len(stats["top_apps"]) >= 1
    assert len(stats["top_commands"]) >= 1
    assert stats["total_days"] >= 1


# ── deep links ────────────────────────────────────────────────────────────────


def test_save_and_get_deep_link(db: Database) -> None:
    db.save_deep_link("myalias", "2285", "Netflix", "tt1234567")
    link = db.get_deep_link("myalias")
    assert link is not None
    assert link["app_id"] == "2285"
    assert link["content_id"] == "tt1234567"


def test_get_deep_link_not_found(db: Database) -> None:
    assert db.get_deep_link("nonexistent") is None


def test_list_deep_links(db: Database) -> None:
    db.save_deep_link("link1", "2285", "Netflix", "abc")
    db.save_deep_link("link2", "13", "Prime", "def")
    links = db.list_deep_links()
    assert len(links) == 2


def test_list_deep_links_empty(db: Database) -> None:
    assert db.list_deep_links() == []


def test_update_deep_link(db: Database) -> None:
    db.save_deep_link("link1", "2285", "Netflix", "old_id")
    db.save_deep_link("link1", "2285", "Netflix", "new_id")
    link = db.get_deep_link("link1")
    assert link is not None
    assert link["content_id"] == "new_id"


def test_delete_deep_link(db: Database) -> None:
    db.save_deep_link("link1", "2285", "Netflix", "abc")
    db.delete_deep_link("link1")
    assert db.get_deep_link("link1") is None


def test_record_deep_link_launch(db: Database) -> None:
    db.save_deep_link("link1", "2285", "Netflix", "abc")
    db.record_deep_link_launch("link1")
    link = db.get_deep_link("link1")
    assert link is not None
    assert link["launch_count"] == 1


# ── network ───────────────────────────────────────────────────────────────────


def test_log_network_request(db: Database) -> None:
    event = NetworkEvent(
        method="GET",
        url="http://192.168.1.50:8060/query/apps",
        request_headers={"Host": "192.168.1.50:8060"},
        status_code=200,
        response_headers={"Content-Type": "text/xml"},
        response_time_ms=42.5,
        body="<apps/>",
        error=None,
    )
    db.log_network_request(event, device_id=None)


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    d = Database(tmp_path / "idempotent.db")
    d.initialize()
    d.initialize()
    assert len(d.list_macros()) > 0


def test_migrate_adds_abort_on_fail_column(tmp_path: Path) -> None:
    """Verify the migration runs when the column is missing from an old DB."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool

    db_file = tmp_path / "legacy.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    # Create macros table WITHOUT the abort_on_fail column
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE macros ("
                "id INTEGER PRIMARY KEY,"
                "name TEXT NOT NULL UNIQUE,"
                "description TEXT,"
                "commands TEXT NOT NULL,"
                "created_at DATETIME NOT NULL,"
                "last_run_at DATETIME,"
                "run_count INTEGER NOT NULL DEFAULT 0,"
                "is_builtin BOOLEAN NOT NULL DEFAULT 0"
                ")"
            )
        )
        conn.commit()
    engine.dispose()

    d = Database(db_file)
    d.initialize()  # Should migrate without error
    macros = d.list_macros()
    assert len(macros) > 0
    assert "abort_on_fail" in macros[0]
    d.set_macro_abort_flag(macros[0]["name"], True)
    updated = d.list_macros()
    target = next(m for m in updated if m["name"] == macros[0]["name"])
    assert target["abort_on_fail"] in (True, 1)
