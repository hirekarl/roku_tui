# Macros: Automation & Sequences

Macros allow you to record, save, and replay sequences of commands. They are the primary way to automate complex interactions in **roku-tui**.

## 🔴 Recording a Macro

The easiest way to create a macro is to record your live actions:

1.  Type `macro record` in the console.
2.  Perform your commands (e.g., `home`, `launch Netflix`, `u`, `u`, `s`).
3.  Type `macro stop <name> [description]` to save.

### What is Recorded?
The recorder captures all navigation and app-launching commands. It automatically ignores "meta" commands like `help`, `history`, `stats`, `clear`, and `tour`.

---

## 🏃 Running Macros

Once saved, a macro can be executed by its name:
```bash
macro run morning
```

### Abort on Failure
By default, macros will continue executing even if one step fails (e.g., an app takes too long to load). You can change this behavior for specific macros:
- `macro set morning abort on`: Stop immediately if a command fails.
- `macro set morning abort off`: Keep going no matter what (default).

---

## 🛠️ Advanced: The `sleep` Command

Some apps require a few seconds to load before they can accept input. You can insert pauses into your macros by manually adding the `sleep` command:

**Example: A "Binge" Macro**
```bash
home
launch Netflix
sleep 5
select
```
*Note: The maximum `sleep` duration is 30 seconds.*

---

## 💾 Direct Database Editing

Macros are stored in a local SQLite database. If you want to view or edit the raw command sequences, you can find the database at:
- **macOS/Linux:** `~/.local/share/roku-tui/roku_tui.db`
- **Windows:** `%LOCALAPPDATA%\roku-tui\roku_tui.db`

You can use `macro show <name>` in the app to preview the steps without running them.
