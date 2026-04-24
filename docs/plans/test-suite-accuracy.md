# Plan: Fix Test Suite Accuracy (Post-Coverage Audit)

## Context

After achieving 100% line coverage, an audit identified 12 issues where tests pass even when the code is broken — tests that only check "doesn't crash," table-type checks with no content assertions, and side effects (ECP calls, DB writes) that are never verified. This plan strengthens the suite to catch real regressions, not just measure line execution.

---

## Files to Modify

| File | Issues addressed |
|---|---|
| `tests/test_console_panel.py` | H1 |
| `tests/test_db_commands.py` | H2, M2 |
| `tests/test_apps_handlers_extra.py` | H3, M1, M5 |
| `tests/test_database.py` | H4 |
| `tests/test_widget_interactions.py` | H5 |
| `tests/test_system_handlers.py` | H6 |
| `tests/test_discovery_screen.py` | H7 |
| `tests/test_app.py` | M3 |

No new files. No source changes.

---

## Fix Details

### H1 — Highlighter tests: add style assertions
**File:** `tests/test_console_panel.py`

`CommandHighlighter.highlight()` calls `text.stylize(style, start, end)` which appends `Span(start, end, style)` to `text._spans`. Currently none of the five tests assert on `_spans`.

Changes per test:

- `test_highlighter_empty_string_returns_early`: add `assert len(t._spans) == 0`
- `test_highlighter_known_command` (`"home"`): add `assert len(t._spans) == 1` and `assert t._spans[0].style == "bold #7aa2f7"` (primary style for exact-name match)
- `test_highlighter_alias_command` (`"channels"` is alias for `apps`): add `assert len(t._spans) == 1` and `assert t._spans[0].style == "bold #bb9af7"` (alias style)
- `test_highlighter_unknown_command` (`"badcmd"`): add `assert len(t._spans) == 1` and `assert t._spans[0].style == "bold #f7768e"` (error style)
- `test_highlighter_chained_commands` (`"home; up"`): add `assert len(t._spans) == 2` (one span per command word)

Style strings sourced from `console_panel.py` lines 48-52.

---

### H2 — Macro list tests: assert table content
**File:** `tests/test_db_commands.py`

The three `test_macro_list_*` tests only assert `isinstance(result, Table)`. Use `rich.console.Console` + `io.StringIO` to render the table and assert on output text.

Pattern to use in each test:
```python
from io import StringIO
from rich.console import Console
buf = StringIO()
Console(file=buf, width=120, highlight=False).print(result)
rendered = buf.getvalue()
```

Assertions to add:
- `test_macro_list_with_user_macro`: assert `"mymacro" in rendered`, `"Does stuff" in rendered`, `"2" in rendered`, `"user" in rendered`
- `test_macro_list_builtin_badge`: assert `"boot" in rendered`, `"Boot sequence" in rendered`, `"builtin" in rendered`
- `test_macro_list_abort_badge`: assert `"critical" in rendered`, `"user abort" in rendered`

Badge text sourced from `db_commands.py` lines 32-38: `"[dim]builtin[/dim]"`, `"[#9ece6a]user abort[/#9ece6a]"`, `"[#9ece6a]user[/#9ece6a]"`. After rendering with Console, the markup tags are stripped so we assert on the plain-text badge words.

---

### H3 — Deep link launch: verify ECP call was made
**File:** `tests/test_apps_handlers_extra.py`

`test_launch_deep_link` uses `_make_client()` which discards network events (`lambda _: None`). Change to capture events and assert the correct ECP call was made.

Changes:
```python
# Replace _make_client() with event-capturing client
events: list[NetworkEvent] = []
client = MockEcpClient(on_network_event=events.append)
result = await handle_launch(client, ["bb"], ctx)
assert "Deep link launched" in result
assert "Netflix" in result
# Verify ECP launch was called with correct app_id and contentId
assert any("/launch/2285" in e.url for e in events)
assert any("contentId=tt0903747" in e.url for e in events)
```

`test_launch_deep_link_no_client` (client=None) needs no change — launch is correctly skipped when client is absent.

---

### H4 — Migration test: verify abort_on_fail column is functional
**File:** `tests/test_database.py`

`test_migrate_adds_abort_on_fail_column` currently only checks that `list_macros()` runs without error after migration. Add assertions that verify the `abort_on_fail` column exists in the returned data and can hold a boolean value.

Add after `macros = d.list_macros()`:
```python
assert len(macros) > 0
# Verify abort_on_fail column was created and is readable
assert "abort_on_fail" in macros[0]
# Verify the column is writable — use set_macro_abort_flag
from roku_tui.db.queries.macros import set_macro_abort_flag
with d._engine.begin() as conn:
    conn.execute(set_macro_abort_flag(macros[0]["name"], True))
updated = d.list_macros()
target = next(m for m in updated if m["name"] == macros[0]["name"])
assert target["abort_on_fail"] in (True, 1)  # SQLite returns int
```

