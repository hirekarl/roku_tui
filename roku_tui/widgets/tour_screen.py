from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from ..mascot import RAT_MARKUP as _MASCOT


@dataclass
class TourStep:
    """A single step in the guided tour."""

    title: str
    body: str
    try_it: str | None = None
    hint: str | None = None


_STEPS = [
    TourStep(
        title="Welcome to roku-tui",
        body=f"{_MASCOT}\n\n"
        "Hi. I'm Ratsmith.\n\n"
        "I'll show you around — this won't take long,\n"
        "and by the end you'll wonder why you ever used the stock remote app.",
        hint="Use [bold]N[/bold] for Next and [bold]P[/bold] for Prev",
    ),
    TourStep(
        title="Console Panel",
        body="The main interface is the Console Panel. Type commands here "
        "to control your Roku.\n\n"
        "Use [bold]Tab[/bold] to autocomplete commands and app names.\n"
        "Use [bold]↑ / ↓[/bold] to cycle through your command history.",
        try_it="home; apps",
        hint="Multiple commands can be chained with semicolons.",
    ),
    TourStep(
        title="Navigation Commands",
        body="Basic navigation uses intuitive commands. Most have single-letter "
        "aliases for speed.\n\n"
        "• [bold]up, down, left, right[/bold] (or u, d, l, r)\n"
        "• [bold]select, back, home[/bold] (or s, b)\n"
        "• [bold]play, rev, fwd[/bold] (or p)",
        try_it="right 3; select",
        hint="Append a number to repeat: [bold]up 5[/bold] presses Up 5 times.",
    ),
    TourStep(
        title="Launch Apps",
        body="Launching apps is fast with fuzzy matching. You don't need to "
        "type the full name or app ID.",
        try_it="launch netflix",
        hint="Type [bold]apps[/bold] to see everything installed on your Roku.",
    ),
    TourStep(
        title="Remote Panel",
        body="Prefer a visual interface? Press [bold]Ctrl+T[/bold] to switch "
        "to the Remote Panel.\n\n"
        "It provides a classic button layout. Your keyboard arrow keys "
        "also work as a D-pad while this tab is active.",
        hint="Press [bold]Ctrl+T[/bold] again to return to the Console.",
    ),
    TourStep(
        title="Network Inspector",
        body="Want to see the raw ECP traffic? Press [bold]Ctrl+N[/bold] to "
        "toggle the Network Panel on the right.\n\n"
        "Every command you send is logged as an HTTP request. "
        "Select a row to inspect headers and XML/JSON responses.",
        hint="Press [bold]/[/bold] to filter the log by URL or method.",
    ),
    TourStep(
        title="Macros",
        body="Macros let you record sequences of commands to replay later. "
        "Perfect for setting up a specific app or state.",
        try_it="macro record",
        hint="Stop recording with [bold]macro stop <name>[/bold].",
    ),
    TourStep(
        title="Deep Links & YouTube",
        body="Jump directly to content with deep links. roku-tui includes "
        "built-in YouTube search support.\n\n"
        "Use [bold]yt search[/bold] then [bold]yt launch 1[/bold] "
        "to play the first result.",
        try_it="yt search lo-fi",
        hint="Save your favorites with [bold]link save <alias>[/bold].",
    ),
    TourStep(
        title="Keyboard Passthrough",
        body="Tired of hunting for letters on the TV screen? "
        "Type [bold]kb[/bold] to enter live keyboard mode.\n\n"
        "Every key you press on your physical keyboard is sent "
        "instantly as text to the Roku.",
        try_it="kb",
        hint="Press [bold]ESC[/bold] to exit keyboard mode.",
    ),
    TourStep(
        title="Stats & Themes",
        body="Personalize your experience with themes and track your usage.",
        try_it="theme nord",
        hint="Type [bold]stats[/bold] to see your most used commands.",
    ),
    TourStep(
        title="That's all.",
        body=f"{_MASCOT}\n\nYou've got everything you need.\n"
        "Now go control something.\n\n[dim]— Ratsmith[/dim]",
    ),
]


class TourScreen(ModalScreen[None]):
    """An interactive walkthrough of the application features."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "dismiss", show=False),
        Binding("q", "dismiss", show=False),
        Binding("s", "dismiss", show=False),
        Binding("f2", "dismiss", show=False),
        Binding("right,n", "next_step", "Next", show=False),
        Binding("left,p", "prev_step", "Prev", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.step_index = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="tour-body"):
            with Horizontal(id="tour-header"):
                yield Static("Guided Tour", id="tour-title")
                yield Label("", id="tour-progress")

            yield Static("", id="tour-step-title")
            yield Static("", id="tour-step-body")

            with Vertical(id="tour-extra"):
                yield Static("", id="tour-try-it")
                yield Static("", id="tour-hint")

            with Horizontal(id="tour-nav"):
                yield Button("◀ Prev [P]", id="tour-prev")
                yield Static("", id="tour-dots")
                yield Button("Next [N] ▶", id="tour-next")

            yield Button("Skip tour", id="tour-skip")

    def on_mount(self) -> None:
        self._update_step()

    def action_next_step(self) -> None:
        if self.step_index < len(_STEPS) - 1:
            self.step_index += 1
            self._update_step()
        else:
            self.dismiss()

    def action_prev_step(self) -> None:
        if self.step_index > 0:
            self.step_index -= 1
            self._update_step()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "tour-next":
            self.action_next_step()
        elif event.button.id == "tour-prev":
            self.action_prev_step()
        else:
            self.dismiss()

    def _update_step(self) -> None:
        step = _STEPS[self.step_index]
        self.query_one("#tour-progress", Label).update(
            f"Step {self.step_index + 1} of {len(_STEPS)}"
        )
        self.query_one("#tour-step-title", Static).update(f"[bold]{step.title}[/bold]")
        self.query_one("#tour-step-body", Static).update(step.body)

        try_it = self.query_one("#tour-try-it", Static)
        if step.try_it:
            try_it.update(
                f"▶ [bold]Try it:[/bold] [italic #73daca]{step.try_it}[/italic #73daca]"
            )
            try_it.remove_class("hidden")
        else:
            try_it.add_class("hidden")

        hint = self.query_one("#tour-hint", Static)
        if step.hint:
            hint.update(f"💡 {step.hint}")
            hint.remove_class("hidden")
        else:
            hint.add_class("hidden")

        # Update dots
        dots = "".join("●" if i == self.step_index else "○" for i in range(len(_STEPS)))
        self.query_one("#tour-dots", Static).update(dots)

        # Disable prev if at start
        self.query_one("#tour-prev", Button).disabled = self.step_index == 0
        next_btn = self.query_one("#tour-next", Button)
        if self.step_index == len(_STEPS) - 1:
            next_btn.label = "Finish [N]"
        else:
            next_btn.label = "Next [N] ▶"
