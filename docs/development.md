# Development & Architecture

This document provides a high-level overview of how **roku-tui** is structured, intended for anyone looking to contribute or understand the codebase.

## 🏗️ The Core Split: Headless vs. UI

The application is built on a "Service-First" architecture. All Roku interaction logic is encapsulated in the `RokuService` class, which is entirely independent of the Textual TUI.

### 1. `RokuService` (`roku_tui/service.py`)
- **Role**: Manages the `EcpClient`, the `Database`, and the `CommandRegistry`.
- **Headless Mode**: When you run `-c "command"`, the app instantiates a `RokuService`, runs the command, and exits.
- **UI Mode**: When you run the TUI, `RokuTuiApp` owns an instance of `RokuService` and proxies user input to it.

### 2. `RokuTuiApp` (`roku_tui/app.py`)
- **Role**: Orchestrates the Textual UI.
- **Components**: Uses `TabbedContent` to manage the Console and Remote panels, and a persistent `NetworkPanel` on the right.
- **Messaging**: Uses Textual's message-passing system to route command results from the service back to the UI widgets.

---

## ⌨️ Command Registry Pattern

The app does not use a massive `if/else` block for commands. Instead, it uses a `CommandRegistry` (`roku_tui/commands/registry.py`).

1.  **Definition**: Every command is a `Command` dataclass containing a name, aliases, a handler function, and help text.
2.  **Registration**: Commands are registered in `roku_tui/commands/handlers/__init__.py`, `db_commands.py`, and `tui_commands.py`.
3.  **Dispatch**: When a user types a command, the registry parses the string, looks up the handler, and executes it asynchronously.

---

## 📡 ECP Networking

The `EcpClient` (`roku_tui/ecp/client.py`) is an asynchronous HTTP client built on `httpx`.

- **Events**: Every request/response is emitted as a `NetworkEvent`.
- **Logging**: These events are routed to both the `Database` (for history) and the `NetworkPanel` (for real-time logging).
- **Mocking**: `MockEcpClient` allows the entire app to run without a real Roku, simulating XML/JSON responses for testing.

---

## 🛠️ Adding a New Command

1.  Open `roku_tui/commands/handlers/` and find the relevant category (e.g., `navigation.py` or `apps.py`), or create a new file if needed.
2.  Write an `async def handle_my_command(...)` function.
3.  Add it to the `register_all` function in `roku_tui/commands/handlers/__init__.py`.
4.  (Optional) Add detailed documentation to `roku_tui/commands/tips.py`.

---

## 🧪 Testing Strategy

We use `pytest` for all verification, targeting **100% line coverage** across the codebase.

- **Unit Tests**: Test handler logic, registry lookups, and service methods using `MockEcpClient` to capture ECP HTTP calls.
- **UI Tests**: Use Textual's `App.run_test()` / `pilot` API to simulate keypresses and assert widget state.
- **Integration Tests**: Verify the end-to-end flow from command input through ECP dispatch to database persistence.

Test files live in `tests/` and mirror the source layout (e.g., `test_apps_handlers_extra.py` covers `commands/handlers/apps.py`). Run the full suite with:

```bash
uv run pytest --cov=roku_tui --cov-report=term-missing
```
