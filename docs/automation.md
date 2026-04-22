# Automation & Cron Job Ideas

**roku-tui**'s headless mode (`-c` or `--command`) allows you to control your TV using standard system tools like `cron`, `systemd` timers, or even custom shell scripts. 

## Command Syntax
The basic structure for a headless command is:
```bash
/path/to/uv run roku-tui --ip <YOUR_ROKU_IP> -c "<commands_separated_by_semicolons>"
```

---

## 📅 Scheduled Cron Scenarios

### 1. The "Morning News" Routine
**Goal:** Automatically turn the TV on and launch your preferred news app so it's ready when you walk into the room.
- **Schedule:** 7:00 AM, Monday-Friday.
- **Command:** `home; launch YouTube; sleep 5; select`
```cron
0 7 * * 1-5 /usr/local/bin/uv run roku-tui --ip 192.168.1.50 -c "home; launch YouTube"
```

### 2. The "Home Occupied" Simulator
**Goal:** Deter intruders while on vacation by making it look like someone is home.
- **Evening Start (6:00 PM):** `home; launch Netflix`
- **Late Night End (11:30 PM):** `power`
```cron
0 18 * * * /usr/local/bin/uv run roku-tui --ip 192.168.1.50 -c "home; launch Netflix"
30 23 * * * /usr/local/bin/uv run roku-tui --ip 192.168.1.50 -c "power"
```

### 3. "Quiet Hours" Enforcement
**Goal:** Automatically mute the TV or lower the volume at night to avoid waking others.
- **Schedule:** 11:00 PM every night.
- **Command:** `volume mute` (or `volume down 10`)
```cron
0 23 * * * /usr/local/bin/uv run roku-tui --ip 192.168.1.50 -c "mute"
```

### 4. Kids' Bedtime "Hard Stop"
**Goal:** Gently (or firmly) remind the family that it's time to turn off the screens.
- **Schedule:** 8:30 PM.
- **Command:** `home; sleep 1; home` (Returning home stops most playback)
```cron
30 20 * * * /usr/local/bin/uv run roku-tui --ip 192.168.1.50 -c "home; home"
```

### 5. Monday Night Football / Weekly Event
**Goal:** Never miss the start of a weekly broadcast.
- **Schedule:** 8:15 PM every Monday.
- **Command:** `launch "ESPN"`
```cron
15 20 * * 1 /usr/local/bin/uv run roku-tui --ip 192.168.1.50 -c "launch ESPN"
```

### 6. Volume Normalization
**Goal:** Ensure the TV isn't "blasting" when the first person turns it on in the morning.
- **Schedule:** 4:00 AM.
- **Command:** `volume down 20` (Effective way to ensure a low baseline)
```cron
0 4 * * * /usr/local/bin/uv run roku-tui --ip 192.168.1.50 -c "volume down 20"
```

---

## ⌨️ Shell Integration & Aliases

### Desktop Mute Button
Add this to your `.zshrc` or `.bashrc` to mute your TV from your terminal while working:
```bash
alias tv-mute='uv run roku-tui --ip 192.168.1.50 -c "mute"'
```

### "Movie Mode" Script
Create a script `movie_night.sh` that dims your smart lights and sets up your Roku:
```bash
#!/bin/bash
# 1. Dim the lights (example using homeassistant CLI)
ha light turn_off entity_id=light.living_room_overhead

# 2. Setup the Roku
uv run roku-tui --ip 192.168.1.50 -c "macro run movie-night"
```

---

## 🛠️ Pro-Tips for Automation Success

1.  **Use Absolute Paths:** Cron environments are minimal. Use `/usr/local/bin/uv` instead of just `uv`. (Find your path with `which uv`).
2.  **Stick to IPs:** Use `--ip` to bypass discovery. It makes your scripts faster and more reliable.
3.  **Timing Matters:** If you launch an app and then want to "press" something inside it, use the `sleep` command: `-c "launch Netflix; sleep 10; select"`.
4.  **Logging:** Redirect output to a log file to see if your cron jobs are succeeding: `>> /tmp/roku_cron.log 2>&1`.
5.  **Chain Wisely:** Use semicolons to build complex sequences like `home; volume down 5; launch "Prime Video"`.
