from __future__ import annotations

import asyncio
from typing import Any

from rich.table import Table

from .registry import Command, CommandRegistry

META_PREFIXES = ("macro ", "history", "stats", "devices", "help", "clear", "cls")
_SLEEP_MAX = 30.0


# ── macro sub-handlers ────────────────────────────────────────────────────────

async def _macro_list(client: Any, args: list[str], context: Any):
    macros = context.db.list_macros()
    if not macros:
        return "[dim]No macros defined.[/dim]"
    table = Table(
        box=None, show_header=True, header_style="bold #7aa2f7", padding=(0, 2, 0, 0)
    )
    table.add_column("Name", width=16)
    table.add_column("Description")
    table.add_column("Runs", justify="right", width=5)
    table.add_column("", width=9)
    for m in macros:
        if m["is_builtin"]:
            badge = "[dim]builtin[/dim]"
        elif m["abort_on_fail"]:
            badge = "[#9ece6a]user abort[/#9ece6a]"
        else:
            badge = "[#9ece6a]user[/#9ece6a]"
        table.add_row(m["name"], m["description"] or "", str(m["run_count"]), badge)
    return table


async def _macro_run(client: Any, args: list[str], context: Any):
    if not args:
        return "[red]Usage:[/red] macro run <name>"
    name = args[0]
    macro = context.db.get_macro(name)
    if macro is None:
        return f"[yellow]No macro named[/yellow] '{name}'"

    abort = macro.get("abort_on_fail", False)
    steps = macro["commands"]
    for i, line in enumerate(steps, 1):
        context.emit_message(f"[dim]macro ›[/dim] {line}")
        ok = await context.dispatch(line)
        if not ok and abort:
            context.db.record_macro_run(name)
            return (
                f"[red]Macro[/red] [bold]{name}[/bold] [red]aborted[/red]"
                f" [dim]at step {i}/{len(steps)}: {line}[/dim]"
            )

    context.db.record_macro_run(name)
    plural = "s" if len(steps) != 1 else ""
    done = f"done ({len(steps)} step{plural})"
    return f"[dim]Macro[/dim] [bold]{name}[/bold] [dim]{done}.[/dim]"


async def _macro_save(client: Any, args: list[str], context: Any):
    if not args:
        return "[red]Usage:[/red] macro save <name> [description]"
    name = args[0]
    description = " ".join(args[1:])

    recent = context.db.recent_commands(limit=20)
    lines = [
        r["line"] for r in reversed(recent)
        if r["success"] and not any(r["line"].startswith(p) for p in META_PREFIXES)
    ][:10]

    if not lines:
        return "[yellow]No recent commands to save.[/yellow] Run some commands first."

    try:
        context.db.save_macro(name, description, lines)
    except ValueError as e:
        return f"[red]Error:[/red] {e}"

    plural = "s" if len(lines) != 1 else ""
    steps_preview = ", ".join(f"[italic]{ln}[/italic]" for ln in lines)
    saved = f"saved ([dim]{len(lines)} step{plural}[/dim])"
    return f"[bold]{name}[/bold] {saved}: {steps_preview}"


async def _macro_show(client: Any, args: list[str], context: Any):
    if not args:
        return "[red]Usage:[/red] macro show <name>"
    macro = context.db.get_macro(args[0])
    if macro is None:
        return f"[yellow]No macro named[/yellow] '{args[0]}'"
    abort_label = (
        "[#f7768e]abort on fail[/#f7768e]"
        if macro.get("abort_on_fail")
        else "[dim]continue on fail[/dim]"
    )
    table = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    table.add_column(style="dim", width=4)
    table.add_column()
    table.add_row("", abort_label)
    table.add_row("", "")
    for i, line in enumerate(macro["commands"], 1):
        table.add_row(str(i), line)
    return table


async def _macro_set(client: Any, args: list[str], context: Any):
    # args: ["<name>", "abort", "on|off"]
    if len(args) < 3 or args[1] != "abort" or args[2] not in ("on", "off"):
        return "[red]Usage:[/red] macro set <name> abort on|off"
    name, _, value = args[0], args[1], args[2]
    macro = context.db.get_macro(name)
    if macro is None:
        return f"[yellow]No macro named[/yellow] '{name}'"
    abort_on_fail = value == "on"
    context.db.set_macro_abort_flag(name, abort_on_fail)
    on = "[#f7768e]abort on fail[/#f7768e]"
    off = "[dim]continue on fail[/dim]"
    state = on if abort_on_fail else off
    return f"[bold]{name}[/bold] → {state}"


async def _macro_delete(client: Any, args: list[str], context: Any):
    if not args:
        return "[red]Usage:[/red] macro delete <name>"
    try:
        context.db.delete_macro(args[0])
    except ValueError as e:
        return f"[red]Error:[/red] {e}"
    return f"[dim]Deleted macro[/dim] [bold]{args[0]}[/bold]"