`set_macro_abort_flag` is already in `roku_tui/db/queries/macros.py` lines 142-153. `d._engine` is the SQLAlchemy engine used internally by `Database`.

---

### H5 — Scroll preservation test: fail loudly if precondition not met
**File:** `tests/test_widget_interactions.py`

`test_network_panel_preserves_scroll_when_not_at_bottom` wraps its core assertion in `if table.max_scroll_y > 1:`, so if the 15-row table doesn't overflow the test terminal, the test silently passes without exercising line 82.

Change:
```python
# Before (silent skip):
if table.max_scroll_y > 1:
    ...

# After (loud failure):
assert table.max_scroll_y > 1, (
    "Table must be scrollable to test scroll preservation; "
    "increase row count or reduce terminal height"
)
table.scroll_y = 0
...
```

---

### H6 — handle_type: verify per-character keypresses
**File:** `tests/test_system_handlers.py`

`test_type_with_client` and `test_type_multi_word` only check the return string. They don't verify that `client.keypress()` was called once per character with the correct `Lit_` encoding.

Changes:
- `test_type_with_client`: replace `_make_client()` with event-capturing client; assert `len(events) == 5` (for "hello") and spot-check `"/keypress/Lit_h" in events[0].url`
- `test_type_multi_word`: assert `len(events) == 11` (for "hello world", including the space as `Lit_%20`) and spot-check space character: `"/keypress/Lit_%20" in events[5].url`

Pattern (same `events` list approach as H3).

---

### H7 — SSDP worker test: make timing robust
**File:** `tests/test_discovery_screen.py`

`test_discover_ssdp_posts_found_message` uses two bare `await pilot.pause()` calls to wait for a `@work(thread=True)` worker. This is non-deterministic.

Change the two bare pauses to a single longer pause:
```python
# Replace:
await pilot.pause()
await pilot.pause()

# With:
await pilot.pause(0.2)  # Give thread worker time to post message and have it processed
```

`discover_rokus` and `_get_device_name_sync` are both mocked to return immediately, so 200ms is more than sufficient while keeping the test fast.

---

### M1 — Deep link: assert analytics recording
**File:** `tests/test_apps_handlers_extra.py`

In `test_launch_deep_link`, `ctx.db.record_deep_link_launch` is set up as a Mock but never asserted. Add:
```python
ctx.db.record_deep_link_launch.assert_called_once_with("bb")
```

---

### M2 — Stats and history: assert table content
**File:** `tests/test_db_commands.py`

Use the same Console render pattern from H2.

- `test_handle_stats` with data: assert `"Days active" in rendered` and the app name appears
- `test_handle_history_with_data`: assert the command text (e.g., `"home"`) appears in rendered output and the success indicator (`"✓"`) is present

---

### M3 — async_connect: eliminate RuntimeWarning
**File:** `tests/test_app.py`

`test_async_connect_calls_service` calls `await app._async_connect(...)` directly, leaving `_prefetch_info`'s worker coroutine unawaited (visible as a RuntimeWarning in test output).

Change to call via `_connect` (the normal path) and wait a tick:
```python
async def test_async_connect_calls_service(app: RokuTuiApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause()
        with patch.object(app.service, "connect", new_callable=AsyncMock) as mock_conn:
            app._connect("192.168.1.50")   # calls run_worker(_async_connect(...))
            await pilot.pause()            # let worker dispatch
            mock_conn.assert_called_once_with("192.168.1.50")
```

---

### M4 (note only — no test change)
`MockEcpClient` requires `on_network_event` as a positional arg; `EcpClient` has it optional. The `_make_client()` helper satisfies this by passing `lambda _: None`. This divergence is acceptable since handler tests care about return values, not network callbacks. No change needed.

---

### M5 — handle_launch: empty cache + no client
**File:** `tests/test_apps_handlers_extra.py`

Add one test for the path where `app_cache` is empty AND client is None (deep link miss → no cache fetch → no match):
```python
async def test_launch_no_app_cache_and_no_client() -> None:
    ctx = MockContext()
    ctx.db.get_deep_link.return_value = None
    ctx.app_cache = []
    result = await handle_launch(None, ["netflix"], ctx)
    assert "No app matching" in result
```

---

## Verification

```bash
uv run pytest --cov=roku_tui --cov-report=term-missing -q
```

Expected: 100% coverage maintained, all tests pass, no RuntimeWarnings in output.

Also run type check to ensure no new type errors were introduced:
```bash
uv run mypy .
```
