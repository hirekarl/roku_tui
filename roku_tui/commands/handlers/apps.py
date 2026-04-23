from __future__ import annotations

import contextlib
import difflib
from typing import TYPE_CHECKING, Any

from rich.table import Table

from ...service_yt import YouTubeClient
from .base import APP_IDS

if TYPE_CHECKING:
    from ...ecp.models import AppInfo


async def handle_launch(client: Any, args: list[str], context: Any) -> str:
    """Handle app launching by name or deep link alias."""
    if not args:
        return "[red]Usage:[/red] launch <app name | alias>"

    query = " ".join(args).lower()

    # 1. Try deep link alias first
    link = context.db.get_deep_link(query)
    if link:
        if client:
            p = {"contentId": link["content_id"]}
            await client.launch(link["app_id"], params=p)
        with contextlib.suppress(Exception):
            context.db.record_deep_link_launch(query)
        name = link["app_name"] or "App"
        return (
            f"[dim]↵[/dim] Deep link launched: [bold #7aa2f7]{name}[/bold #7aa2f7] "
            f"([dim]{link['alias']}[/dim])"
        )

    # 2. Try regular app launch
    app_cache: list[AppInfo] = context.app_cache

    if not app_cache and client:
        app_cache = await client.query_apps()
        context.app_cache = app_cache
        if hasattr(context, "suggester") and context.suggester:
            context.suggester.update_app_names([a.name for a in app_cache])

    names = [a.name for a in app_cache]
    matches = difflib.get_close_matches(
        query, [n.lower() for n in names], n=1, cutoff=0.4
    )
    if not matches:
        for app in app_cache:
            if query in app.name.lower():
                matches = [app.name.lower()]
                break

    if not matches:
        return (
            f"[yellow]No app matching[/yellow] '{query}'. "
            "Try [bold]apps[/bold] to see installed apps."
        )

    matched_name = matches[0]
    app = next(a for a in app_cache if a.name.lower() == matched_name)
    if client:
        await client.launch(app.id)
    with contextlib.suppress(Exception):
        context.db.log_app_launch(app, context._current_device_id())
    return f"[dim]↵[/dim] Launched [bold #7aa2f7]{app.name}[/bold #7aa2f7]"


async def handle_apps(client: Any, args: list[str], context: Any) -> Table | str:
    """List all installed apps on the Roku device."""
    if not client:
        return "[yellow]Not connected.[/yellow]"
    apps = await client.query_apps()
    context.app_cache = apps
    if hasattr(context, "suggester") and context.suggester:
        context.suggester.update_app_names([a.name for a in apps])
    table = Table(
        "ID",
        "Name",
        "Version",
        box=None,
        show_header=True,
        header_style="bold #7aa2f7",
        padding=(0, 2, 0, 0),
    )
    for app in apps:
        table.add_row(app.id, app.name, app.version)
    return table


async def handle_active(client: Any, args: list[str], context: Any) -> str:
    """Identify the currently active/foreground app."""
    if not client:
        return "[yellow]Not connected.[/yellow]"
    app = await client.query_active_app()
    if not app:
        return "[dim]No active app.[/dim]"
    return f"[bold #7aa2f7]{app.name}[/bold #7aa2f7] [dim](id: {app.id})[/dim]"


async def handle_link(client: Any, args: list[str], context: Any) -> Table | str:
    """Manage persistent deep link content shortcuts."""
    sub = args[0].lower() if args else "list"

    if sub == "save":
        if len(args) < 4:
            return "[red]Usage:[/red] link save <alias> <app_name | id> <content_id>"
        alias, app_input, content_id = args[1].lower(), args[2].lower(), args[3]

        # Resolve app ID
        app_id = APP_IDS.get(app_input, app_input)

        context.db.save_deep_link(alias, app_id, app_input.capitalize(), content_id)
        return f"[green]✓[/green] Saved deep link alias: [bold]{alias}[/bold]"

    elif sub == "list":
        links = context.db.list_deep_links()
        if not links:
            return (
                "[dim]No deep links saved. Use [bold]link save[/bold] to add one.[/dim]"
            )

        table = Table(
            "Alias",
            "App",
            "Content ID",
            "L-Count",
            box=None,
            show_header=True,
            header_style="bold #bb9af7",
            padding=(0, 2, 0, 0),
        )
        for link in links:
            table.add_row(
                link["alias"],
                link["app_name"] or "Unknown",
                link["content_id"],
                str(link["launch_count"]),
            )
        return table

    elif sub == "delete":
        if len(args) < 2:
            return "[red]Usage:[/red] link delete <alias>"
        context.db.delete_deep_link(args[1].lower())
        return f"[green]✓[/green] Deleted alias: [bold]{args[1].lower()}[/bold]"

    else:
        return "[red]Unknown link command.[/red] Try: list, save, delete"


async def handle_youtube(client: Any, args: list[str], context: Any) -> Table | str:
    """Search for and launch YouTube content."""
    if not args:
        usage = (
            "[red]Usage:[/red] yt search <query> | "
            "yt launch <id> | yt save <alias> <id>"
        )
        return usage

    sub = args[0].lower()
    yt_client = YouTubeClient()
    yt_app_id = APP_IDS["youtube"]

    if sub == "search":
        query = " ".join(args[1:])
        if not query:
            return "[red]Usage:[/red] yt search <query>"

        results = await yt_client.search(query)
        if not results:
            return "[yellow]No results found.[/yellow]"

        context._yt_results = results  # Cache for numerical launch

        table = Table(
            "#",
            "Title",
            "Channel",
            "ID",
            box=None,
            show_header=True,
            header_style="bold #f70000",
            padding=(0, 2, 0, 0),
        )
        for i, res in enumerate(results, 1):
            table.add_row(str(i), res["title"], res["channel"], res["id"])

        table.add_section()
        table.add_row(
            "",
            "[dim]Type [bold]yt launch 1[/bold] to play first result[/dim]",
            "",
            "",
        )
        return table

    elif sub == "launch":
        if len(args) < 2:
            return "[red]Usage:[/red] yt launch <id | index>"

        val = args[1]
        video_id = val

        # Check if it's a numeric index from last search
        if val.isdigit() and hasattr(context, "_yt_results"):
            idx = int(val) - 1
            if 0 <= idx < len(context._yt_results):
                video_id = context._yt_results[idx]["id"]

        if client:
            await client.launch(yt_app_id, params={"contentId": video_id})
        return f"[dim]↵[/dim] YouTube launched: [bold]{video_id}[/bold]"

    elif sub == "save":
        if len(args) < 3:
            return "[red]Usage:[/red] yt save <alias> <id>"
        alias, video_id = args[1].lower(), args[2]
        context.db.save_deep_link(alias, yt_app_id, "YouTube", video_id)
        return f"[green]✓[/green] Saved YouTube alias: [bold]{alias}[/bold]"

    return f"[red]Unknown yt command:[/red] {sub}"