_MACRO_SUBS = {
    "list": _macro_list,
    "run": _macro_run,
    "save": _macro_save,
    "show": _macro_show,
    "delete": _macro_delete,
    "set": _macro_set,
}


async def handle_macro(client: Any, args: list[str], context: Any):
    sub = args[0] if args else ""
    fn = _MACRO_SUBS.get(sub)
    if fn is None:
        return (
            "[red]Usage:[/red] macro "
            "[bold]list[/bold] | [bold]run[/bold] <name> | "
            "[bold]save[/bold] <name> | [bold]show[/bold] <name> | "
            "[bold]delete[/bold] <name> | "
            "[bold]set[/bold] <name> abort on|off"
        )
    return await fn(client, args[1:], context)


# ── history ───────────────────────────────────────────────────────────────────

async def handle_history(client: Any, args: list[str], context: Any):
    if args and args[0] == "search":
        term = " ".join(args[1:])
        if not term:
            return "[red]Usage:[/red] history search <term>"
        rows = context.db.search_commands(term)
    else:
        limit = int(args[0]) if args and args[0].isdigit() else 20
        rows = context.db.recent_commands(limit)

    if not rows:
        return "[dim]No command history yet.[/dim]"

    table = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    table.add_column(style="dim", width=20)
    table.add_column()
    table.add_column(style="dim", width=4)
    for r in rows:
        ts = r["executed_at"].strftime("%m-%d %H:%M") if r["executed_at"] else ""
        status = "[green]✓[/green]" if r["success"] else "[red]✗[/red]"
        table.add_row(ts, r["line"], status)
    return table


# ── stats ─────────────────────────────────────────────────────────────────────

async def handle_stats(client: Any, args: list[str], context: Any):
    stats = context.db.usage_stats()

    table = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    table.add_column(style="bold #7aa2f7", width=22)
    table.add_column()

    if stats["top_apps"]:
        table.add_row("[bold]Top apps launched[/bold]", "")
        for a in stats["top_apps"]:
            table.add_row(f"  {a['app_name']}", f"{a['count']}×")
        table.add_row("", "")

    if stats["top_commands"]:
        table.add_row("[bold]Top commands[/bold]", "")
        for c in stats["top_commands"]:
            table.add_row(f"  {c['line']}", f"{c['count']}×")
        table.add_row("", "")

    table.add_row("Days active", str(stats["total_days"]))
    return table


# ── devices ───────────────────────────────────────────────────────────────────

async def handle_devices(client: Any, args: list[str], context: Any):
    devs = context.db.list_devices()
    if not devs:
        return "[dim]No devices seen yet.[/dim]"
    table = Table(
        box=None, show_header=True, header_style="bold #7aa2f7", padding=(0, 2, 0, 0)
    )
    table.add_column("IP")
    table.add_column("Name")
    table.add_column("Model")
    table.add_column("Last seen")
    table.add_column("Connects", justify="right")
    for d in devs:
        ts = (
            d["last_connected_at"].strftime("%Y-%m-%d %H:%M")
            if d["last_connected_at"]
            else "—"
        )
        table.add_row(
            d["ip"],
            d["friendly_name"] or "—",
            d["model_name"] or "—",
            ts,
            str(d["connect_count"]),
        )
    return table


# ── sleep ─────────────────────────────────────────────────────────────────────

async def handle_sleep(client: Any, args: list[str], context: Any):
    if not args:
        return f"[red]Usage:[/red] sleep <seconds> (max {_SLEEP_MAX:.0f})"
    try:
        secs = float(args[0])
    except ValueError:
        return f"[red]Usage:[/red] sleep <seconds> (max {_SLEEP_MAX:.0f})"
    if secs <= 0 or secs > _SLEEP_MAX:
        return f"[red]sleep:[/red] value must be between 0 and {_SLEEP_MAX:.0f}"
    await asyncio.sleep(secs)
    return f"[dim]Slept {secs:g}s[/dim]"


# ── registration ──────────────────────────────────────────────────────────────

def register_db_commands(registry: CommandRegistry) -> None:
    registry.register(Command(
        name="macro",
        aliases=[],
        args=["list", "run", "save", "show", "delete", "set"],
        handler=handle_macro,
        help_text=(
            "macro list | run <name> | save <name> [desc]"
            " | show <name> | delete <name> | set <name> abort on|off"
        ),
    ))
    registry.register(Command(
        name="sleep",
        aliases=[],
        args=[],
        handler=handle_sleep,
        help_text="sleep <seconds> — pause for N seconds (usable in macros)",
    ))
    registry.register(Command(
        name="history",
        aliases=["hist"],
        args=["search"],
        handler=handle_history,
        help_text="history [N] | history search <term>",
    ))
    registry.register(Command(
        name="stats",
        aliases=[],
        args=[],
        handler=handle_stats,
        help_text="Show usage statistics",
    ))
    registry.register(Command(
        name="devices",
        aliases=["devs"],
        args=[],
        handler=handle_devices,
        help_text="List known Roku devices",
    ))
